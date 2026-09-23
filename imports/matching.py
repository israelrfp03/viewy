"""Búsqueda de candidatos y clasificación de confianza del matching contra
TMDB — única fuente de verdad de contenido en Viewy (igual que en el resto
de la app: nunca AniList/Jikan para identidad, solo para enriquecimiento
posterior y opcional). Reglas fijas, sin machine learning: el sistema nunca
elige en solitario cuando hay ambigüedad real.
"""

from integrations import tmdb

MAX_CANDIDATES = 5


def find_candidates(title):
    """Devuelve (candidatos, error). error es "provider_error" si TMDB falló;
    None si la búsqueda se completó (con o sin resultados)."""
    try:
        results = tmdb.search(title)
    except tmdb.TMDBError:
        return [], "provider_error"
    return results[:MAX_CANDIDATES], None


def classify_match(title, candidates):
    """Devuelve (match_state, candidato_preseleccionado).

    - "matched": un único candidato con título exactamente igual (normalizado).
    - "ambiguous": cero o más de un candidato con título exacto — el usuario
      decide, nunca se preselecciona nada.
    - "not_found": TMDB no devolvió ningún resultado.
    """
    if not candidates:
        return "not_found", None

    normalized = _normalize(title)
    exact_matches = [c for c in candidates if _normalize(c.title) == normalized]
    if len(exact_matches) == 1:
        return "matched", exact_matches[0]
    return "ambiguous", None


def _normalize(text):
    return " ".join(text.strip().lower().split())


def resolved_media_type(candidate):
    """La heurística de anime ya existente (Fase 7) decide el tipo final,
    nunca el LLM ni un candidato "a ciegas"."""
    if candidate.is_anime_candidate:
        return "anime"
    return candidate.media_type
