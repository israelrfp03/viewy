import re

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

PROVIDER_NAME = "anilist"
API_URL = "https://graphql.anilist.co"
REQUEST_TIMEOUT = 5
ENRICHMENT_CACHE_TTL = 60 * 60 * 24  # 24 horas

SPOILER_MARKUP = re.compile(r"~![\s\S]*?!~")


class AniListError(Exception):
    """Fallo genérico al comunicarse con AniList."""


class AniListTimeoutError(AniListError):
    pass


class AniListNotFoundError(AniListError):
    pass


SEARCH_QUERY = """
query ($search: String) {
  Page(perPage: 6) {
    media(search: $search, type: ANIME) {
      id
      title { romaji english }
      startDate { year }
      coverImage { medium }
    }
  }
}
"""

DETAIL_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title { romaji english }
    source
    status
    studios(isMain: true) { nodes { name } }
    characters(sort: ROLE, perPage: 8) {
      edges {
        role
        node { name { full } image { medium } description(asHtml: false) }
        voiceActors(language: JAPANESE, sort: RELEVANCE) { name { full } }
      }
    }
    staff(sort: RELEVANCE, perPage: 5) {
      edges { role node { name { full } } }
    }
    relations {
      edges { relationType(version: 2) node { title { romaji english } type } }
    }
    streamingEpisodes { title thumbnail }
  }
}
"""


def _post(query, variables):
    try:
        response = requests.post(
            API_URL, json={"query": query, "variables": variables}, timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout as exc:
        raise AniListTimeoutError("AniList no respondió a tiempo.") from exc
    except requests.exceptions.RequestException as exc:
        raise AniListError("No se pudo contactar con AniList.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise AniListError("AniList devolvió una respuesta inesperada.") from exc

    if response.status_code != 200 or payload.get("errors"):
        message = payload.get("errors", [{}])[0].get("message", "Error desconocido de AniList.")
        raise AniListError(message)

    return payload["data"]


def _clean_description(text):
    if not text:
        return ""
    text = SPOILER_MARKUP.sub("", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip()
    if len(text) > 220:
        text = text[:220].rsplit(" ", 1)[0] + "..."
    return text


def search_candidates(query):
    data = _post(SEARCH_QUERY, {"search": query})
    candidates = []

    try:
        results = data["Page"]["media"]
        for item in results:
            title = item.get("title") or {}
            cover = item.get("coverImage") or {}
            start_date = item.get("startDate") or {}

            candidates.append(
                AnimeCandidate(
                    source=PROVIDER_NAME,
                    external_id=str(item["id"]),
                    title_romaji=title.get("romaji") or "",
                    title_english=title.get("english") or "",
                    release_year=start_date.get("year"),
                    poster_url=cover.get("medium") or "",
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise AniListError("AniList devolvió una respuesta con un formato inesperado.") from exc

    return candidates


def get_enrichment(external_id):
    cache_key = f"anilist:enrichment:{external_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    data = _post(DETAIL_QUERY, {"id": int(external_id)})
    media = data.get("Media")
    if media is None:
        raise AniListNotFoundError("No se encontró ese anime en AniList.")

    try:
        title = media.get("title") or {}
        studios = [node["name"] for node in (media.get("studios") or {}).get("nodes", [])]

        characters = []
        for edge in (media.get("characters") or {}).get("edges", []):
            node = edge.get("node") or {}
            name = (node.get("name") or {}).get("full", "")
            image = (node.get("image") or {}).get("medium", "")
            voice_actors = edge.get("voiceActors") or []
            voice_actor = voice_actors[0]["name"]["full"] if voice_actors else ""
            characters.append(
                AnimeCharacter(
                    name=name,
                    image_url=image,
                    role=edge.get("role") or "",
                    voice_actor=voice_actor,
                    description=_clean_description(node.get("description")),
                )
            )

        staff = []
        for edge in (media.get("staff") or {}).get("edges", []):
            node = edge.get("node") or {}
            staff.append(
                AnimeStaffMember(
                    name=(node.get("name") or {}).get("full", ""),
                    role=edge.get("role") or "",
                )
            )

        relations = []
        for edge in (media.get("relations") or {}).get("edges", []):
            node = edge.get("node") or {}
            if node.get("type") != "ANIME":
                continue
            node_title = node.get("title") or {}
            relations.append(
                AnimeRelation(
                    title=node_title.get("english") or node_title.get("romaji") or "",
                    relation_type=edge.get("relationType") or "",
                )
            )

        episodes = []
        for index, ep in enumerate(media.get("streamingEpisodes") or [], start=1):
            episodes.append(
                AnimeEpisode(
                    number=index,
                    title=ep.get("title") or f"Episodio {index}",
                    thumbnail_url=ep.get("thumbnail") or "",
                )
            )

        enrichment = AnimeEnrichment(
            external_id=str(media["id"]),
            title_romaji=title.get("romaji") or "",
            title_english=title.get("english") or "",
            source_material=media.get("source") or "",
            studio=studios[0] if studios else "",
            status=media.get("status") or "",
            characters=characters,
            staff=staff,
            relations=relations,
            episodes=episodes,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AniListError("AniList devolvió una respuesta con un formato inesperado.") from exc

    cache.set(cache_key, enrichment, ENRICHMENT_CACHE_TTL)
    return enrichment
