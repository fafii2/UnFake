"""
API route definitions.

All routes are mounted under /api/v1 by main.py.
"""

import time
import asyncio
import uuid

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
from scripts.check_providers import check as check_providers

router = APIRouter()
_readiness = None
_readiness_lock = asyncio.Lock()
_jobs = {}
_job_tasks = set()


@router.post('/verifications', status_code=202)
async def start_verification(request: VerifyRequest):
    """Keep browser requests short while live providers finish asynchronously."""
    now = time.monotonic()
    for key, job in list(_jobs.items()):
        if now - job['created'] > 600 and job['status'] != 'pending':
            del _jobs[key]
    if len(_jobs) >= 32:
        finished = [key for key, job in _jobs.items() if job['status'] != 'pending']
        if finished:
            del _jobs[finished[0]]
        else:
            raise HTTPException(status_code=429, detail='UnFake is busy. Please try again shortly.')
    identifier = uuid.uuid4().hex
    _jobs[identifier] = {'status': 'pending', 'created': now}

    async def run():
        try:
            result = await _verify_claim(request, timeout=75)
            _jobs[identifier].update(status='completed', result=result.model_dump(mode='json'))
        except HTTPException as exc:
            _jobs[identifier].update(status='error', error=str(exc.detail))
        except Exception:
            _jobs[identifier].update(status='error', error='Verification could not be completed. Please try again.')

    task = asyncio.create_task(run())
    _job_tasks.add(task)
    task.add_done_callback(_job_tasks.discard)
    return {'id': identifier, 'status': 'pending'}


@router.get('/verifications/{identifier}')
async def verification_status(identifier: str):
    job = _jobs.get(identifier)
    if not job or time.monotonic() - job['created'] > 600:
        raise HTTPException(status_code=404, detail='This verification expired or the backend restarted. Please try again.')
    return {'id': identifier, **{key: value for key, value in job.items() if key != 'created'}}


@router.get('/health')
async def health():
    return {'service': 'unfake-api', 'version': '0.4.1', 'status': 'running',
            'live_search_configured': bool(settings.SEARCH_API_KEY),
            'evaluation_configured': bool(settings.GEMINI_API_KEY),
            'evaluation_model': settings.LLM_MODEL if settings.GEMINI_API_KEY else None,
            'embedding_provider': settings.EMBEDDING_PROVIDER,
            'live_check': _readiness}


@router.post('/readiness')
async def readiness():
    """Explicitly test live providers; reuse the result for five minutes."""
    global _readiness
    async with _readiness_lock:
        if _readiness and time.time() - _readiness['checked_at'] < 300:
            return _readiness
        checks = await check_providers()
        _readiness = {
            'ready': all(item['status'] == 'ok' for item in checks.values()),
            'checked_at': time.time(), 'checks': checks,
        }
        return _readiness


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
    return await _verify_claim(request, timeout=settings.VERIFY_TIMEOUT_SECONDS)


async def _verify_claim(request: VerifyRequest, timeout: float) -> VerifyResponse:
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
        return await asyncio.wait_for(run_pipeline(), timeout=timeout)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail='Verification timed out. Please try again.')
