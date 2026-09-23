"""Clasificación de confianza del matching contra TMDB — reglas fijas, sin
machine learning. La ambigüedad nunca se resuelve sola."""

import pytest

from imports.matching import classify_match, find_candidates, resolved_media_type
from integrations.tmdb import TMDBError, TMDBSearchResult


def _candidate(external_id="1", title="X", is_anime=False, media_type="series"):
    return TMDBSearchResult(external_id, "tv", media_type, title, 2020, "", "", is_anime)


class TestClassifyMatch:
    def test_single_exact_title_match_is_matched(self):
        candidates = [_candidate(title="Interstellar")]
        state, selected = classify_match("Interstellar", candidates)
        assert state == "matched"
        assert selected.title == "Interstellar"

    def test_multiple_exact_matches_are_ambiguous_and_nothing_preselected(self):
        """Caso real: "One Piece" tiene el anime y el live-action, ambos con
        título exactamente igual — no se autoselecciona ninguno."""
        candidates = [_candidate(external_id="1", title="One Piece"), _candidate(external_id="2", title="One Piece")]
        state, selected = classify_match("One Piece", candidates)
        assert state == "ambiguous"
        assert selected is None

    def test_no_exact_match_among_fuzzy_candidates_is_ambiguous(self):
        candidates = [_candidate(title="Dark Matter"), _candidate(title="Darker")]
        state, selected = classify_match("Dark", candidates)
        assert state == "ambiguous"
        assert selected is None

    def test_no_candidates_is_not_found(self):
        state, selected = classify_match("Algo inventado", [])
        assert state == "not_found"
        assert selected is None

    def test_matching_is_case_and_whitespace_insensitive(self):
        candidates = [_candidate(title="Breaking Bad")]
        state, selected = classify_match("  breaking   bad  ", candidates)
        assert state == "matched"


class TestFindCandidates:
    def test_provider_error_is_reported_not_raised(self, monkeypatch):
        import imports.matching as matching_module

        monkeypatch.setattr(matching_module.tmdb, "search", lambda q: (_ for _ in ()).throw(TMDBError()))
        candidates, error = find_candidates("X")
        assert candidates == []
        assert error == "provider_error"


class TestResolvedMediaType:
    def test_anime_candidate_overrides_base_type(self):
        candidate = _candidate(is_anime=True, media_type="series")
        assert resolved_media_type(candidate) == "anime"

    def test_non_anime_keeps_base_type(self):
        candidate = _candidate(is_anime=False, media_type="movie")
        assert resolved_media_type(candidate) == "movie"
