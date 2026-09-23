"""analytics/services.py — parte ORM. Biblioteca vacía, conteos, rating
medio ignorando null, aislamiento entre usuarios."""

import datetime

import pytest
from django.utils import timezone

from analytics.services import (
    anime_stats,
    get_dashboard_stats,
    get_favorites,
    get_top_rated,
    media_type_breakdown,
    movie_watch_time,
    rating_stats,
    recent_completed,
    status_counts,
)
from library.models import AnimeMetadata, UserMedia

pytestmark = pytest.mark.django_db


class TestEmptyLibrary:
    def test_dashboard_stats_has_no_errors_and_no_fake_averages(self, user):
        stats = get_dashboard_stats(user)
        assert stats["total"] == 0
        assert stats["rating_stats"]["average"] is None  # nunca 0.0 engañoso
        assert stats["movie_watch_minutes"] is None
        assert stats["anime_stats"] is None


class TestStatusCounts:
    def test_counts_each_status_correctly(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"), status="planned")
        make_user_media(user, make_media(title="B"), status="watching")
        make_user_media(user, make_media(title="C"), status="completed")
        make_user_media(user, make_media(title="D"), status="completed")

        counts = status_counts(UserMedia.objects.filter(user=user))
        assert counts == {"planned": 1, "watching": 1, "completed": 2, "dropped": 0}


class TestMediaTypeBreakdown:
    def test_percentages_sum_reasonably_and_no_division_by_zero(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A", media_type="movie"))
        make_user_media(user, make_media(title="B", media_type="movie"))
        make_user_media(user, make_media(title="C", media_type="anime"))

        queryset = UserMedia.objects.filter(user=user)
        breakdown = media_type_breakdown(queryset, queryset.count())
        assert breakdown["movie"]["count"] == 2
        assert breakdown["movie"]["percentage"] == 67
        assert breakdown["series"]["count"] == 0
        assert breakdown["series"]["percentage"] == 0


class TestRatingStats:
    def test_average_ignores_null_ratings(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"), rating=8)
        make_user_media(user, make_media(title="B"), rating=None)

        stats = rating_stats(UserMedia.objects.filter(user=user))
        assert stats["average"] == 8.0
        assert stats["rated_count"] == 1  # el sin puntuar no cuenta

    def test_best_and_worst(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="A"), rating=3)
        make_user_media(user, make_media(title="B"), rating=9)

        stats = rating_stats(UserMedia.objects.filter(user=user))
        assert stats["best"] == 9
        assert stats["worst"] == 3


class TestMovieWatchTime:
    def test_only_counts_completed_movies_with_known_duration(self, user, make_media, make_user_media):
        movie_ok = make_media(title="Peli", media_type="movie", duration_minutes=120)
        movie_unknown = make_media(title="Peli sin duración", media_type="movie", duration_minutes=None)
        series = make_media(title="Serie", media_type="series", duration_minutes=100)

        make_user_media(user, movie_ok, status="completed")
        make_user_media(user, movie_unknown, status="completed")
        make_user_media(user, series, status="completed")

        total = movie_watch_time(UserMedia.objects.filter(user=user))
        assert total == 120


class TestRecentCompleted:
    def test_excludes_completed_items_without_finished_at(self, user, make_media, make_user_media):
        """Regresión: el orden de NULL en finished_at DESC no es portable
        entre SQLite y MySQL (Fase 8) — nunca debe depender de eso."""
        make_user_media(user, make_media(title="Sin fecha"), status="completed", finished_at=None)
        with_date = make_user_media(
            user, make_media(title="Con fecha"), status="completed", finished_at=datetime.date(2026, 1, 1)
        )

        result = list(recent_completed(UserMedia.objects.filter(user=user)))
        assert result == [with_date]

    def test_respects_limit(self, user, make_media, make_user_media):
        for i in range(10):
            make_user_media(
                user, make_media(title=f"T{i}"), status="completed",
                finished_at=datetime.date(2026, 1, i + 1),
            )
        result = recent_completed(UserMedia.objects.filter(user=user), limit=3)
        assert len(result) == 3


class TestTemporalStats:
    def test_completed_this_month_counts_current_month_only(self, user, make_media, make_user_media):
        today = timezone.now().date()
        last_year = datetime.date(today.year - 1, 1, 1)  # fecha fija que nunca es "este mes/año"

        make_user_media(user, make_media(title="Este mes"), status="completed", finished_at=today)
        make_user_media(user, make_media(title="Año pasado"), status="completed", finished_at=last_year)

        stats = get_dashboard_stats(user)["temporal_stats"]
        assert stats["completed_this_month"] == 1
        assert stats["completed_this_year"] == 1


class TestAnimeStats:
    def test_none_when_no_enriched_anime(self, user):
        assert anime_stats(user) is None

    def test_returns_most_frequent_studio(self, user, make_media, make_user_media):
        m1 = make_media(title="A", media_type="anime")
        m2 = make_media(title="B", media_type="anime")
        make_user_media(user, m1)
        make_user_media(user, m2)
        AnimeMetadata.objects.create(media=m1, external_id="1", studio="Toei Animation")
        AnimeMetadata.objects.create(media=m2, external_id="2", studio="Toei Animation")

        result = anime_stats(user)
        assert result["top_studio"]["studio"] == "Toei Animation"
        assert result["top_studio"]["count"] == 2


class TestTopRatedAndFavorites:
    def test_get_top_rated_filters_by_media_type(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Peli", media_type="movie"), rating=9)
        make_user_media(user, make_media(title="Anime", media_type="anime"), rating=8)

        result = get_top_rated(user, media_type="anime")
        assert [e.media.title for e in result] == ["Anime"]

    def test_get_favorites_only_returns_favorited(self, user, make_media, make_user_media):
        make_user_media(user, make_media(title="Fav"), favorite=True)
        make_user_media(user, make_media(title="NoFav"), favorite=False)

        result = get_favorites(user)
        assert [e.media.title for e in result] == ["Fav"]


class TestIsolationBetweenUsers:
    def test_dashboard_stats_never_mixes_users(self, make_user, make_media, make_user_media):
        user_a = make_user(username="a")
        user_b = make_user(username="b")
        make_user_media(user_a, make_media(title="De A"), rating=10)

        stats_a = get_dashboard_stats(user_a)
        stats_b = get_dashboard_stats(user_b)
        assert stats_a["total"] == 1
        assert stats_b["total"] == 0
