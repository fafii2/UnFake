"""
API route definitions.

All routes are mounted under /api/v1 by main.py.
"""

import time
import asyncio

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
from services.retrieval import retrieve_evidence
from services.evaluator import evaluate_claim
from config import settings

router = APIRouter()


@router.get('/health')
async def health():
    return {'service': 'unfake-api', 'version': '0.4.0', 'status': 'running',
            'live_search_configured': bool(settings.SEARCH_API_KEY),
            'evaluation_configured': bool(settings.GEMINI_API_KEY),
            'embedding_provider': settings.EMBEDDING_PROVIDER}


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
    start_time = time.perf_counter()

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
        processing_time = int((time.perf_counter() - start_time) * 1000)
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

    timings = {'preprocess_triage_ms': round((time.perf_counter() - start_time) * 1000, 3)}

    async def run_pipeline():
        retrieved_at = time.perf_counter()
        retrieved = await retrieve_evidence(normalized)
        timings['retrieval_ms'] = round((time.perf_counter() - retrieved_at) * 1000, 3)
        evaluated_at = time.perf_counter()
        evaluated = await evaluate_claim(normalized, retrieved['evidence'])
        timings['evaluation_ms'] = round((time.perf_counter() - evaluated_at) * 1000, 3)
        return VerifyResponse(
            status=VerifyStatus.COMPLETED, verdict=evaluated['verdict'],
            explanation=evaluated['explanation'], confidence=evaluated['confidence'],
            confidence_kind=evaluated['confidence_kind'], evaluation_method=evaluated['evaluation_method'],
            triage=TriageResult(**triage_result),
            evidence=[EvidenceItem(**item) for item in evaluated['evidence']],
            warnings=retrieved['warnings'] + evaluated['warnings'], timings=timings,
            original_claim=request.claim,
            processing_time_ms=int((time.perf_counter() - start_time) * 1000))

    try:
        return await asyncio.wait_for(run_pipeline(), timeout=settings.VERIFY_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail='Verification timed out. Please try again.')
