"""Fallback LLM para líneas ambiguas — una sola llamada por lote, nunca
una por línea."""

from unittest.mock import patch

import pytest

from imports import llm


class TestParseAmbiguousLines:
    def test_empty_list_never_calls_llm(self):
        with patch("imports.llm.call_gemini") as mock_call:
            result = llm.parse_ambiguous_lines([])
        assert result == {}
        assert mock_call.called is False

    def test_valid_response_maps_by_index(self):
        fake = {"items": [{"index": 0, "title": "1917", "rating": None}, {"index": 1, "title": "Se7en", "rating": 8}]}
        with patch("imports.llm.call_gemini", return_value=fake):
            result = llm.parse_ambiguous_lines(["1917", "Se7en 8"])
        assert result == {0: {"title": "1917", "rating": None}, 1: {"title": "Se7en", "rating": 8.0}}

    def test_invalid_json_shape_raises_response_error(self):
        with patch("imports.llm.call_gemini", return_value={"nope": True}):
            with pytest.raises(llm.LLMResponseError):
                llm.parse_ambiguous_lines(["X"])

    def test_rating_out_of_range_is_sanitized_to_none(self):
        fake = {"items": [{"index": 0, "title": "X", "rating": 99}]}
        with patch("imports.llm.call_gemini", return_value=fake):
            result = llm.parse_ambiguous_lines(["X"])
        assert result[0]["rating"] is None

    def test_index_out_of_bounds_is_discarded(self):
        fake = {"items": [{"index": 5, "title": "X", "rating": 8}]}
        with patch("imports.llm.call_gemini", return_value=fake):
            result = llm.parse_ambiguous_lines(["X"])
        assert result == {}

    def test_timeout_propagates(self):
        with patch("imports.llm.call_gemini", side_effect=llm.LLMTimeoutError()):
            with pytest.raises(llm.LLMTimeoutError):
                llm.parse_ambiguous_lines(["X"])
