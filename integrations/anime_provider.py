"""Orquesta los proveedores de enriquecimiento de anime con reintento automático.

Se prueba AniList primero (mejor modelo de datos, una sola query). Si no está
disponible, se prueba Jikan como respaldo. Mientras uno de los dos funcione,
el enriquecimiento de anime sigue funcionando — ninguno de los dos es una
dependencia crítica por sí solo.
"""

from . import anilist, jikan

PROVIDERS = {
    "anilist": anilist,
    "jikan": jikan,
}


class AnimeProviderUnavailable(Exception):
    """Ningún proveedor de enriquecimiento de anime está disponible ahora mismo."""


def search_anime(query):
    """Devuelve (candidatos, proveedor_usado). Prueba anilist, luego jikan."""
    try:
        return anilist.search_candidates(query), "anilist"
    except anilist.AniListError:
        pass

    try:
        return jikan.search_candidates(query), "jikan"
    except jikan.JikanError as exc:
        raise AnimeProviderUnavailable(
            "Ni AniList ni Jikan están disponibles ahora mismo."
        ) from exc


def get_anime_enrichment(source, external_id):
    """Obtiene el enriquecimiento de un anime ya confirmado, del proveedor que le corresponde."""
    provider = PROVIDERS.get(source)
    if provider is None:
        raise AnimeProviderUnavailable(f"Proveedor desconocido: {source!r}.")

    try:
        return provider.get_enrichment(external_id)
    except (anilist.AniListError, jikan.JikanError) as exc:
        raise AnimeProviderUnavailable(
            f"No se pudo obtener información de {source} ahora mismo."
        ) from exc
