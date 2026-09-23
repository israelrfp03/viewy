"""Flujo de búsqueda/alta desde TMDB (Fase 6) y enriquecimiento con
AniList/Jikan (Fase 7.5) — completamente mockeado."""

from unittest.mock import patch

import pytest
from django.urls import reverse

from integrations import tmdb
from integrations.anime_provider import AnimeProviderUnavailable
from integrations.tmdb import TMDBDetail, TMDBSearchResult
from library.models import AnimeMetadata, MediaItem, UserMedia

pytestmark = pytest.mark.django_db


class TestMediaSearch:
    def test_successful_search_shows_results(self, client, user):
        client.force_login(user)
        fake_results = [TMDBSearchResult("1", "movie", "movie", "Interstellar", 2014, "", "", False)]
        with patch("library.views.tmdb.search", return_value=fake_results):
            response = client.get(reverse("library:search"), {"q": "Interstellar"})
        assert response.status_code == 200
        assert b"Interstellar" in response.content

    def test_provider_down_shows_friendly_message_not_500(self, client, user):
        client.force_login(user)
        with patch("library.views.tmdb.search", side_effect=tmdb.TMDBError("caído")):
            response = client.get(reverse("library:search"), {"q": "X"})
        assert response.status_code == 200


class TestMediaAddFromTMDB:
    def test_valid_selection_creates_media_and_entry(self, client, user):
        client.force_login(user)
        with patch(
            "library.views.tmdb.get_detail",
            return_value=TMDBDetail("1", "movie", "movie", "Interstellar", 2014, "", "", False, 169, None),
        ):
            response = client.post(
                reverse("library:add_from_tmdb"),
                {"external_id": "1", "source_type": "movie", "media_type": "movie"},
            )
        assert response.status_code == 302
        assert UserMedia.objects.filter(user=user, media__title="Interstellar").exists()

    def test_invalid_source_type_is_rejected(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse("library:add_from_tmdb"),
            {"external_id": "1", "source_type": "no_valido", "media_type": "movie"},
        )
        assert response.status_code == 302
        assert not MediaItem.objects.filter(external_id="1").exists()

    def test_adding_same_content_twice_does_not_duplicate_user_media(self, client, user):
        client.force_login(user)
        with patch(
            "library.views.tmdb.get_detail",
            return_value=TMDBDetail("1", "movie", "movie", "X", 2020, "", "", False, 100, None),
        ):
            client.post(reverse("library:add_from_tmdb"), {"external_id": "1", "source_type": "movie", "media_type": "movie"})
            client.post(reverse("library:add_from_tmdb"), {"external_id": "1", "source_type": "movie", "media_type": "movie"})
        assert UserMedia.objects.filter(user=user, media__external_id="1").count() == 1

    def test_provider_error_does_not_crash(self, client, user):
        client.force_login(user)
        with patch("library.views.tmdb.get_detail", side_effect=tmdb.TMDBError("caído")):
            response = client.post(
                reverse("library:add_from_tmdb"),
                {"external_id": "1", "source_type": "movie", "media_type": "movie"},
            )
        assert response.status_code == 302
        assert MediaItem.objects.count() == 0


class TestAnimeEnrichmentFlow:
    def test_detail_shows_enrichment_when_available(self, client, user, make_media, make_user_media):
        media = make_media(title="One Piece", media_type="anime")
        AnimeMetadata.objects.create(media=media, external_source="anilist", external_id="1", studio="Toei")
        entry = make_user_media(user, media)
        client.force_login(user)

        fake_enrichment = type("E", (), {"characters": [], "staff": [], "relations": [], "episodes": []})()
        with patch("library.views.get_anime_enrichment", return_value=fake_enrichment):
            response = client.get(reverse("library:detail", args=[entry.pk]))
        assert response.status_code == 200

    def test_detail_degrades_gracefully_when_provider_unavailable(self, client, user, make_media, make_user_media):
        media = make_media(title="One Piece", media_type="anime")
        AnimeMetadata.objects.create(media=media, external_source="anilist", external_id="1")
        entry = make_user_media(user, media)
        client.force_login(user)

        with patch("library.views.get_anime_enrichment", side_effect=AnimeProviderUnavailable()):
            response = client.get(reverse("library:detail", args=[entry.pk]))
        assert response.status_code == 200  # nunca un 500, biblioteca sigue funcionando

    def test_search_candidates_shows_provider_unavailable_message(self, client, user, make_media, make_user_media):
        media = make_media(title="One Piece", media_type="anime")
        entry = make_user_media(user, media)
        client.force_login(user)

        with patch("library.views.search_anime", side_effect=AnimeProviderUnavailable()):
            response = client.get(reverse("library:anime_search", args=[entry.pk]))
        assert response.status_code == 200

    def test_confirm_match_rejects_unknown_source(self, client, user, make_media, make_user_media):
        media = make_media(title="One Piece", media_type="anime")
        entry = make_user_media(user, media)
        client.force_login(user)

        response = client.post(
            reverse("library:anime_confirm", args=[entry.pk]),
            {"external_id": "1", "source": "proveedor_inventado"},
        )
        assert response.status_code == 302
        assert not AnimeMetadata.objects.filter(media=media).exists()

    def test_only_anime_can_be_enriched(self, client, user, make_media, make_user_media):
        movie = make_media(title="Interstellar", media_type="movie")
        entry = make_user_media(user, movie)
        client.force_login(user)

        response = client.get(reverse("library:anime_search", args=[entry.pk]))
        assert response.status_code == 302
        assert response.url == reverse("library:detail", args=[entry.pk])

    def test_confirm_match_creates_anime_metadata(self, client, user, make_media, make_user_media):
        media = make_media(title="One Piece", media_type="anime")
        entry = make_user_media(user, media)
        client.force_login(user)

        fake_enrichment = type(
            "E",
            (),
            {
                "external_id": "1",
                "title_romaji": "One Piece",
                "title_english": "One Piece",
                "source_material": "manga",
                "studio": "Toei Animation",
            },
        )()
        with patch("library.views.get_anime_enrichment", return_value=fake_enrichment):
            response = client.post(
                reverse("library:anime_confirm", args=[entry.pk]),
                {"external_id": "1", "source": "anilist"},
            )

        assert response.status_code == 302
        metadata = AnimeMetadata.objects.get(media=media)
        assert metadata.external_source == "anilist"
        assert metadata.studio == "Toei Animation"

    def test_confirm_match_updates_existing_metadata_without_duplicating(
        self, client, user, make_media, make_user_media
    ):
        media = make_media(title="One Piece", media_type="anime")
        AnimeMetadata.objects.create(media=media, external_source="jikan", external_id="99", studio="Viejo")
        entry = make_user_media(user, media)
        client.force_login(user)

        fake_enrichment = type(
            "E",
            (),
            {
                "external_id": "1",
                "title_romaji": "One Piece",
                "title_english": "One Piece",
                "source_material": "manga",
                "studio": "Toei Animation",
            },
        )()
        with patch("library.views.get_anime_enrichment", return_value=fake_enrichment):
            client.post(
                reverse("library:anime_confirm", args=[entry.pk]),
                {"external_id": "1", "source": "anilist"},
            )

        assert AnimeMetadata.objects.filter(media=media).count() == 1
        metadata = AnimeMetadata.objects.get(media=media)
        assert metadata.studio == "Toei Animation"

    def test_confirm_match_rejects_id_already_linked_to_another_title(
        self, client, user, make_media, make_user_media
    ):
        other_media = make_media(title="Naruto", media_type="anime")
        AnimeMetadata.objects.create(media=other_media, external_source="anilist", external_id="1")

        media = make_media(title="One Piece", media_type="anime")
        entry = make_user_media(user, media)
        client.force_login(user)

        fake_enrichment = type("E", (), {"external_id": "1"})()
        with patch("library.views.get_anime_enrichment", return_value=fake_enrichment):
            response = client.post(
                reverse("library:anime_confirm", args=[entry.pk]),
                {"external_id": "1", "source": "anilist"},
            )

        assert response.status_code == 302
        assert not AnimeMetadata.objects.filter(media=media).exists()

    def test_confirm_match_provider_unavailable_does_not_crash(self, client, user, make_media, make_user_media):
        media = make_media(title="One Piece", media_type="anime")
        entry = make_user_media(user, media)
        client.force_login(user)

        with patch("library.views.get_anime_enrichment", side_effect=AnimeProviderUnavailable()):
            response = client.post(
                reverse("library:anime_confirm", args=[entry.pk]),
                {"external_id": "1", "source": "anilist"},
            )

        assert response.status_code == 302
        assert not AnimeMetadata.objects.filter(media=media).exists()


class TestHomeView:
    def test_authenticated_user_sees_quick_stats_and_watchlist(self, client, user, make_media, make_user_media):
        media = make_media(title="Interstellar")
        make_user_media(user, media, favorite=True, status="completed", rating=9)
        client.force_login(user)

        response = client.get(reverse("library:home"))

        assert response.status_code == 200
        assert response.context["quick_stats"]["total"] == 1
        assert response.context["quick_stats"]["favorites"] == 1

    def test_anonymous_user_sees_page_without_stats(self, client):
        response = client.get(reverse("library:home"))
        assert response.status_code == 200
        assert response.context.get("quick_stats") is None
