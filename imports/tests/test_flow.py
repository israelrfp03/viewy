"""Flujo completo de importación: analyze_text() nunca guarda nada,
confirm_import() guarda válidos y reporta fallidos por separado, límite
máximo, duplicados, exclusión, y el viaje HTTP start→preview→confirmar."""

from unittest.mock import patch

import pytest
from django.urls import reverse

from imports.services import MAX_ITEMS, analyze_text, confirm_import
from integrations.tmdb import TMDBDetail, TMDBError, TMDBSearchResult
from library.models import MediaItem, UserMedia

pytestmark = pytest.mark.django_db


def _candidate(external_id="1", title="X", media_type="movie", is_anime=False):
    return TMDBSearchResult(external_id, "movie" if media_type == "movie" else "tv", media_type, title, 2020, "", "", is_anime)


def _detail(external_id="1", title="X", media_type="movie"):
    return TMDBDetail(
        external_id, "movie" if media_type == "movie" else "tv", media_type, title, 2020, "", "", False,
        100 if media_type == "movie" else None, None if media_type == "movie" else 24,
    )


class TestAnalyzeTextNeverSaves:
    def test_no_database_writes_happen_during_analysis(self, user):
        with patch("imports.matching.tmdb.search", return_value=[_candidate(title="Breaking Bad")]):
            analyze_text(user, "Breaking Bad 9")
        assert MediaItem.objects.count() == 0
        assert UserMedia.objects.count() == 0

    def test_max_items_limit_truncates_and_reports_it(self, user):
        text = "\n".join(f"Título {i}" for i in range(150))
        with patch("imports.matching.tmdb.search", return_value=[]):
            rows, truncated = analyze_text(user, text)
        assert len(rows) == MAX_ITEMS
        assert truncated is True

    def test_ambiguous_title_produces_no_preselected_candidate(self, user):
        candidates = [_candidate(external_id="1", title="One Piece"), _candidate(external_id="2", title="One Piece")]
        with patch("imports.matching.tmdb.search", return_value=candidates):
            rows, _ = analyze_text(user, "One Piece")
        assert rows[0]["match_state"] == "ambiguous"
        assert rows[0]["selected_external_id"] is None

    def test_already_owned_content_is_flagged(self, user, make_media, make_user_media):
        owned = make_media(title="Ya la tengo", external_source="tmdb", external_id="1")
        make_user_media(user, owned)
        with patch("imports.matching.tmdb.search", return_value=[_candidate(external_id="1", title="Ya la tengo")]):
            rows, _ = analyze_text(user, "Ya la tengo")
        assert rows[0]["already_in_library"] is True

    def test_isolation_between_users(self, make_user, make_media, make_user_media):
        owner = make_user(username="dueño")
        media = make_media(title="Dark", external_source="tmdb", external_id="1")
        make_user_media(owner, media)

        other = make_user(username="otro")
        with patch("imports.matching.tmdb.search", return_value=[_candidate(external_id="1", title="Dark")]):
            rows, _ = analyze_text(other, "Dark")
        assert rows[0]["already_in_library"] is False


class TestConfirmImport:
    def _row(self, **overrides):
        row = {
            "title": "X", "rating": 8.0, "media_type": "movie", "status": "completed",
            "match_state": "matched", "selected_external_id": "1", "selected_source_type": "movie",
            "candidates": [], "already_in_library": False, "duplicate_action": "ignore", "excluded": False,
        }
        row.update(overrides)
        return row

    def test_valid_row_is_added(self, user):
        with patch("imports.services.tmdb.get_detail", return_value=_detail()):
            summary = confirm_import(user, [self._row()])
        assert summary == {"added": 1, "updated": 0, "ignored": 0, "not_found": 0, "errors": 0}
        assert UserMedia.objects.filter(user=user, media__title="X").exists()

    def test_excluded_row_is_ignored_and_not_saved(self, user):
        summary = confirm_import(user, [self._row(excluded=True)])
        assert summary["ignored"] == 1
        assert not UserMedia.objects.filter(user=user).exists()

    def test_duplicate_with_ignore_action_does_not_change_existing(self, user, make_media, make_user_media):
        media = make_media(title="X", external_source="tmdb", external_id="1")
        make_user_media(user, media, rating=5, status="watching")

        with patch("imports.services.tmdb.get_detail", return_value=_detail()):
            confirm_import(user, [self._row(rating=9, already_in_library=True, duplicate_action="ignore")])

        entry = UserMedia.objects.get(user=user, media=media)
        assert entry.rating == 5  # sin cambios

    def test_duplicate_with_update_action_updates_existing(self, user, make_media, make_user_media):
        media = make_media(title="X", external_source="tmdb", external_id="1")
        make_user_media(user, media, rating=5, status="watching")

        with patch("imports.services.tmdb.get_detail", return_value=_detail()):
            summary = confirm_import(
                user, [self._row(rating=9, status="completed", already_in_library=True, duplicate_action="update")]
            )

        entry = UserMedia.objects.get(user=user, media=media)
        assert entry.rating == 9
        assert entry.status == "completed"
        assert summary["updated"] == 1
        assert UserMedia.objects.filter(user=user).count() == 1  # nunca duplica

    def test_row_without_selected_candidate_counts_as_not_found(self, user):
        summary = confirm_import(user, [self._row(selected_external_id=None)])
        assert summary["not_found"] == 1

    def test_partial_error_does_not_block_other_valid_rows(self, user):
        def fake_detail(external_id, source_type):
            if external_id == "fallido":
                raise TMDBError("caído")
            return _detail(external_id=external_id, title="OK")

        rows = [self._row(selected_external_id="ok", title="OK"), self._row(selected_external_id="fallido", title="Falla")]
        with patch("imports.services.tmdb.get_detail", side_effect=fake_detail):
            summary = confirm_import(user, rows)

        assert summary["added"] == 1
        assert summary["errors"] == 1

    def test_decimal_rating_is_rounded_to_integer(self, user):
        with patch("imports.services.tmdb.get_detail", return_value=_detail()):
            confirm_import(user, [self._row(rating=7.5)])
        entry = UserMedia.objects.get(user=user)
        assert entry.rating == 8


class TestHTTPFlowSessionHandling:
    def test_preview_without_prior_analysis_redirects_to_start(self, client, user):
        client.force_login(user)
        response = client.get(reverse("imports:preview"))
        assert response.status_code == 302
        assert response.url == reverse("imports:start")

    def test_full_flow_end_to_end(self, client, user):
        client.force_login(user)

        with patch("imports.matching.tmdb.search", return_value=[_candidate(external_id="1", title="Breaking Bad", media_type="series")]):
            response = client.post(reverse("imports:start"), {"text": "Breaking Bad 9"})
        assert response.status_code == 302
        assert response.url == reverse("imports:preview")

        # nada guardado todavía, aunque ya se haya "analizado"
        assert UserMedia.objects.filter(user=user).count() == 0

        with patch(
            "imports.services.tmdb.get_detail",
            return_value=_detail(external_id="1", title="Breaking Bad", media_type="series"),
        ):
            response = client.post(
                reverse("imports:preview"),
                {
                    "title_0": "Breaking Bad", "rating_0": "9", "media_type_0": "series", "status_0": "completed",
                },
            )
        assert response.status_code == 302
        assert response.url == reverse("imports:result")
        assert UserMedia.objects.filter(user=user, media__title="Breaking Bad").exists()

        # el resultado se consume una sola vez
        response = client.get(reverse("imports:result"))
        assert response.status_code == 200
        response = client.get(reverse("imports:result"))
        assert response.status_code == 302

    def test_requires_login(self, client):
        response = client.get(reverse("imports:start"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url
