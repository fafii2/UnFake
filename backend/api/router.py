"""
API route definitions.

All routes are mounted under /api/v1 by main.py.
"""

import time

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

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

    Current implementation: returns a clearly-labeled STUB response
    to prove end-to-end communication between the extension and backend.
    Real verification logic will be added in Milestones 2–5.
    """
    start_time = time.time()

    # ── Stub response ────────────────────────────────────────────────
    # This is a placeholder. The real pipeline will be:
    #   1. Preprocess the claim
    #   2. Run triage (is it verifiable?)
    #   3. Retrieve evidence (local archive + web search)
    #   4. Evaluate evidence (RAG pipeline)
    #   5. Return verdict with citations
    #
    # The [STUB] prefix makes it obvious this is not a real result.
    # ─────────────────────────────────────────────────────────────────

    processing_time = int((time.time() - start_time) * 1000)

    return VerifyResponse(
        status=VerifyStatus.COMPLETED,
        verdict=Verdict.INSUFFICIENT_EVIDENCE,
        explanation=(
            "[STUB] This is a placeholder response from the UnFake backend. "
            "The verification pipeline is not yet implemented. "
            f"Your claim ({len(request.claim)} characters) was received "
            f"via {request.input_type.value} input and will be processed "
            "once the retrieval and evaluation services are built."
        ),
        confidence=None,
        triage=TriageResult(
            is_verifiable=True,
            reason="[STUB] Triage engine not yet implemented. All claims pass through.",
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
