"""Orquesta la importación: parsear texto, resolver ambigüedades (LLM en
lote, solo si hace falta), buscar candidatos en TMDB, construir la vista
previa, y confirmar el lote guardando cada fila en su propia transacción.
"""

from django.db import transaction

from integrations import tmdb
from library.models import MediaItem, UserMedia
from library.services import get_or_create_media_from_tmdb

from .llm import LLMError, parse_ambiguous_lines
from .matching import classify_match, find_candidates, resolved_media_type
from .parsing import parse_text

MAX_ITEMS = 100


def analyze_text(user, text):
    """Devuelve (rows, truncated). rows es una lista de dicts JSON-serializables
    (aptos para guardar en sesión), uno por línea no vacía del texto pegado."""
    parsed_lines = parse_text(text)
    truncated = len(parsed_lines) > MAX_ITEMS
    parsed_lines = parsed_lines[:MAX_ITEMS]

    low_confidence_indices = [i for i, p in enumerate(parsed_lines) if p.confidence == "low"]
    llm_results = {}
    if low_confidence_indices:
        raw_lines = [parsed_lines[i].raw_text for i in low_confidence_indices]
        try:
            resolved = parse_ambiguous_lines(raw_lines)
            llm_results = {low_confidence_indices[position]: value for position, value in resolved.items()}
        except LLMError:
            pass  # si el LLM falla, se usan las líneas tal cual (título completo, sin rating)

    existing_external_ids = set(
        MediaItem.objects.filter(user_entries__user=user)
        .exclude(external_id="")
        .values_list("external_id", flat=True)
    )

    rows = []
    for i, parsed in enumerate(parsed_lines):
        if i in llm_results:
            title, rating = llm_results[i]["title"], llm_results[i]["rating"]
        else:
            title, rating = parsed.title, parsed.rating
        rows.append(_build_row(parsed.raw_text, title, rating, existing_external_ids))

    return rows, truncated


def _build_row(raw_text, title, rating, existing_external_ids):
    title = (title or "").strip()[:255]

    row = {
        "raw_text": raw_text,
        "title": title,
        "rating": rating,
        "media_type": None,
        "status": "completed" if rating is not None else "planned",
        "match_state": "invalid",
        "selected_external_id": None,
        "selected_source_type": None,
        "candidates": [],
        "already_in_library": False,
        "duplicate_action": "ignore",
        "excluded": False,
        "invalid_reason": None,
    }

    if not title:
        row["invalid_reason"] = "Título vacío."
        return row

    if rating is not None and not (1 <= rating <= 10):
        row["invalid_reason"] = "Rating fuera de rango (1-10) — se ignorará al guardar."
        row["rating"] = None
        row["status"] = "planned"

    candidates, error = find_candidates(title)
    if error:
        row["match_state"] = "not_found"
        row["invalid_reason"] = row["invalid_reason"] or "TMDB no está disponible ahora mismo."
        return row

    match_state, selected = classify_match(title, candidates)
    row["match_state"] = match_state
    row["candidates"] = [_serialize_candidate(c) for c in candidates]

    if selected:
        row["selected_external_id"] = selected.external_id
        row["selected_source_type"] = selected.source_type
        row["media_type"] = resolved_media_type(selected)
        row["already_in_library"] = selected.external_id in existing_external_ids

    return row


def _serialize_candidate(c):
    return {
        "external_id": c.external_id,
        "source_type": c.source_type,
        "media_type": "anime" if c.is_anime_candidate else c.media_type,
        "title": c.title,
        "release_year": c.release_year,
        "poster_url": c.poster_url,
    }


def confirm_import(user, rows):
    """Cada fila se procesa en su propia transacción: un fallo puntual no
    bloquea el resto del lote (ver Fase 13 — "guardar válidos, reportar
    fallidos" en vez de todo-o-nada)."""
    summary = {"added": 0, "updated": 0, "ignored": 0, "not_found": 0, "errors": 0}

    for row in rows:
        if row.get("excluded"):
            summary["ignored"] += 1
            continue
        try:
            with transaction.atomic():
                _confirm_row(user, row, summary)
        except Exception:
            summary["errors"] += 1

    return summary


def _confirm_row(user, row, summary):
    title = (row.get("title") or "").strip()[:255]
    media_type = row.get("media_type")
    external_id = row.get("selected_external_id")
    source_type = row.get("selected_source_type")

    if not external_id or media_type not in MediaItem.MediaType.values:
        summary["not_found"] += 1
        return

    rating = row.get("rating")
    if rating is not None:
        rating = max(1, min(10, round(rating)))

    status = row.get("status")
    if status not in UserMedia.Status.values:
        status = UserMedia.Status.PLANNED

    try:
        detail = tmdb.get_detail(external_id, source_type)
    except tmdb.TMDBError:
        summary["errors"] += 1
        return

    media = get_or_create_media_from_tmdb(detail, media_type)
    entry = UserMedia.objects.filter(user=user, media=media).first()

    if entry:
        if row.get("duplicate_action") == "update":
            if rating is not None:
                entry.rating = rating
            entry.status = status
            entry.save()
            summary["updated"] += 1
        else:
            summary["ignored"] += 1
        return

    if not title:
        summary["errors"] += 1
        return

    UserMedia.objects.create(user=user, media=media, rating=rating, status=status)
    summary["added"] += 1
