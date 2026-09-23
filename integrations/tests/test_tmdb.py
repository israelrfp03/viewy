"""Cliente de TMDB, completamente mockeado — ningún test toca internet real."""

import pytest
import requests

from integrations import tmdb


def _mock_response(monkeypatch, status_code=200, json_data=None, raise_exc=None):
    def fake_get(*args, **kwargs):
        if raise_exc:
            raise raise_exc
        response = requests.Response()
        response.status_code = status_code
        response.json = lambda: json_data
        return response

    monkeypatch.setattr(tmdb.requests, "get", fake_get)


class TestSearch:
    def test_successful_search_returns_normalized_results(self, monkeypatch):
        _mock_response(
            monkeypatch,
            json_data={
                "results": [
                    {
                        "id": 1396,
                        "media_type": "tv",
                        "name": "Breaking Bad",
                        "first_air_date": "2008-01-20",
                        "poster_path": "/poster.jpg",
                        "overview": "Un profesor de química...",
                        "original_language": "en",
                        "genre_ids": [18],
                    }
                ]
            },
        )
        results = tmdb.search("Breaking Bad")
        assert len(results) == 1
        result = results[0]
        assert result.external_id == "1396"
        assert result.source_type == "tv"
        assert result.media_type == "series"  # normalizado desde "tv"
        assert result.release_year == 2008
        assert result.poster_url.endswith("/poster.jpg")
        assert result.is_anime_candidate is False

    def test_anime_candidate_heuristic_true(self, monkeypatch):
        _mock_response(
            monkeypatch,
            json_data={
                "results": [
                    {
                        "id": 37854, "media_type": "tv", "name": "One Piece",
                        "first_air_date": "1999-01-01", "poster_path": "", "overview": "",
                        "original_language": "ja", "genre_ids": [16, 10759],
                    }
                ]
            },
        )
        results = tmdb.search("One Piece")
        assert results[0].is_anime_candidate is True

    def test_western_animation_is_not_anime_candidate(self, monkeypatch):
        _mock_response(
            monkeypatch,
            json_data={
                "results": [
                    {
                        "id": 60625, "media_type": "tv", "name": "Rick and Morty",
                        "first_air_date": "2013-01-01", "poster_path": "", "overview": "",
                        "original_language": "en", "genre_ids": [16, 35],
                    }
                ]
            },
        )
        results = tmdb.search("Rick and Morty")
        assert results[0].is_anime_candidate is False

    def test_person_results_are_skipped(self, monkeypatch):
        """media_type "person" no tiene mapeo interno — se descarta, no rompe."""
        _mock_response(
            monkeypatch,
            json_data={"results": [{"id": 1, "media_type": "person", "name": "Alguien"}]},
        )
        assert tmdb.search("Alguien") == []

    def test_missing_poster_results_in_empty_string(self, monkeypatch):
        _mock_response(
            monkeypatch,
            json_data={
                "results": [
                    {
                        "id": 1, "media_type": "movie", "title": "X", "release_date": "",
                        "poster_path": None, "overview": "", "original_language": "en", "genre_ids": [],
                    }
                ]
            },
        )
        assert tmdb.search("X")[0].poster_url == ""

    def test_timeout_raises_tmdb_timeout_error(self, monkeypatch):
        _mock_response(monkeypatch, raise_exc=requests.exceptions.Timeout())
        with pytest.raises(tmdb.TMDBTimeoutError):
            tmdb.search("X")

    def test_connection_error_raises_tmdb_error(self, monkeypatch):
        _mock_response(monkeypatch, raise_exc=requests.exceptions.ConnectionError())
        with pytest.raises(tmdb.TMDBError):
            tmdb.search("X")

    def test_401_raises_auth_error(self, monkeypatch):
        _mock_response(monkeypatch, status_code=401, json_data={})
        with pytest.raises(tmdb.TMDBAuthError):
            tmdb.search("X")

    def test_unexpected_status_raises_generic_error(self, monkeypatch):
        _mock_response(monkeypatch, status_code=500, json_data={})
        with pytest.raises(tmdb.TMDBError):
            tmdb.search("X")

    def test_invalid_json_raises_tmdb_error(self, monkeypatch):
        def fake_get(*args, **kwargs):
            response = requests.Response()
            response.status_code = 200
            response.json = lambda: (_ for _ in ()).throw(ValueError("bad json"))
            return response

        monkeypatch.setattr(tmdb.requests, "get", fake_get)
        with pytest.raises(tmdb.TMDBError):
            tmdb.search("X")


class TestGetDetail:
    def test_movie_detail_has_duration_but_no_episodes(self, monkeypatch):
        _mock_response(
            monkeypatch,
            json_data={
                "id": 157336, "title": "Interstellar", "release_date": "2014-11-05",
                "poster_path": "/x.jpg", "overview": "", "original_language": "en",
                "genres": [], "runtime": 169,
            },
        )
        detail = tmdb.get_detail("157336", "movie")
        assert detail.duration_minutes == 169
        assert detail.episodes is None
        assert detail.media_type == "movie"

    def test_series_detail_has_episodes_but_no_duration(self, monkeypatch):
        _mock_response(
            monkeypatch,
            json_data={
                "id": 1396, "name": "Breaking Bad", "first_air_date": "2008-01-20",
                "poster_path": "", "overview": "", "original_language": "en",
                "genres": [], "number_of_episodes": 62,
            },
        )
        detail = tmdb.get_detail("1396", "tv")
        assert detail.episodes == 62
        assert detail.duration_minutes is None
        assert detail.media_type == "series"

    def test_zero_episodes_normalizes_to_none(self, monkeypatch):
        """Una serie recién anunciada con 0 episodios contabilizados no debe
        mostrarse como "0 episodios" — se normaliza a None (desconocido)."""
        _mock_response(
            monkeypatch,
            json_data={
                "id": 1, "name": "Nueva serie", "first_air_date": "2026-01-01",
                "poster_path": "", "overview": "", "original_language": "en",
                "genres": [], "number_of_episodes": 0,
            },
        )
        detail = tmdb.get_detail("1", "tv")
        assert detail.episodes is None

    def test_missing_title_fields_result_in_empty_string(self, monkeypatch):
        _mock_response(
            monkeypatch,
            json_data={
                "id": 1, "release_date": "", "poster_path": "", "overview": "",
                "original_language": "en", "genres": [],
            },
        )
        detail = tmdb.get_detail("1", "movie")
        assert detail.title == ""
