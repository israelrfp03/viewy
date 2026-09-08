from dataclasses import dataclass

import requests
from django.conf import settings

SEARCH_URL = f"{settings.TMDB_API_BASE_URL}/search/multi"
DETAIL_URL = f"{settings.TMDB_API_BASE_URL}/{{media_type}}/{{external_id}}"
REQUEST_TIMEOUT = 5

TMDB_TO_INTERNAL_MEDIA_TYPE = {
    "movie": "movie",
    "tv": "series",
}


class TMDBError(Exception):
    """Fallo genérico al comunicarse con TMDB."""


class TMDBTimeoutError(TMDBError):
    pass


class TMDBAuthError(TMDBError):
    pass


@dataclass
class TMDBSearchResult:
    external_id: str
    media_type: str
    title: str
    release_year: int | None
    poster_url: str
    description: str


@dataclass
class TMDBDetail(TMDBSearchResult):
    duration_minutes: int | None
    episodes: int | None


def _headers():
    return {
        "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
        "Accept": "application/json",
    }


def _request(url, params=None):
    try:
        response = requests.get(url, headers=_headers(), params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        raise TMDBTimeoutError("TMDB no respondió a tiempo.") from exc
    except requests.exceptions.RequestException as exc:
        raise TMDBError("No se pudo contactar con TMDB.") from exc

    if response.status_code == 401:
        raise TMDBAuthError("Credenciales de TMDB inválidas.")
    if response.status_code != 200:
        raise TMDBError(f"TMDB respondió con un error inesperado ({response.status_code}).")

    try:
        return response.json()
    except ValueError as exc:
        raise TMDBError("TMDB devolvió una respuesta inesperada.") from exc


def _extract_year(date_str):
    if not date_str:
        return None
    try:
        return int(date_str[:4])
    except ValueError:
        return None


def _poster_url(poster_path):
    if not poster_path:
        return ""
    return f"{settings.TMDB_IMAGE_BASE_URL}{poster_path}"


def search(query):
    data = _request(SEARCH_URL, params={"query": query})
    results = []

    for item in data.get("results", []):
        media_type = TMDB_TO_INTERNAL_MEDIA_TYPE.get(item.get("media_type"))
        if media_type is None:
            continue

        title = item.get("title") or item.get("name") or ""
        release_date = item.get("release_date") or item.get("first_air_date")

        results.append(
            TMDBSearchResult(
                external_id=str(item["id"]),
                media_type=media_type,
                title=title,
                release_year=_extract_year(release_date),
                poster_url=_poster_url(item.get("poster_path")),
                description=item.get("overview") or "",
            )
        )

    return results


def get_detail(external_id, media_type):
    tmdb_media_type = "movie" if media_type == "movie" else "tv"
    url = DETAIL_URL.format(media_type=tmdb_media_type, external_id=external_id)
    data = _request(url)

    title = data.get("title") or data.get("name") or ""
    release_date = data.get("release_date") or data.get("first_air_date")

    return TMDBDetail(
        external_id=str(data["id"]),
        media_type=media_type,
        title=title,
        release_year=_extract_year(release_date),
        poster_url=_poster_url(data.get("poster_path")),
        description=data.get("overview") or "",
        duration_minutes=(data.get("runtime") or None) if media_type == "movie" else None,
        episodes=data.get("number_of_episodes") if media_type == "series" else None,
    )
