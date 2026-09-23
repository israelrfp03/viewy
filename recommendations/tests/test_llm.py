"""Validación del structured output de recomendaciones — nunca confiar
ciegamente en lo que devuelve el LLM, ni siquiera con schema forzado."""

from unittest.mock import patch

from recommendations import llm


class TestGetRecommendationsFromLLM:
    def test_valid_response_is_returned(self):
        fake = {"recommendations": [{"title": "Arcane", "media_type": "series", "reason": "Buena animación"}]}
        with patch("recommendations.llm.call_gemini", return_value=fake):
            result = llm.get_recommendations_from_llm("sys", "user")
        assert result == [{"title": "Arcane", "media_type": "series", "reason": "Buena animación"}]

    def test_missing_recommendations_key_raises_response_error(self):
        with patch("recommendations.llm.call_gemini", return_value={"nope": True}):
            try:
                llm.get_recommendations_from_llm("sys", "user")
                assert False
            except llm.LLMResponseError:
                pass

    def test_item_missing_media_type_is_dropped_not_fatal(self):
        fake = {
            "recommendations": [
                {"title": "Sin tipo", "reason": "r"},
                {"title": "Válido", "media_type": "movie", "reason": "r"},
            ]
        }
        with patch("recommendations.llm.call_gemini", return_value=fake):
            result = llm.get_recommendations_from_llm("sys", "user")
        assert len(result) == 1
        assert result[0]["title"] == "Válido"

    def test_invalid_media_type_value_is_dropped(self):
        fake = {"recommendations": [{"title": "X", "media_type": "documental", "reason": "r"}]}
        with patch("recommendations.llm.call_gemini", return_value=fake):
            result = llm.get_recommendations_from_llm("sys", "user")
        assert result == []

    def test_result_capped_at_max_recommendations(self):
        items = [{"title": f"T{i}", "media_type": "movie", "reason": "r"} for i in range(20)]
        with patch("recommendations.llm.call_gemini", return_value={"recommendations": items}):
            result = llm.get_recommendations_from_llm("sys", "user")
        assert len(result) == llm.MAX_RECOMMENDATIONS

    def test_timeout_propagates_as_llm_timeout_error(self):
        with patch("recommendations.llm.call_gemini", side_effect=llm.LLMTimeoutError()):
            try:
                llm.get_recommendations_from_llm("sys", "user")
                assert False
            except llm.LLMTimeoutError:
                pass
