import asyncio
import json
from unittest.mock import AsyncMock

import httpx
import pytest

from services import evaluator


@pytest.mark.parametrize('status, expected_calls', [(503, 2), (401, 1), (429, 1)])
def test_only_temporary_provider_failures_are_retried(monkeypatch, status, expected_calls):
    monkeypatch.setattr(evaluator.settings, 'GEMINI_API_KEY', 'test-only-key')
    calls = []
    assessment = {'verdict': 'insufficient_evidence', 'explanation': 'The evidence does not establish the claim.',
                  'raw_confidence': 0.5, 'citations': []}

    def handle(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(status, json={'error': 'Provider failure'})
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': json.dumps(assessment)}]}}]})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(evaluator.httpx, 'AsyncClient', lambda **kwargs: original_client(
        transport=httpx.MockTransport(handle), **kwargs))
    monkeypatch.setattr(evaluator.asyncio, 'sleep', AsyncMock())
    if status == 503:
        assert asyncio.run(evaluator.model_assessment('claim', [])).verdict.value == 'insufficient_evidence'
    else:
        with pytest.raises(httpx.HTTPStatusError):
            asyncio.run(evaluator.model_assessment('claim', []))
    assert len(calls) == expected_calls
