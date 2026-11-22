import asyncio
from unittest.mock import AsyncMock
import httpx
import pytest
from config import settings
from scripts import check_providers
from services import evaluator


def test_unconfigured_checks_do_not_make_provider_requests(monkeypatch):
    call = AsyncMock(side_effect=AssertionError('Must not call a provider without credentials'))
    monkeypatch.setattr(check_providers, 'web_search', call)
    monkeypatch.setattr(check_providers, 'model_assessment', call)
    result = asyncio.run(check_providers.check())
    assert result['search']['status'] == 'not_configured'
    assert result['evaluation']['status'] == 'not_configured'
    call.assert_not_called()


def test_failed_check_never_exposes_provider_error_body(monkeypatch):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'private-key')
    request = httpx.Request('POST', 'https://example.test')
    response = httpx.Response(401, request=request, text='private-key and private provider diagnostics')
    error = httpx.HTTPStatusError('private-key', request=request, response=response)
    monkeypatch.setattr(check_providers, 'model_assessment', AsyncMock(side_effect=error))
    result = asyncio.run(check_providers.check('evaluation'))
    assert result['evaluation']['http_status'] == 401
    assert 'private-key' not in str(result)
    assert 'provider diagnostics' not in str(result)


@pytest.mark.parametrize('status, phrase', [(401, 'credentials'), (429, 'quota'), (404, 'model')])
def test_evaluation_failure_preserves_evidence_and_explains_configuration(monkeypatch, status, phrase):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'private-key')
    request = httpx.Request('POST', 'https://example.test')
    response = httpx.Response(status, request=request, text='private-key')
    error = httpx.HTTPStatusError('private-key', request=request, response=response)
    monkeypatch.setattr(evaluator, 'model_assessment', AsyncMock(side_effect=error))
    evidence = [{'id': 'S1', 'snippet': 'Evidence remains visible.'}]
    result = asyncio.run(evaluator.evaluate_claim('claim', evidence))
    assert result['verdict'] == 'insufficient_evidence'
    assert result['evidence'] == evidence
    assert phrase in result['warnings'][0]
    assert 'private-key' not in str(result)
