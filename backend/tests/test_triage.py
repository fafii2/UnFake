"""
Tests for the rule-based triage engine.

Currently tests only the stub behavior. Real triage tests
will be added in Milestone 2 alongside the implementation.
"""

from services.triage import triage_claim


class TestTriageClaim:
    """Tests for the triage_claim function."""

    def test_stub_accepts_all_claims(self):
        """Stub implementation should mark all claims as verifiable."""
        result = triage_claim("The Earth is round.")
        assert result["is_verifiable"] is True

    def test_stub_returns_reason(self):
        """Stub implementation should return a reason string."""
        result = triage_claim("Any claim at all.")
        assert isinstance(result["reason"], str)
        assert "[STUB]" in result["reason"]
