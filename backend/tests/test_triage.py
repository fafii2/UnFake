"""
Comprehensive test suite for the rule-based claim triage engine.

Tests evaluate:
- Factual assertions (English, Tagalog, Taglish)
- Attributed / borderline assertions
- Subjective opinions and personal beliefs
- Inquiries and rhetorical questions
- Casual slang, memes, and sarcasm
- Too-short sentence fragments
"""

import pytest
from services.triage import TriageCategory, triage_claim


class TestTriageFactualAssertions:
    """Claims containing verifiable entities, metrics, dates, or actions."""

    @pytest.mark.parametrize(
        "claim",
        [
            "President Marcos signed Republic Act 11954 establishing the Maharlika Investment Fund.",
            "The Philippine inflation rate dropped to 3.3% in August 2024.",
            "DepEd announced the opening of classes for 24 million students.",
            "PNP arrested three suspects in Quezon City for illegal firearms.",
            "The Supreme Court declared the executive order unconstitutional.",
            "Inaprubahan ng DOH ang ₱15 billion budget para sa mga pampublikong ospital noong 2024.",
            "Tumaas ang presyo ng bigas sa Metro Manila nitong Setyembre.",
            "May 7,641 na mga pulo sa Pilipinas ayon sa opisyal na talaan ng NAMRIA.",
            "Naglabas ang Comelec ng resolusyon tungkol sa voter registration.",
            "Pinirmahan ng Pangulo ang bagong batas sa Malacañang kahapon.",
        ],
    )
    def test_verifiable_factual_claims_pass(self, claim):
        result = triage_claim(claim)
        assert result["is_verifiable"] is True
        assert result["category"] in [
            TriageCategory.FACTUAL_ASSERTION.value,
            TriageCategory.UNCERTAIN_BORDERLINE.value,
        ]
        assert isinstance(result["reason"], str)


class TestTriageAttributedBorderlineClaims:
    """Claims with attribution markers (quotes, hearsay, 'ayon kay', 'allegedly')."""

    @pytest.mark.parametrize(
        "claim",
        [
            "According to Senator Hontiveros, POGO hubs were involved in illegal operations.",
            "Sabi ni Mayor Lacuna bumaba raw ang insidente ng krimen sa Maynila noong 2024.",
            "PhilHealth reportedly increased dialysis benefits for members.",
            "Ayon sa ulat ng PSA, bumagal ang pagtaas ng presyo ng bilihin.",
        ],
    )
    def test_attributed_claims_pass_with_borderline_category(self, claim):
        result = triage_claim(claim)
        assert result["is_verifiable"] is True
        assert result["category"] == TriageCategory.UNCERTAIN_BORDERLINE.value
        assert "attributed" in result["reason"].lower() or "reported" in result["reason"].lower()


class TestTriageOpinions:
    """Subjective value judgments and personal perspectives."""

    @pytest.mark.parametrize(
        "claim",
        [
            "In my opinion, the government is not doing enough for small farmers.",
            "I think Boracay is the best island beach in the entire world.",
            "Personally, I feel that adobo is delicious and better than sinigang.",
            "Sa tingin ko mas masarap kumain sa karinderya kaysa sa mamahaling restaurant.",
            "Para sa akin, napakaganda ng Pilipinas pero mahirap ang buhay.",
            "Sobrang pangit ng bagong logo ng ahensya ng gobyerno.",
            "Naniniwala ako na mas mabait ang mga taga-probinsya kaysa sa siyudad.",
            "It seems to me that current traffic policies are terrible.",
        ],
    )
    def test_opinions_are_rejected(self, claim):
        result = triage_claim(claim)
        assert result["is_verifiable"] is False
        assert result["category"] == TriageCategory.OPINION.value
        assert "opinion" in result["reason"].lower() or "value judgment" in result["reason"].lower()


class TestTriageQuestions:
    """Questions, rhetorical inquiries, and interrogative sentences."""

    @pytest.mark.parametrize(
        "claim",
        [
            "Bakit ba ang mahal ng presyo ng sibuyas at gulay ngayon?",
            "Is it true that classes are suspended tomorrow in all levels?",
            "Kailan darating ang bagong ayuda mula sa tanggapan ng DSWD?",
            "Totoo ba na may bagong holiday sa susunod na Lunes?",
            "Who was appointed as the new secretary of the department?",
            "Ano ang dahilan kung bakit walang kuryente sa probinsya?",
        ],
    )
    def test_questions_are_rejected(self, claim):
        result = triage_claim(claim)
        assert result["is_verifiable"] is False
        assert result["category"] == TriageCategory.QUESTION.value
        assert "question" in result["reason"].lower() or "inquiry" in result["reason"].lower()


class TestTriageCasualSlangAndNoise:
    """Social media chatter, memes, sarcasm, and conversational filler."""

    @pytest.mark.parametrize(
        "claim",
        [
            "grabe naman yan haha charot lang mga beh",
            "fake news yarn lol lmao fr fr",
            "nakakaloka ang init ngayon beh grabe",
            "sana all mayaman eme lang yarn mga lods",
        ],
    )
    def test_casual_slang_rejected(self, claim):
        result = triage_claim(claim)
        assert result["is_verifiable"] is False
        assert result["category"] == TriageCategory.CASUAL_COMMENTARY.value
        assert "informal" in result["reason"].lower() or "slang" in result["reason"].lower()


class TestTriageTooShort:
    """Phrases that are too short to form verifiable claims."""

    @pytest.mark.parametrize(
        "claim",
        [
            "Fake news!",
            "Marcos out!",
            "Ayoko na talaga.",
            "Yes indeed.",
        ],
    )
    def test_too_short_rejected(self, claim):
        result = triage_claim(claim)
        assert result["is_verifiable"] is False
        assert result["category"] == TriageCategory.TOO_SHORT.value
        assert "too short" in result["reason"].lower()
