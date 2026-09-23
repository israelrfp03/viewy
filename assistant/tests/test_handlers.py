"""Cada handler ejecuta ORM/pandas real sobre datos reales — el LLM nunca
participa aquí. Cubre los intents que pide explícitamente la Fase 14."""

import datetime

import pytest

from assistant.handlers import INTENT_HANDLERS
from assistant.responses import RESPONSE_RENDERERS

pytestmark = pytest.mark.django_db

DEFAULT_FILTERS = {
    "media_type": None, "status": None, "year": None, "month": None,
    "limit": 5, "clarify_question": None, "recommendation_text": "",
}


def _filters(**overrides):
    filters = dict(DEFAULT_FILTERS)
    filters.update(overrides)
    return filters


def _run(intent, user, **filter_overrides):
    filters = _filters(**filter_overrides)
    result = INTENT_HANDLERS[intent](user, filters)
    text = RESPONSE_RENDERERS[intent](result, filters)
    return result, text


class TestAverageRating:
    def test_with_data(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"), rating=8)
        result, text = _run("average_rating", user)
        assert result["average"] == 8.0
        assert "8.0" in text

    def test_without_data_does_not_fake_a_zero(self, user):
        result, text = _run("average_rating", user)
        assert result["average"] is None
        assert "0.0" not in text

    def test_filtered_by_media_type_uses_pandas(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Peli", media_type="movie"), rating=5)
        make_user_media(user, make_media(title="Anime", media_type="anime"), rating=9)
        result, _ = _run("average_rating", user, media_type="anime")
        assert result["average"] == 9.0


class TestCountByType:
    def test_all_types(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A", media_type="movie"))
        make_user_media(user, make_media(title="B", media_type="anime"))
        result, text = _run("count_by_type", user)
        assert result["breakdown"]["movie"]["count"] == 1
        assert "película" in text.lower()


class TestCompletedByPeriod:
    def test_filters_by_year_and_type(self, user, make_media, make_user_media):
        make_user_media(
            user, make_media(title="Anime 2025", media_type="anime"), status="completed",
            finished_at=datetime.date(2025, 6, 1),
        )
        make_user_media(
            user, make_media(title="Peli 2025", media_type="movie"), status="completed",
            finished_at=datetime.date(2025, 6, 1),
        )
        result, text = _run("completed_by_period", user, year=2025, media_type="anime")
        assert result["value"] == 1
        assert "2025" in text


class TestTopRated:
    def test_orders_by_rating_desc(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Baja"), rating=5)
        make_user_media(user, make_media(title="Alta"), rating=9)
        result, text = _run("top_rated", user, limit=1)
        assert result["items"][0]["title"] == "Alta"
        assert "Alta" in text


class TestRecentlyCompleted:
    def test_returns_most_recent_first(self, user, make_media, make_user_media):
        make_user_media(
            user, make_media(title="Vieja"), status="completed", finished_at=datetime.date(2025, 1, 1)
        )
        make_user_media(
            user, make_media(title="Nueva"), status="completed", finished_at=datetime.date(2026, 1, 1)
        )
        result, _ = _run("recently_completed", user)
        assert result["items"][0]["title"] == "Nueva"


class TestFavorites:
    def test_returns_only_favorited(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Fav"), favorite=True)
        make_user_media(user, make_media(title="NoFav"), favorite=False)
        result, text = _run("favorites", user)
        assert [i["title"] for i in result["items"]] == ["Fav"]


class TestItemsByStatus:
    def test_planned_items(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Pendiente"), status="planned")
        make_user_media(user, make_media(title="Viendo"), status="watching")
        result, _ = _run("items_by_status", user, status="planned")
        assert [i["title"] for i in result["items"]] == ["Pendiente"]

    def test_no_items_for_that_status(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"), status="completed")
        result, text = _run("items_by_status", user, status="dropped")
        assert result["items"] == []
        assert "No tienes" in text


class TestTotalLibrary:
    def test_empty_library_does_not_show_a_raw_zero(self, user):
        result, text = _run("total_library", user)
        assert result["value"] == 0
        assert "Todavía no tienes" in text

    def test_with_items(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"))
        result, text = _run("total_library", user)
        assert result["value"] == 1
        assert "1" in text
