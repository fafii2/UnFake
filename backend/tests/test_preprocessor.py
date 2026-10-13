"""
Tests for the text preprocessing service.
"""

from services.preprocessor import normalize_claim


class TestNormalizeClaim:
    """Tests for the normalize_claim function."""

    def test_strips_leading_trailing_whitespace(self):
        assert normalize_claim("  hello world  ") == "hello world"

    def test_collapses_multiple_spaces(self):
        assert normalize_claim("hello    world") == "hello world"

    def test_collapses_newlines_and_tabs(self):
        assert normalize_claim("hello\n\nworld\tthere") == "hello world there"

    def test_preserves_single_spaces(self):
        assert normalize_claim("hello world") == "hello world"

    def test_handles_empty_string(self):
        assert normalize_claim("") == ""

    def test_handles_only_whitespace(self):
        assert normalize_claim("   \n\t  ") == ""

    def test_preserves_unicode(self):
        result = normalize_claim("  Ang Pilipinas  ay  maganda  ")
        assert result == "Ang Pilipinas ay maganda"

    def test_preserves_special_characters(self):
        result = normalize_claim("Price: ₱3,500.00 — confirmed!")
        assert result == "Price: ₱3,500.00 — confirmed!"
