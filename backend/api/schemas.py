"""
Pydantic schemas for the UnFake API contract.

These models define the exact shape of requests and responses
exchanged between the browser extension and the backend.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------- Enums ----------

class InputType(str, Enum):
    """How the claim was captured by the extension."""
    TEXT = "text"
    IMAGE_OCR = "image_ocr"


class VerifyStatus(str, Enum):
    """Overall status of the verification request."""
    COMPLETED = "completed"
    TRIAGE_REJECTED = "triage_rejected"
    ERROR = "error"


class Verdict(str, Enum):
    """Verdict based on the available evidence."""
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    MIXED = "mixed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceRelevance(str, Enum):
    """How a piece of evidence relates to the claim."""
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    CONTEXTUAL = "contextual"


class EvidenceSourceType(str, Enum):
    """Where the evidence was retrieved from."""
    LOCAL_ARCHIVE = "local_archive"
    WEB_SEARCH = "web_search"


# ---------- Request ----------

class VerifyRequest(BaseModel):
    """Request body for POST /api/v1/verify."""
    claim: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The factual statement to verify.",
    )
    input_type: InputType = Field(
        ...,
        description="How the claim was captured (text selection or OCR).",
    )

    @field_validator("claim")
    @classmethod
    def claim_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Claim must not be empty or whitespace-only.")
        return stripped


# ---------- Response ----------

class EvidenceItem(BaseModel):
    """A single piece of retrieved evidence."""
    title: str
    source_url: str
    publisher: str
    published_date: Optional[str] = None
    snippet: str
    relevance: EvidenceRelevance
    source_type: EvidenceSourceType


class TriageResult(BaseModel):
    """Triage engine classification result."""
    is_verifiable: bool
    category: Optional[str] = None
    reason: str


class VerifyResponse(BaseModel):
    """Successful response from POST /api/v1/verify."""
    status: VerifyStatus
    verdict: Optional[Verdict] = None
    explanation: str
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Reserved for future use. Currently always null.",
    )
    triage: Optional[TriageResult] = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    original_claim: str
    processing_time_ms: int = Field(ge=0)


class ErrorResponse(BaseModel):
    """Error response body."""
    status: str = "error"
    error_code: str
    message: str
