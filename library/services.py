"""Lógica de negocio de biblioteca reutilizada por varias apps (library,
imports) — evita que cada flujo de alta reimplemente la deduplicación."""

from .models import MediaItem


def get_or_create_media_from_tmdb(detail, media_type):
    """Crea o reutiliza un MediaItem a partir de un detalle de TMDB.

    `media_type` es la clasificación elegida por el usuario (puede ser "anime",
    más específica que el `detail.media_type` base de TMDB). "anime" nunca
    degrada un MediaItem ya clasificado como tal, pero sí puede "mejorar" uno
    que todavía era genérico ("movie"/"series").
    """
    media = MediaItem.objects.filter(
        external_source=MediaItem.ExternalSource.TMDB, external_id=detail.external_id
    ).first()
    if media:
        if media_type == MediaItem.MediaType.ANIME and media.media_type != MediaItem.MediaType.ANIME:
            media.media_type = MediaItem.MediaType.ANIME
            media.save(update_fields=["media_type"])
        return media

    # Reutiliza un MediaItem manual equivalente en vez de duplicar el título.
    media = MediaItem.objects.filter(
        title__iexact=detail.title,
        media_type__in={detail.media_type, media_type},
        external_id="",
    ).first()
    if media:
        media.external_id = detail.external_id
        media.external_source = MediaItem.ExternalSource.TMDB
        media.poster_url = detail.poster_url or media.poster_url
        media.description = detail.description or media.description
        media.release_year = detail.release_year or media.release_year
        media.duration_minutes = detail.duration_minutes or media.duration_minutes
        media.episodes = detail.episodes or media.episodes
        if media_type == MediaItem.MediaType.ANIME:
            media.media_type = MediaItem.MediaType.ANIME
        media.save()
        return media

    return MediaItem.objects.create(
        title=detail.title,
        media_type=media_type,
        release_year=detail.release_year,
        description=detail.description,
        poster_url=detail.poster_url,
        external_id=detail.external_id,
        external_source=MediaItem.ExternalSource.TMDB,
        duration_minutes=detail.duration_minutes,
        episodes=detail.episodes,
    )
