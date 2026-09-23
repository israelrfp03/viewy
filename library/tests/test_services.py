"""get_or_create_media_from_tmdb: deduplicación por external_source+external_id,
adopción de entradas manuales equivalentes, y la regla "solo mejora hacia
anime, nunca degrada"."""

import pytest

from integrations.tmdb import TMDBDetail
from library.models import MediaItem
from library.services import get_or_create_media_from_tmdb

pytestmark = pytest.mark.django_db


def _detail(external_id="1", title="One Piece", media_type="series", **kwargs):
    defaults = dict(
        source_type="tv",
        media_type=media_type,
        title=title,
        release_year=1999,
        poster_url="",
        description="",
        is_anime_candidate=False,
        duration_minutes=None,
        episodes=None,
    )
    defaults.update(kwargs)
    return TMDBDetail(external_id=external_id, **defaults)


class TestGetOrCreateMediaFromTMDB:
    def test_creates_new_media_item_when_none_exists(self):
        media = get_or_create_media_from_tmdb(_detail(), "series")
        assert media.external_source == MediaItem.ExternalSource.TMDB
        assert media.title == "One Piece"

    def test_reuses_existing_media_item_with_same_external_id(self):
        first = get_or_create_media_from_tmdb(_detail(external_id="42"), "series")
        second = get_or_create_media_from_tmdb(_detail(external_id="42"), "series")
        assert first.pk == second.pk
        assert MediaItem.objects.filter(external_id="42").count() == 1

    def test_adopts_equivalent_manual_entry_instead_of_duplicating(self, make_media):
        manual = make_media(title="Interstellar", media_type="movie", external_id="")
        media = get_or_create_media_from_tmdb(
            _detail(external_id="99", title="Interstellar", media_type="movie"), "movie"
        )
        assert media.pk == manual.pk
        assert media.external_id == "99"
        assert MediaItem.objects.filter(title="Interstellar").count() == 1

    def test_reclassifying_as_anime_upgrades_existing_series(self):
        media = get_or_create_media_from_tmdb(_detail(external_id="7"), "series")
        assert media.media_type == "series"

        upgraded = get_or_create_media_from_tmdb(_detail(external_id="7"), "anime")
        assert upgraded.pk == media.pk
        assert upgraded.media_type == "anime"

    def test_anime_is_never_downgraded_back_to_series(self):
        media = get_or_create_media_from_tmdb(_detail(external_id="7"), "anime")
        assert media.media_type == "anime"

        same = get_or_create_media_from_tmdb(_detail(external_id="7"), "series")
        assert same.pk == media.pk
        assert same.media_type == "anime"  # nunca degrada
