"""
Tests for the enhanced text preprocessing service.
"""

from services.preprocessor import (
    clean_repeated_punctuation,
    normalize_claim,
    normalize_quotes,
    strip_enclosing_quotes,
    strip_leading_bullets_and_prefixes,
)


class TestNormalizeQuotes:
    """Tests for quote normalization."""

    def test_curly_quotes_converted(self):
        assert normalize_quotes("“hello” and ‘world’") == '"hello" and \'world\''

    def test_guillemets_converted(self):
        assert normalize_quotes("«balita»") == '"balita"'


class TestStripEnclosingQuotes:
    """Tests for stripping wrapping quotes and brackets."""

    def test_strips_double_quotes(self):
        assert strip_enclosing_quotes('"The world is round"') == "The world is round"

    def test_strips_single_quotes(self):
        assert strip_enclosing_quotes("'The world is round'") == "The world is round"

    def test_strips_square_brackets(self):
        assert strip_enclosing_quotes("[Breaking Report]") == "Breaking Report"

    def test_does_not_strip_internal_quotes(self):
        claim = 'Marcos stated "no new taxes" in 2024.'
        assert strip_enclosing_quotes(claim) == claim


class TestCleanRepeatedPunctuation:
    """Tests for collapsing repeated punctuation."""

    def test_collapses_multiple_question_marks(self):
        assert clean_repeated_punctuation("Totoo ba ito???") == "Totoo ba ito?"

    def test_collapses_multiple_exclamation_marks(self):
        assert clean_repeated_punctuation("Huwag maniwala!!!!") == "Huwag maniwala!"

    def test_collapses_excessive_dots(self):
        assert clean_repeated_punctuation("Waiting.....") == "Waiting..."


class TestStripPrefixes:
    """Tests for broadcast and bullet prefix stripping."""

    def test_strips_breaking_news(self):
        assert strip_leading_bullets_and_prefixes("BREAKING NEWS: Bagyong Nika hits Luzon") == "Bagyong Nika hits Luzon"

    def test_strips_just_in(self):
        assert strip_leading_bullets_and_prefixes("JUST IN - Sotto files bill") == "Sotto files bill"

    def test_strips_tagalog_prefix(self):
        assert strip_leading_bullets_and_prefixes("BALITA: Bagong tulay binuksan") == "Bagong tulay binuksan"

    def test_strips_bullet_points(self):
        assert strip_leading_bullets_and_prefixes("- PhilHealth increases benefits") == "PhilHealth increases benefits"
        assert strip_leading_bullets_and_prefixes("• DOTr orders fare rollback") == "DOTr orders fare rollback"
        assert strip_leading_bullets_and_prefixes("1. DepEd begins school year") == "DepEd begins school year"


class TestNormalizeClaimEndToEnd:
    """Comprehensive end-to-end normalization tests."""

    def test_cleans_messy_social_media_selection(self):
        raw = '  “BREAKING NEWS:  President signs  RA 11954 in Malacañang!!!”  '
        expected = "President signs RA 11954 in Malacañang!"
        assert normalize_claim(raw) == expected

    def test_collapses_newlines_and_tabs(self):
        raw = "Philippine\n\ninflation rate\tdropped to 3.3%."
        expected = "Philippine inflation rate dropped to 3.3%."
        assert normalize_claim(raw) == expected

    def test_handles_empty_and_whitespace(self):
        assert normalize_claim("") == ""
        assert normalize_claim("   \n\t  ") == ""

    def test_preserves_currency_and_numbers(self):
        raw = '  [JUST IN] Budget reached ₱5.768 trillion for fiscal year 2024  '
        expected = "Budget reached ₱5.768 trillion for fiscal year 2024"
        assert normalize_claim(raw) == expected

    def test_preserves_tagalog_characters(self):
        raw = "‘BALITA: May 7,641 na mga pulo sa Pilipinas ayon sa NAMRIA.’"
        expected = "May 7,641 na mga pulo sa Pilipinas ayon sa NAMRIA."
        assert normalize_claim(raw) == expected
