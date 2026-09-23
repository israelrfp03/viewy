"""analytics/dataframes.py — no probamos que pandas "funcione", probamos
nuestra lógica: DataFrame vacío con columnas garantizadas, nulls, serialización
JSON (regresión del bug real de np.float64 de la Fase 9)."""

import datetime
import json

import pytest

from analytics.dataframes import (
    LIBRARY_COLUMNS,
    busiest_month,
    content_type_over_time,
    get_advanced_stats,
    get_library_dataframe,
    monthly_completions,
    rating_distribution,
    ratings_by_type,
    yearly_activity,
)

pytestmark = pytest.mark.django_db


class TestGetLibraryDataframe:
    def test_empty_user_has_all_expected_columns(self, user):
        df = get_library_dataframe(user)
        assert df.empty
        assert list(df.columns) == LIBRARY_COLUMNS

    def test_dates_are_parsed_as_datetime(self, user, make_media, make_user_media):
        import pandas as pd

        make_user_media(
            user, make_media(title="X"), status="completed", finished_at=datetime.date(2026, 3, 1)
        )
        df = get_library_dataframe(user)
        assert pd.api.types.is_datetime64_any_dtype(df["finished_at"])

    def test_isolation_between_users(self, make_user, make_media, make_user_media):
        user_a = make_user(username="a")
        user_b = make_user(username="b")
        make_user_media(user_a, make_media(title="De A"))

        assert get_library_dataframe(user_b).empty


class TestMonthlyCompletions:
    def test_ignores_rows_without_finished_at(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="X"), status="completed", finished_at=datetime.date(2026, 1, 15))
        make_user_media(user, make_media(title="Y"), status="watching", finished_at=None)

        df = get_library_dataframe(user)
        assert monthly_completions(df) == [{"month": "2026-01", "count": 1}]

    def test_empty_dataframe_returns_empty_list(self, user):
        assert monthly_completions(get_library_dataframe(user)) == []


class TestRatingsByType:
    def test_ignores_null_ratings_and_is_json_serializable(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A", media_type="anime"), rating=8)
        make_user_media(user, make_media(title="B", media_type="anime"), rating=None)

        df = get_library_dataframe(user)
        result = ratings_by_type(df)
        assert result == [{"media_type": "anime", "count": 1, "average": 8.0, "best": 8, "worst": 8}]
        json.dumps(result)  # regresión Fase 9: np.float64/np.int64 no serializaban

    def test_none_when_no_ratings(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"), rating=None)
        assert ratings_by_type(get_library_dataframe(user)) == []


class TestRatingDistribution:
    def test_counts_each_score(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"), rating=9)
        make_user_media(user, make_media(title="B"), rating=9)
        make_user_media(user, make_media(title="C"), rating=7)

        result = rating_distribution(get_library_dataframe(user))
        assert {"rating": 9, "count": 2} in result
        assert {"rating": 7, "count": 1} in result


class TestYearlyActivity:
    def test_groups_by_year(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"), status="completed", finished_at=datetime.date(2024, 1, 1))
        make_user_media(user, make_media(title="B"), status="completed", finished_at=datetime.date(2025, 1, 1))
        make_user_media(user, make_media(title="C"), status="completed", finished_at=datetime.date(2025, 6, 1))

        result = yearly_activity(get_library_dataframe(user))
        assert {"year": 2024, "count": 1} in result
        assert {"year": 2025, "count": 2} in result


class TestBusiestMonth:
    def test_returns_month_with_most_completions(self, user, make_media, make_user_media):
        for day in (1, 2):
            make_user_media(
                user, make_media(title=f"T{day}"), status="completed",
                finished_at=datetime.date(2026, 3, day),
            )
        make_user_media(user, make_media(title="Solo"), status="completed", finished_at=datetime.date(2026, 4, 1))

        assert busiest_month(get_library_dataframe(user)) == {"month": "2026-03", "count": 2}

    def test_none_when_nothing_completed(self, user):
        assert busiest_month(get_library_dataframe(user)) is None


class TestContentTypeOverTime:
    def test_always_includes_all_three_types(self, user, make_media, make_user_media):
        """Aunque el usuario solo tenga un tipo, las 3 claves deben existir
        (evita depender del filtro |default en la plantilla)."""
        make_user_media(
            user, make_media(title="X", media_type="movie"), status="completed",
            finished_at=datetime.date(2026, 1, 1),
        )
        result = content_type_over_time(get_library_dataframe(user))
        assert result == [{"month": "2026-01", "movie": 1, "series": 0, "anime": 0}]


class TestGetAdvancedStats:
    def test_full_output_is_json_serializable_even_when_empty(self, user):
        json.dumps(get_advanced_stats(user))

    def test_full_output_is_json_serializable_with_data(self, user, make_media, make_user_media):
        make_user_media(
            user, make_media(title="X", media_type="anime"), status="completed",
            rating=9, finished_at=datetime.date(2026, 1, 1),
        )
        json.dumps(get_advanced_stats(user))
