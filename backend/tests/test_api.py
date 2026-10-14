"""
Tests for POST /api/v1/verify endpoint.

These tests verify the API contract, input validation,
and response structure — not the verification logic itself
(which is stubbed in Milestone 1).
"""

import pytest


class TestVerifyEndpoint:
    """Tests for the /api/v1/verify endpoint."""

    # ── Successful requests ──────────────────────────────────────────

    def test_verify_valid_text_claim(self, client):
        """A valid text claim should return a 200 with the correct structure."""
        response = client.post("/api/v1/verify", json={
            "claim": "The Philippines has over 7,000 islands.",
            "input_type": "text",
        })

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert data["status"] == "completed"
        assert data["verdict"] == "insufficient_evidence"
        assert "explanation" in data
        assert "[STUB]" in data["explanation"]
        assert data["original_claim"] == "The Philippines has over 7,000 islands."
        assert data["processing_time_ms"] >= 0
        assert isinstance(data["evidence"], list)

    def test_verify_valid_image_ocr_claim(self, client):
        """An image_ocr claim should also be accepted."""
        response = client.post("/api/v1/verify", json={
            "claim": "Text extracted from an image via OCR.",
            "input_type": "image_ocr",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_verify_returns_triage_result(self, client):
        """The response should include triage information."""
        response = client.post("/api/v1/verify", json={
            "claim": "President Marcos signed Republic Act 11954 in July 2023.",
            "input_type": "text",
        })

        data = response.json()
        assert "triage" in data
        assert data["triage"]["is_verifiable"] is True
        assert data["triage"]["category"] == "FACTUAL_ASSERTION"
        assert isinstance(data["triage"]["reason"], str)

    def test_verify_returns_evidence_list_for_factual_claim(self, client):
        """The response should include an evidence array for verifiable claims."""
        response = client.post("/api/v1/verify", json={
            "claim": "The Department of Health announced the hospital budget for 2024.",
            "input_type": "text",
        })

        data = response.json()
        assert isinstance(data["evidence"], list)
        assert len(data["evidence"]) >= 1

        evidence = data["evidence"][0]
        assert "title" in evidence
        assert "source_url" in evidence
        assert "publisher" in evidence
        assert "snippet" in evidence
        assert "relevance" in evidence
        assert "source_type" in evidence

    def test_verify_rejects_opinion_with_triage_status(self, client):
        """Subjective opinions should return status: triage_rejected with verdict: None."""
        response = client.post("/api/v1/verify", json={
            "claim": "In my opinion, adobo is the best dish in the Philippines.",
            "input_type": "text",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triage_rejected"
        assert data["verdict"] is None
        assert data["evidence"] == []
        assert data["triage"]["is_verifiable"] is False
        assert data["triage"]["category"] == "OPINION"
        assert "opinion" in data["explanation"].lower()

    def test_verify_rejects_question_with_triage_status(self, client):
        """Questions should return status: triage_rejected."""
        response = client.post("/api/v1/verify", json={
            "claim": "Bakit ba ang mahal ng presyo ng sibuyas ngayon?",
            "input_type": "text",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triage_rejected"
        assert data["verdict"] is None
        assert data["triage"]["is_verifiable"] is False
        assert data["triage"]["category"] == "QUESTION"

    def test_verify_preserves_original_claim(self, client):
        """The response should echo back the original claim (stripped)."""
        claim = "  Marcos declared martial law in 1972.  "
        response = client.post("/api/v1/verify", json={
            "claim": claim,
            "input_type": "text",
        })

        data = response.json()
        assert data["original_claim"] == claim.strip()

    # ── Input validation errors ──────────────────────────────────────

    def test_verify_rejects_empty_claim(self, client):
        """An empty claim string should return 422."""
        response = client.post("/api/v1/verify", json={
            "claim": "",
            "input_type": "text",
        })

        assert response.status_code == 422

    def test_verify_rejects_whitespace_only_claim(self, client):
        """A whitespace-only claim should return 422."""
        response = client.post("/api/v1/verify", json={
            "claim": "   \n\t  ",
            "input_type": "text",
        })

        assert response.status_code == 422

    def test_verify_rejects_missing_claim(self, client):
        """A request without a claim field should return 422."""
        response = client.post("/api/v1/verify", json={
            "input_type": "text",
        })

        assert response.status_code == 422

    def test_verify_rejects_missing_input_type(self, client):
        """A request without an input_type should return 422."""
        response = client.post("/api/v1/verify", json={
            "claim": "Some claim.",
        })

        assert response.status_code == 422

    def test_verify_rejects_invalid_input_type(self, client):
        """An unrecognized input_type should return 422."""
        response = client.post("/api/v1/verify", json={
            "claim": "Some claim.",
            "input_type": "video",
        })

        assert response.status_code == 422

    def test_verify_rejects_claim_too_long(self, client):
        """A claim exceeding 5000 characters should return 422."""
        long_claim = "x" * 5001
        response = client.post("/api/v1/verify", json={
            "claim": long_claim,
            "input_type": "text",
        })

        assert response.status_code == 422

    def test_verify_accepts_claim_at_max_length(self, client):
        """A claim of exactly 5000 characters should be accepted."""
        max_claim = "x" * 5000
        response = client.post("/api/v1/verify", json={
            "claim": max_claim,
            "input_type": "text",
        })

        assert response.status_code == 200

    # ── Edge cases ───────────────────────────────────────────────────

    def test_verify_handles_unicode(self, client):
        """Unicode text (Filipino/Tagalog) should be accepted."""
        response = client.post("/api/v1/verify", json={
            "claim": "Ang Pilipinas ay may mahigit 7,000 na mga isla.",
            "input_type": "text",
        })

        assert response.status_code == 200
        data = response.json()
        assert "Pilipinas" in data["original_claim"]

    def test_verify_handles_special_characters(self, client):
        """Claims with special characters should be accepted."""
        response = client.post("/api/v1/verify", json={
            "claim": 'He said: "The budget is ₱3.5 billion" — fact or fiction?',
            "input_type": "text",
        })

        assert response.status_code == 200


class TestHealthCheck:
    """Tests for the root health check endpoint."""

    def test_root_returns_status(self, client):
        """The root endpoint should confirm the service is running."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["service"] == "unfake-api"
