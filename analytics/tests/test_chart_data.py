"""chart_data.py: forma exacta que consume Chart.js. No probamos Chart.js,
probamos que el backend entrega la estructura correcta."""

import datetime
import json

import pytest

from analytics.chart_data import build_chart_data
from analytics.services import get_dashboard_stats

pytestmark = pytest.mark.django_db


def test_empty_library_returns_all_none(user):
    chart_data = build_chart_data(get_dashboard_stats(user))
    assert all(value is None for value in chart_data.values())


def test_type_breakdown_excludes_zero_count_types(user, make_media, make_user_media):
    make_user_media(user, make_media(title="X", media_type="movie"))
    chart_data = build_chart_data(get_dashboard_stats(user))
    assert chart_data["type_breakdown"]["labels"] == ["Película"]
    assert chart_data["type_breakdown"]["data"] == [1]


def test_monthly_activity_labels_and_values_are_coherent(user, make_media, make_user_media):
    make_user_media(
        user, make_media(title="X"), status="completed", finished_at=datetime.date(2026, 5, 1)
    )
    chart_data = build_chart_data(get_dashboard_stats(user))
    assert chart_data["monthly_activity"] == {"labels": ["2026-05"], "data": [1]}


def test_type_over_time_has_three_datasets(user, make_media, make_user_media):
    make_user_media(
        user, make_media(title="X", media_type="anime"), status="completed",
        finished_at=datetime.date(2026, 1, 1),
    )
    chart_data = build_chart_data(get_dashboard_stats(user))
    assert set(chart_data["type_over_time"]["datasets"].keys()) == {"movie", "series", "anime"}


def test_full_payload_is_json_serializable(user, make_media, make_user_media):
    make_user_media(
        user, make_media(title="X", media_type="anime"), status="completed",
        rating=9, finished_at=datetime.date(2026, 1, 1),
    )
    chart_data = build_chart_data(get_dashboard_stats(user))
    json.dumps(chart_data)


def test_isolation_between_users(make_user, make_media, make_user_media):
    user_a = make_user(username="a")
    user_b = make_user(username="b")
    make_user_media(
        user_a, make_media(title="X"), status="completed", finished_at=datetime.date(2026, 1, 1)
    )
    chart_data_b = build_chart_data(get_dashboard_stats(user_b))
    assert chart_data_b["monthly_activity"] is None
