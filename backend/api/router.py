"""
API route definitions.

All routes are mounted under /api/v1 by main.py.
"""

import time

from fastapi import APIRouter, HTTPException

from api.schemas import (
    ErrorResponse,
    EvidenceItem,
    EvidenceRelevance,
    EvidenceSourceType,
    InputType,
    TriageResult,
    Verdict,
    VerifyRequest,
    VerifyResponse,
    VerifyStatus,
)
from services.preprocessor import normalize_claim
from services.triage import triage_claim

router = APIRouter()


@router.post(
    "/verify",
    response_model=VerifyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        504: {"model": ErrorResponse, "description": "Processing timeout"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
    summary="Verify a claim",
    description="Submit a factual claim for evidence-based verification.",
)
async def verify_claim(request: VerifyRequest) -> VerifyResponse:
    """
    Verify a factual claim against available evidence.

    Pipeline:
      1. Preprocess & normalize raw claim text
      2. Triage claim: filter out opinions, questions, casual slang
      3. If non-verifiable: return immediately (status: triage_rejected)
      4. If verifiable: coordinate evidence retrieval & RAG evaluation
    """
    start_time = time.time()

    # ── Step 1: Preprocessing & Normalization ────────────────────────
    normalized = normalize_claim(request.claim)
    if not normalized:
        raise HTTPException(
            status_code=422,
            detail="Claim text contains only formatting noise or invalid characters.",
        )

    # ── Step 2: Rule-Based Claim Triage ──────────────────────────────
    triage_result = triage_claim(normalized)

    # ── Step 3: Early Exit if Non-Verifiable ──────────────────────────
    if not triage_result["is_verifiable"]:
        processing_time = int((time.time() - start_time) * 1000)
        return VerifyResponse(
            status=VerifyStatus.TRIAGE_REJECTED,
            verdict=None,
            explanation=(
                f"This text was not submitted for verification because it appears to be a "
                f"{triage_result['category'].replace('_', ' ').lower()} rather than an empirical factual claim. "
                f"{triage_result['reason']}"
            ),
            confidence=None,
            triage=TriageResult(
                is_verifiable=False,
                category=triage_result["category"],
                reason=triage_result["reason"],
            ),
            evidence=[],
            original_claim=request.claim,
            processing_time_ms=processing_time,
        )

    # ── Step 4: Verification Pipeline (M4/M5 stub) ───────────────────
    processing_time = int((time.time() - start_time) * 1000)

    return VerifyResponse(
        status=VerifyStatus.COMPLETED,
        verdict=Verdict.INSUFFICIENT_EVIDENCE,
        explanation=(
            "[STUB] This claim passed triage and was accepted for verification. "
            f"Triage category: {triage_result['category']}. "
            "Evidence retrieval and RAG evaluation will be integrated in Milestones 4 and 5."
        ),
        confidence=None,
        triage=TriageResult(
            is_verifiable=True,
            category=triage_result["category"],
            reason=triage_result["reason"],
        ),
        evidence=[
            EvidenceItem(
                title="[STUB] Example fact-check article",
                source_url="https://example.com/fact-check",
                publisher="Example Publisher",
                published_date="2025-01-01",
                snippet=(
                    "This is an example evidence snippet. In the real system, "
                    "this would contain a relevant excerpt from a fact-checking "
                    "article or news source."
                ),
                relevance=EvidenceRelevance.CONTEXTUAL,
                source_type=EvidenceSourceType.LOCAL_ARCHIVE,
            )
        ],
        original_claim=request.claim,
        processing_time_ms=processing_time,
    )
