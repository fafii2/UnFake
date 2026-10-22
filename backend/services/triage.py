"""
Rule-based claim triage engine.

Distinguishes potentially verifiable factual claims from:
- Subjective opinions and personal beliefs
- Inquiries and rhetorical questions
- Sarcasm, slang, and casual commentary
- Truncated sentence fragments

Supports English, Tagalog, and Taglish text.
"""

from __future__ import annotations

import re
from enum import Enum


class TriageCategory(str, Enum):
    """Classification categories produced by the triage engine."""
    FACTUAL_ASSERTION = "FACTUAL_ASSERTION"
    UNCERTAIN_BORDERLINE = "UNCERTAIN_BORDERLINE"
    QUESTION = "QUESTION"
    OPINION = "OPINION"
    CASUAL_COMMENTARY = "CASUAL_COMMENTARY"
    TOO_SHORT = "TOO_SHORT"


# ---------- Regex Patterns ----------

# 1. Casual / Slang / Sarcasm
CASUAL_SLANG_PATTERN = re.compile(
    r"\b(?:"
    r"lmao|lol|rofl|omg|smh|fr\s+fr|tbh|idk|"
    r"haha+|hehe+|huhu+|hihi+|"
    r"charot|charing|char|eme|yarn|beh|mga\s+beh|accla|forda|forderson|awit|chismis\s+lang|"
    r"grabe\s+naman|nakakaloka|sana\s+ol|sana\s+all"
    r")\b",
    re.IGNORECASE,
)

# 2. Questions & Inquiries
QUESTION_STARTERS_PATTERN = re.compile(
    r"^(?:"
    # English starters
    r"who|what|where|when|why|how|which|whose|whom|"
    r"is|are|was|were|do|does|did|can|could|will|would|should|has|have|had|"
    # Tagalog starters
    r"sino|ano|saan|kailan|bakit|paano|alin|kanino|gaano|"
    r"totoo\s+ba|dapat\s+ba|meron\s+ba|mayroon\s+ba|pwede\s+ba|maaari\s+ba"
    r")\b",
    re.IGNORECASE,
)

EMBEDDED_QUESTION_PATTERN = re.compile(
    r"\b(?:"
    r"totoo\s+ba\s+na|is\s+it\s+true\s+that|pwede\s+bang|can\s+you\s+believe"
    r")\b",
    re.IGNORECASE,
)

# 3. Opinions & Subjective Value Judgments
OPINION_MARKERS_PATTERN = re.compile(
    r"\b(?:"
    # First-person belief markers
    r"i\s+think|i\s+feel|in\s+my\s+opinion|in\s+my\s+view|personally|i\s+believe|"
    r"it\s+seems\s+to\s+me|my\s+favorite|i\s+wish|i\s+hope|for\s+me|"
    r"sa\s+tingin\s+ko|sa\s+palagay\s+ko|para\s+sa\s+akin|para\s+sakin|naniniwala\s+ako|"
    r"sa\s+opinyon\s+ko|sa\s+pananaw\s+ko|paborito\s+ko|"
    # Subjective evaluative adjectives
    r"mas\s+masarap|mas\s+maganda|pinakamaganda|pinakamasarap|sobrang\s+pangit|"
    r"sobrang\s+ganda|nakakatakot\s+naman|nakakainis|nakakadismaya|dapat\s+lang|"
    r"is\s+better\s+than|the\s+best|the\s+worst|so\s+ugly|delicious|terrible|horrible|"
    r"wonderful|disgusting"
    r")\b",
    re.IGNORECASE,
)

# 4. Attributed / Borderline Markers (quotes, hearsay, unverified reports)
ATTRIBUTION_MARKERS_PATTERN = re.compile(
    r"\b(?:"
    r"claimed\s+that|alleged\s+that|allegedly|according\s+to|reportedly|quoted\s+saying|"
    r"ayon\s+kay|ayon\s+sa|sabi\s+ni|sabi\s+ng|sinabi\s+ni|sinabi\s+ng|umano|diumano|di-umano|"
    r"raw|daw"
    r")\b",
    re.IGNORECASE,
)

# 5. Factual Anchors: Named Entities, Institutions, Officials
NAMED_ENTITIES_PATTERN = re.compile(
    r"\b(?:"
    r"president|pangulong|pres\.|senator|senador|sen\.|secretary|kalihim|sec\.|"
    r"governor|gov\.|mayor|bise\s+presidente|vice\s+president|vp|"
    r"marcos|duterte|robredo|aquino|romualdez|escudero|padilla|tulfo|sotto|cayetano|hontiveros|"
    r"doh|deped|dswd|dotr|dpwh|dilg|dfa|dti|da|dole|doj|dnd|pnp|afp|comelec|"
    r"supreme\s+court|korte\s+suprema|congress|kongreso|senate|senado|house\s+of\s+representatives|"
    r"malacañang|malacanang|bsp|bir|boc|pagcor|philhealth|ltfrb|lto|mmda|neda|psa|namria|who|un|pco|"
    r"republic\s+act|ra\s+\d+|executive\s+order|eo\s+\d+|house\s+bill|senate\s+bill|constitution|batas"
    r")\b",
    re.IGNORECASE,
)

# 6. Factual Anchors: Numerical / Monetary / Statistical
METRICS_PATTERN = re.compile(
    r"(?:"
    r"[₱\$€¥]\s*[\d,]+(?:\.\d+)?|"
    r"\b\d+(?:\.\d+)?\s*(?:%|(?:percent|porsyento)\b)|"
    r"\b\d+(?:\.\d+)?\s*(?:billion|bilyon|million|milyon|trillion|trilyon|thousand|libo)\b"
    r")",
    re.IGNORECASE,
)

# 7. Factual Anchors: Temporal / Dates
TEMPORAL_PATTERN = re.compile(
    r"\b(?:"
    r"19\d\d|20[0-3]\d|"
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"enero|pebrero|marso|abril|mayo|hunyo|hulyo|agosto|setyembre|oktubre|nobyembre|disyembre|"
    r"noong|nitong|kahapon|kamakailan"
    r")\b",
    re.IGNORECASE,
)

# 8. Factual Anchors: Verifiable Action Predicates
VERIFIABLE_PREDICATES_PATTERN = re.compile(
    r"\b(?:"
    # English
    r"signed|approved|passed|enacted|declared|arrested|increased|decreased|"
    r"dropped|rose|announced|filed|issued|ordered|launched|confirmed|denied|"
    r"suspended|vetoed|recorded|"
    # Tagalog
    r"pinirmahan|inaprubahan|ipinasa|ipinatupad|nagdeklara|inaresto|nahuli|"
    r"tumaas|bumaba|inilabas|nag-anunsyo|kinumpirma|itinanggi|sinuspinde|nagsumite"
    r")\b",
    re.IGNORECASE,
)


def triage_claim(claim: str) -> dict:
    """
    Classify whether a claim is suitable for evidence retrieval and verification.

    Args:
        claim: Normalized claim string.

    Returns:
        dict:
            - is_verifiable (bool): Whether the claim should proceed to verification.
            - category (str): The classification category (TriageCategory).
            - reason (str): Human-readable explanation of why it was accepted or rejected.
    """
    text = claim.strip()
    words = text.split()

    # Rule 1: Too short / sentence fragment
    short_assertion = len(words) == 3 and bool(re.search(r"\b(?:is|are|was|were|ay)\b", text, re.I))
    if len(words) < 4 and not short_assertion:
        return {
            "is_verifiable": False,
            "category": TriageCategory.TOO_SHORT.value,
            "reason": "Text is too short to form a verifiable factual assertion (fewer than 4 words).",
        }

    # Rule 2: Casual commentary, sarcasm, or slang
    casual_match = CASUAL_SLANG_PATTERN.search(text)
    if casual_match:
        # Check if the whole sentence is casual banter
        has_factual_anchors = (
            bool(NAMED_ENTITIES_PATTERN.search(text))
            or bool(METRICS_PATTERN.search(text))
            or bool(VERIFIABLE_PREDICATES_PATTERN.search(text))
        )
        if not has_factual_anchors:
            return {
                "is_verifiable": False,
                "category": TriageCategory.CASUAL_COMMENTARY.value,
                "reason": f"Text contains informal commentary or slang marker: '{casual_match.group(0)}'.",
            }

    # Rule 3: Questions / Inquiries
    if text.endswith("?"):
        return {
            "is_verifiable": False,
            "category": TriageCategory.QUESTION.value,
            "reason": "Text is phrased as a question rather than a factual assertion.",
        }

    question_starter = QUESTION_STARTERS_PATTERN.search(text)
    embedded_question = EMBEDDED_QUESTION_PATTERN.search(text)
    if question_starter or embedded_question:
        # If it starts with question words and lacks clear declarative predicate
        if not VERIFIABLE_PREDICATES_PATTERN.search(text) or text.endswith("?"):
            marker = question_starter.group(0) if question_starter else embedded_question.group(0)
            return {
                "is_verifiable": False,
                "category": TriageCategory.QUESTION.value,
                "reason": f"Text begins with an interrogative inquiry: '{marker}'.",
            }

    # Rule 4: Subjective Opinion / Personal View
    opinion_match = OPINION_MARKERS_PATTERN.search(text)
    # A qualified factual event can still be checked; evaluative judgments cannot.
    qualified_fact = (
        opinion_match
        and bool(re.fullmatch(r"i\s+think|i\s+believe|sa\s+tingin\s+ko|naniniwala\s+ako", opinion_match.group(0), re.I))
        and bool(VERIFIABLE_PREDICATES_PATTERN.search(text))
        and bool(NAMED_ENTITIES_PATTERN.search(text))
        and bool(TEMPORAL_PATTERN.search(text) or METRICS_PATTERN.search(text))
        and len(list(OPINION_MARKERS_PATTERN.finditer(text))) == 1
    )
    if opinion_match and not qualified_fact:
        return {
            "is_verifiable": False,
            "category": TriageCategory.OPINION.value,
            "reason": f"Text expresses a personal opinion or value judgment: '{opinion_match.group(0)}'.",
        }

    # Rule 5: Check for Factual Anchors
    entities_match = NAMED_ENTITIES_PATTERN.search(text)
    metrics_match = METRICS_PATTERN.search(text)
    temporal_match = TEMPORAL_PATTERN.search(text)
    predicates_match = VERIFIABLE_PREDICATES_PATTERN.search(text)
    attribution_match = ATTRIBUTION_MARKERS_PATTERN.search(text)

    factual_score = sum([
        bool(entities_match),
        bool(metrics_match),
        bool(temporal_match),
        bool(predicates_match),
    ])

    # Rule 6: Attributed or Borderline Statement
    if (attribution_match or qualified_fact) and factual_score >= 1:
        return {
            "is_verifiable": True,
            "category": TriageCategory.UNCERTAIN_BORDERLINE.value,
            "reason": "Claim contains an attributed, qualified or reported assertion; proceeding with verification.",
        }

    # Rule 7: Clear Factual Assertion
    if factual_score >= 1 or short_assertion:
        matched_indicators = []
        if entities_match:
            matched_indicators.append(f"entity: '{entities_match.group(0)}'")
        if metrics_match:
            matched_indicators.append(f"metric: '{metrics_match.group(0)}'")
        if predicates_match:
            matched_indicators.append(f"action: '{predicates_match.group(0)}'")
        if temporal_match:
            matched_indicators.append(f"date/time: '{temporal_match.group(0)}'")

        return {
            "is_verifiable": True,
            "category": TriageCategory.FACTUAL_ASSERTION.value,
            "reason": f"Verifiable factual claim detected ({', '.join(matched_indicators)}).",
        }

    # Rule 8: Fallback
    # If the text has normal sentence length (>= 5 words) and declarative structure,
    # treat as borderline factual assertion so we don't accidentally drop valid claims
    if len(words) >= 5 and not text.endswith("?"):
        return {
            "is_verifiable": True,
            "category": TriageCategory.UNCERTAIN_BORDERLINE.value,
            "reason": "Declarative statement without strong opinion markers; proceeding as borderline claim.",
        }

    return {
        "is_verifiable": False,
        "category": TriageCategory.OPINION.value,
        "reason": "Text does not contain sufficient verifiable factual indicators.",
    }
