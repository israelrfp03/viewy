"""build_taste_profile() (contexto compacto, sin datos personales) y
get_recommendations() (orquestador: LLM mockeado + verificación TMDB)."""

from unittest.mock import patch

import pytest

from integrations.tmdb import TMDBSearchResult
from library.models import MediaItem
from recommendations import llm
from recommendations.services import build_taste_profile, get_recommendations

pytestmark = pytest.mark.django_db


class TestBuildTasteProfile:
    def test_empty_library_returns_none_and_never_calls_llm(self, user):
        with patch("recommendations.services.get_recommendations_from_llm") as mock_llm:
            profile, is_thin, titles = build_taste_profile(user)
            assert profile is None
            assert mock_llm.called is False

    def test_profile_never_contains_username_or_email(self, make_user, make_media, make_user_media):
        secret_user = make_user(username="usuario_secreto_123", email="privado@ejemplo.com")
        make_user_media(secret_user, make_media(title="X"), rating=8)

        profile, _, _ = build_taste_profile(secret_user)
        assert "usuario_secreto_123" not in profile
        assert "privado@ejemplo.com" not in profile

    def test_thin_profile_without_ratings_or_favorites(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"))
        _, is_thin, _ = build_taste_profile(user)
        assert is_thin is True

    def test_not_thin_when_user_has_ratings(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"), rating=8)
        _, is_thin, _ = build_taste_profile(user)
        assert is_thin is False

    def test_dedup_titles_capped_at_max(self, user, make_media, make_user_media):
        for i in range(150):
            make_user_media(user, make_media(title=f"T{i}"))
        _, _, titles = build_taste_profile(user)
        assert len(titles) == 100


class TestGetRecommendations:
    def test_empty_library_returns_not_enough_data(self, user):
        results, error, _ = get_recommendations(user, "")
        assert error == "not_enough_data"
        assert results == []

    def test_llm_error_returns_llm_unavailable(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"), rating=8)
        with patch("recommendations.services.get_recommendations_from_llm", side_effect=llm.LLMError()):
            results, error, _ = get_recommendations(user, "")
        assert error == "llm_unavailable"

    def test_already_owned_content_is_excluded_even_if_llm_suggests_it(
        self, user, make_media, make_user_media
    ):
        owned = make_media(title="Ya la tengo", media_type="series", external_source="tmdb", external_id="1")
        make_user_media(user, owned, rating=9)

        fake_llm_response = [{"title": "Ya la tengo", "media_type": "series", "reason": "r"}]
        fake_candidate = [TMDBSearchResult("1", "tv", "series", "Ya la tengo", 2020, "", "", False)]

        with patch("recommendations.services.get_recommendations_from_llm", return_value=fake_llm_response), \
             patch("recommendations.services.tmdb.search", return_value=fake_candidate):
            results, error, _ = get_recommendations(user, "")

        assert error == "no_verifiable_results"
        assert results == []

    def test_tmdb_anime_heuristic_overrides_llm_media_type(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"), rating=8)
        fake_llm_response = [{"title": "One Piece", "media_type": "series", "reason": "r"}]
        fake_candidate = [TMDBSearchResult("77", "tv", "series", "One Piece", 1999, "", "", True)]

        with patch("recommendations.services.get_recommendations_from_llm", return_value=fake_llm_response), \
             patch("recommendations.services.tmdb.search", return_value=fake_candidate):
            results, error, _ = get_recommendations(user, "")

        assert error is None
        assert results[0]["media_type"] == "anime"  # TMDB manda, no el LLM

    def test_no_verifiable_results_when_tmdb_finds_nothing(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"), rating=8)
        fake_llm_response = [{"title": "Título inventado", "media_type": "movie", "reason": "r"}]

        with patch("recommendations.services.get_recommendations_from_llm", return_value=fake_llm_response), \
             patch("recommendations.services.tmdb.search", return_value=[]):
            results, error, _ = get_recommendations(user, "")

        assert error == "no_verifiable_results"

    def test_isolation_between_users(self, make_user, make_media, make_user_media):
        user_a = make_user(username="a")
        user_b = make_user(username="b")
        make_user_media(user_a, make_media(title="Solo de A"), rating=9)

        with patch("recommendations.services.get_recommendations_from_llm") as mock_llm:
            get_recommendations(user_b, "")
            assert mock_llm.called is False  # user_b no tiene biblioteca
