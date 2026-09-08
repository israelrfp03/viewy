import requests
from django.core.cache import cache

from .anime_types import (
    AnimeCandidate,
    AnimeCharacter,
    AnimeEnrichment,
    AnimeEpisode,
    AnimeRelation,
    AnimeStaffMember,
)

PROVIDER_NAME = "jikan"
API_BASE_URL = "https://api.jikan.moe/v4"
REQUEST_TIMEOUT = 8  # Jikan tiende a ser más lento que AniList/TMDB.
ENRICHMENT_CACHE_TTL = 60 * 60 * 24  # 24 horas


class JikanError(Exception):
    """Fallo genérico al comunicarse con Jikan (proxy no oficial de MyAnimeList)."""


class JikanTimeoutError(JikanError):
    pass


class JikanNotFoundError(JikanError):
    pass


def _get(path, params=None):
    try:
        response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        raise JikanTimeoutError("Jikan no respondió a tiempo.") from exc
    except requests.exceptions.RequestException as exc:
        raise JikanError("No se pudo contactar con Jikan.") from exc

    if response.status_code == 404:
        raise JikanNotFoundError("No se encontró ese anime en Jikan.")
    if response.status_code != 200:
        raise JikanError(f"Jikan respondió con un error inesperado ({response.status_code}).")

    try:
        return response.json()
    except ValueError as exc:
        raise JikanError("Jikan devolvió una respuesta inesperada.") from exc


def search_candidates(query):
    payload = _get("/anime", params={"q": query, "limit": 6})
    candidates = []

    try:
        for item in payload.get("data", []):
            images = (item.get("images") or {}).get("jpg") or {}
            candidates.append(
                AnimeCandidate(
                    source=PROVIDER_NAME,
                    external_id=str(item["mal_id"]),
                    title_romaji=item.get("title") or "",
                    title_english=item.get("title_english") or "",
                    release_year=item.get("year"),
                    poster_url=images.get("image_url") or "",
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise JikanError("Jikan devolvió una respuesta con un formato inesperado.") from exc

    return candidates


def get_enrichment(external_id):
    cache_key = f"jikan:enrichment:{external_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    detail = _get(f"/anime/{external_id}")
    characters_payload = _get(f"/anime/{external_id}/characters")
    staff_payload = _get(f"/anime/{external_id}/staff")
    relations_payload = _get(f"/anime/{external_id}/relations")
    episodes_payload = _get(f"/anime/{external_id}/episodes")

    try:
        data = detail["data"]
        studios = [s["name"] for s in data.get("studios", [])]

        characters = []
        for entry in characters_payload.get("data", [])[:8]:
            character = entry.get("character") or {}
            images = (character.get("images") or {}).get("jpg") or {}
            voice_actors = entry.get("voice_actors") or []
            japanese_va = next(
                (va for va in voice_actors if va.get("language") == "Japanese"), None
            )
            voice_actor = ((japanese_va or {}).get("person") or {}).get("name", "")
            characters.append(
                AnimeCharacter(
                    name=character.get("name") or "",
                    image_url=images.get("image_url") or "",
                    role=entry.get("role") or "",
                    voice_actor=voice_actor,
                    description="",  # Jikan no ofrece biografía de personaje en este endpoint.
                )
            )

        staff = []
        for entry in staff_payload.get("data", [])[:5]:
            person = entry.get("person") or {}
            positions = entry.get("positions") or []
            staff.append(
                AnimeStaffMember(name=person.get("name") or "", role=", ".join(positions))
            )

        relations = []
        for entry in relations_payload.get("data", []):
            relation_type = entry.get("relation") or ""
            for related in entry.get("entry", []):
                if related.get("type") != "anime":
                    continue
                relations.append(
                    AnimeRelation(title=related.get("name") or "", relation_type=relation_type)
                )

        episodes = []
        for index, ep in enumerate(episodes_payload.get("data", []), start=1):
            episodes.append(
                AnimeEpisode(
                    number=index,
                    title=ep.get("title") or f"Episodio {index}",
                    thumbnail_url="",
                )
            )

        enrichment = AnimeEnrichment(
            external_id=str(data["mal_id"]),
            title_romaji=data.get("title") or "",
            title_english=data.get("title_english") or "",
            source_material=data.get("source") or "",
            studio=studios[0] if studios else "",
            status=data.get("status") or "",
            characters=characters,
            staff=staff,
            relations=relations,
            episodes=episodes,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise JikanError("Jikan devolvió una respuesta con un formato inesperado.") from exc

    cache.set(cache_key, enrichment, ENRICHMENT_CACHE_TTL)
    return enrichment
