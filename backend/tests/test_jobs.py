import asyncio
import time
from unittest.mock import AsyncMock

from api import router
from api.schemas import VerifyResponse, VerifyStatus, Verdict


def test_job_survives_between_short_browser_requests(client, monkeypatch):
    monkeypatch.setattr(router, '_jobs', {})

    async def finish(request, timeout):
        assert timeout == 75
        await asyncio.sleep(0.03)
        return VerifyResponse(status=VerifyStatus.COMPLETED, verdict=Verdict.SUPPORTED,
                              explanation='A source supports the claim.', original_claim=request.claim,
                              processing_time_ms=30)

    monkeypatch.setattr(router, '_verify_claim', finish)
    with client:
        response = client.post('/api/v1/verifications', json={'claim': 'A factual claim exists.', 'input_type': 'text'})
        assert response.status_code == 202
        job = response.json()
        assert job['status'] == 'pending'
        for _ in range(100):
            result = client.get('/api/v1/verifications/' + job['id']).json()
            if result['status'] != 'pending':
                break
            time.sleep(0.01)
        assert result['status'] == 'completed'
        assert result['result']['original_claim'] == 'A factual claim exists.'
        assert result['result']['verdict'] == 'supported'


def test_invalid_job_requests_never_start_provider_work(client, monkeypatch):
    verify = AsyncMock()
    monkeypatch.setattr(router, '_verify_claim', verify)
    assert client.post('/api/v1/verifications', json={'claim': '', 'input_type': 'text'}).status_code == 422
    verify.assert_not_called()
    assert client.get('/api/v1/verifications/not-a-job').status_code == 404


def test_jobs_are_bounded_while_providers_are_busy(client, monkeypatch):
    monkeypatch.setattr(router, '_jobs', {str(i): {'status': 'pending', 'created': time.monotonic()} for i in range(32)})
    response = client.post('/api/v1/verifications', json={'claim': 'A factual claim exists.', 'input_type': 'text'})
    assert response.status_code == 429


def test_completed_jobs_expire(client, monkeypatch):
    monkeypatch.setattr(router, '_jobs', {'old': {'status': 'completed', 'created': time.monotonic() - 601}})
    assert client.get('/api/v1/verifications/old').status_code == 404
