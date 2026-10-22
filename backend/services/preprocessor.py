"""
Text preprocessing service.

Normalizes and cleans user-submitted claim text before verification:
- Normalizes typographic quotes and Unicode characters
- Strips enclosing quotes, brackets, and leading bullets/prefixes
- Collapses repeated punctuation (e.g. ??? -> ?, !!! -> !)
- Collapses multi-line and excessive whitespace
- Preserves semantic meaning, named entities, numbers, and dates
"""

import re
import unicodedata

# Common news/social broadcast prefixes to clean off claims (e.g. "BREAKING:", "[JUST IN]", "(ALERT)")
BROADCAST_PREFIXES_REGEX = re.compile(
    r"^(?:[\[\(]?(?:breaking(?:\s+news)?|just\s+in|alert|urgent|balita|ulat|update|fyi|flash(?:\s+report)?)\b[\]\)]?\s*[:\-–—]?\s*)+",
    re.IGNORECASE,
)

# Repeated punctuation: ??? -> ?, !!! -> !, .... -> ...
REPEATED_QUESTION_REGEX = re.compile(r"\?{2,}")
REPEATED_EXCLAMATION_REGEX = re.compile(r"!{2,}")
REPEATED_DOTS_REGEX = re.compile(r"\.{4,}")


def normalize_quotes(text: str) -> str:
    """Normalize typographic quotes and apostrophes to standard ASCII quotes."""
    replacements = {
        "“": '"',
        "”": '"',
        "„": '"',
        "«": '"',
        "»": '"',
        "‘": "'",
        "’": "'",
        "`": "'",
        "‚": "'",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def strip_enclosing_quotes(text: str) -> str:
    """Strip matching quotation marks or brackets wrapping the entire claim."""
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        if len(text) >= 2:
            text = text[1:-1].strip()
    elif (text.startswith("[") and text.endswith("]")) or (
        text.startswith("(") and text.endswith(")")
    ):
        if len(text) >= 2:
            text = text[1:-1].strip()
    return text


def clean_repeated_punctuation(text: str) -> str:
    """Collapse excessive punctuation while keeping standard punctuation intact."""
    text = REPEATED_QUESTION_REGEX.sub("?", text)
    text = REPEATED_EXCLAMATION_REGEX.sub("!", text)
    text = REPEATED_DOTS_REGEX.sub("...", text)
    return text


def strip_leading_bullets_and_prefixes(text: str) -> str:
    """Remove list numbers, bullets, and breaking news headers."""
    # Remove leading list bullets / numbers (e.g., "- Claim", "1. Claim")
    if re.match(r"^[\-\*\•]\s+\S", text):
        text = re.sub(r"^[\-\*\•]\s+", "", text)
    elif re.match(r"^\d+[\.\)]\s+\S", text):
        text = re.sub(r"^\d+[\.\)]\s+", "", text)

    # Remove broadcast labels like "BREAKING NEWS: "
    text = BROADCAST_PREFIXES_REGEX.sub("", text)
    return text.strip()


def normalize_claim(raw_text: str) -> str:
    """
    Comprehensive normalization for factual claims.

    Args:
        raw_text: Raw text as captured from the user's selection.

    Returns:
        Cleaned, normalized claim preserving original meaning.
    """
    if not raw_text:
        return ""

    # Normalize unicode characters (NFC form)
    text = unicodedata.normalize("NFC", raw_text)
    # Drop only whole UI/timestamp lines, never dates or words inside an assertion.
    noise = re.compile(r"^(?:(?:like|reply|share|see more|see less)|\d+\s*(?:h|hr|hrs|min|mins)\s*(?:ago)?|\[?\d{1,2}:\d{2}\s*(?:am|pm)?\]?)$", re.I)
    text = '\n'.join(line for line in text.splitlines() if not noise.fullmatch(line.strip()))

    # Normalize typographic quotes to straight quotes
    text = normalize_quotes(text)

    # Collapse whitespace (newlines, tabs, multiple spaces)
    text = " ".join(text.split())

    # Strip enclosing quotes or brackets
    text = strip_enclosing_quotes(text)

    # Strip leading bullets and broadcast prefixes
    text = strip_leading_bullets_and_prefixes(text)

    # If stripping prefixes revealed another layer of enclosing quotes, strip them
    text = strip_enclosing_quotes(text)

    # Collapse repeated punctuation
    text = clean_repeated_punctuation(text)

    return text.strip()
