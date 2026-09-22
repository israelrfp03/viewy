"""Construye el perfil de gustos del usuario (Django ORM, reutilizando la
Fase 8 donde ya aplica) y orquesta la llamada al LLM + verificación TMDB.

El LLM nunca calcula nada que ya podamos calcular: recibe agregados y
ejemplos ya resueltos por ORM. Solo decide qué títulos encajan.
"""

from django.db.models import Avg

from analytics.services import get_dashboard_stats
from integrations import tmdb
from library.models import MediaItem, UserMedia

from .llm import LLMError, get_recommendations_from_llm
from .prompts import SYSTEM_PROMPT, build_user_prompt

MAX_EXAMPLE_TITLES = 8
MAX_DROPPED_TITLES = 5
MAX_LIBRARY_TITLES_FOR_DEDUP = 100

MEDIA_TYPE_LABELS = {"movie": "película", "series": "serie", "anime": "anime"}


def build_taste_profile(user):
    """Devuelve (profile_text, is_thin_profile, library_titles_for_dedup).

    profile_text es None si el usuario no tiene absolutamente nada en su
    biblioteca — en ese caso no debe llegar a llamarse al LLM."""
    entries = UserMedia.objects.filter(user=user).select_related("media")
    total = entries.count()
    if total == 0:
        return None, False, []

    stats = get_dashboard_stats(user)

    top_rated = (
        entries.filter(rating__isnull=False).order_by("-rating").select_related("media")[:MAX_EXAMPLE_TITLES]
    )
    favorites = entries.filter(favorite=True).select_related("media")[:MAX_EXAMPLE_TITLES]
    dropped = (
        entries.filter(status=UserMedia.Status.DROPPED)
        .order_by("-updated_at")
        .select_related("media")[:MAX_DROPPED_TITLES]
    )
    library_titles = list(
        entries.order_by("-created_at").values_list("media__title", flat=True)[:MAX_LIBRARY_TITLES_FOR_DEDUP]
    )

    lines = [f"Biblioteca: {total} títulos ({_type_summary(stats['media_type_breakdown'])})."]

    if stats["rating_stats"]["rated_count"]:
        lines.append(
            f"Rating medio: {stats['rating_stats']['average']}/10 ({stats['rating_stats']['rated_count']} puntuados)."
        )

    if top_rated:
        examples = ", ".join(f'"{e.media.title}" ({_label(e.media.media_type)}, {e.rating}/10)' for e in top_rated)
        lines.append(f"Mejor puntuados: {examples}.")

    if favorites:
        lines.append("Favoritos: " + ", ".join(f'"{e.media.title}"' for e in favorites) + ".")

    if dropped:
        lines.append(
            "Abandonados recientemente (evitar algo muy parecido a esto): "
            + ", ".join(f'"{e.media.title}"' for e in dropped)
            + "."
        )

    avg_movie_duration = _average_movie_duration(entries)
    if avg_movie_duration:
        lines.append(f"Duración media de las películas que ha visto: {avg_movie_duration} min.")

    profile_text = "Perfil de gustos del usuario:\n- " + "\n- ".join(lines)
    is_thin_profile = not (stats["rating_stats"]["rated_count"] or favorites)

    return profile_text, is_thin_profile, library_titles


def _label(media_type):
    return MEDIA_TYPE_LABELS.get(media_type, media_type)


def _type_summary(breakdown):
    parts = [
        f"{data['count']} {_label(value)}{'s' if data['count'] != 1 else ''}"
        for value, data in breakdown.items()
        if data["count"]
    ]
    return ", ".join(parts) if parts else "sin contenido"


def _average_movie_duration(entries):
    movies = entries.filter(
        media__media_type=MediaItem.MediaType.MOVIE,
        status=UserMedia.Status.COMPLETED,
        media__duration_minutes__isnull=False,
    )
    result = movies.aggregate(avg=Avg("media__duration_minutes"))
    return round(result["avg"]) if result["avg"] else None


def get_recommendations(user, request_text):
    """Devuelve (recommendations, error_code, is_thin_profile).

    error_code es None si todo fue bien, o uno de:
    "not_enough_data" | "llm_unavailable" | "no_verifiable_results"."""
    profile_text, is_thin_profile, library_titles = build_taste_profile(user)
    if profile_text is None:
        return [], "not_enough_data", False

    context = profile_text
    if library_titles:
        context += "\n\nYa en su biblioteca (no recomendar de nuevo): " + ", ".join(
            f'"{t}"' for t in library_titles
        )

    user_prompt = build_user_prompt(context, request_text)

    try:
        raw_recommendations = get_recommendations_from_llm(SYSTEM_PROMPT, user_prompt)
    except LLMError:
        return [], "llm_unavailable", is_thin_profile

    if not raw_recommendations:
        return [], "llm_unavailable", is_thin_profile

    existing_external_ids = set(
        MediaItem.objects.filter(user_entries__user=user).exclude(external_id="").values_list(
            "external_id", flat=True
        )
    )

    verified = [
        candidate
        for item in raw_recommendations
        if (candidate := _verify_with_tmdb(item, existing_external_ids)) is not None
    ]

    if not verified:
        return [], "no_verifiable_results", is_thin_profile

    return verified, None, is_thin_profile


def _verify_with_tmdb(item, existing_external_ids):
    """Busca el título propuesto por el LLM en TMDB (única fuente de verdad de
    contenido en Viewy). Si no hay match, o si ya está en la biblioteca del
    usuario (capa dura de deduplicación), se descarta la sugerencia."""
    try:
        results = tmdb.search(item["title"])
    except tmdb.TMDBError:
        return None

    if not results:
        return None

    match = results[0]
    if match.external_id in existing_external_ids:
        return None

    media_type = item["media_type"]
    if match.is_anime_candidate:
        media_type = "anime"
    elif media_type == "anime":
        media_type = match.media_type

    return {
        "title": match.title,
        "poster_url": match.poster_url,
        "release_year": match.release_year,
        "external_id": match.external_id,
        "source_type": match.source_type,
        "media_type": media_type,
        "reason": item["reason"],
    }
