"""Parser determinista: separadores variados, casos límite numéricos ya
encontrados en la Fase 13 ("1917", "Se7en"), líneas vacías."""

import pytest

from imports.parsing import parse_line, parse_text


class TestParseText:
    def test_empty_text_returns_no_lines(self):
        assert parse_text("") == []

    def test_blank_lines_are_skipped(self):
        result = parse_text("Dark 9\n\n   \nBreaking Bad")
        assert len(result) == 2

    def test_single_line(self):
        result = parse_text("Dark 9")
        assert len(result) == 1

    def test_multiple_lines(self):
        result = parse_text("Dark 9\nBreaking Bad 10\nOne Piece 8")
        assert len(result) == 3


class TestSeparators:
    @pytest.mark.parametrize(
        "line,expected_title,expected_rating",
        [
            ("Dark 9", "Dark", 9.0),
            ("Dark: 9", "Dark", 9.0),
            ("Dark - 9", "Dark", 9.0),
            ("Dark - 9/10", "Dark", 9.0),
            ("Dark | 7.5", "Dark", 7.5),
            ("Dark | 7,5", "Dark", 7.5),
            ("Dark (9)", "Dark", 9.0),
            ("Dark ⭐ 9", "Dark", 9.0),
        ],
    )
    def test_recognized_separator_formats(self, line, expected_title, expected_rating):
        result = parse_line(line)
        assert result.title == expected_title
        assert result.rating == expected_rating
        assert result.confidence == "high"

    def test_title_without_rating_is_high_confidence(self):
        result = parse_line("Breaking Bad")
        assert result.title == "Breaking Bad"
        assert result.rating is None
        assert result.confidence == "high"


class TestNumericEdgeCases:
    def test_purely_numeric_title_is_low_confidence(self):
        """"1917" no debe interpretarse como título="191" rating=7."""
        result = parse_line("1917")
        assert result.confidence == "low"
        assert result.title == "1917"
        assert result.rating is None

    def test_digit_embedded_in_title_is_low_confidence(self):
        result = parse_line("Se7en")
        assert result.confidence == "low"

    def test_title_with_no_digits_is_never_low_confidence(self):
        result = parse_line("The Matrix")
        assert result.confidence == "high"


class TestInvalidLine:
    def test_whitespace_only_line_returns_none(self):
        assert parse_line("   ") is None

    def test_empty_string_returns_none(self):
        assert parse_line("") is None
