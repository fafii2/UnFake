from unittest.mock import AsyncMock

from api import router


def test_health_does_not_claim_live_readiness_from_configured_keys(client, monkeypatch):
    monkeypatch.setattr(router, '_readiness', None)
    monkeypatch.setattr(router.settings, 'SEARCH_API_KEY', 'configured')
    monkeypatch.setattr(router.settings, 'GEMINI_API_KEY', 'configured')
    result = client.get('/api/v1/health').json()
    assert result['live_search_configured'] is True
    assert result['live_check'] is None


def test_readiness_requires_both_providers_and_caches_requests(client, monkeypatch):
    monkeypatch.setattr(router, '_readiness', None)
    check = AsyncMock(return_value={'search': {'status': 'ok'}, 'evaluation': {'status': 'http_error', 'http_status': 429}})
    monkeypatch.setattr(router, 'check_providers', check)
    result = client.post('/api/v1/readiness').json()
    assert result['ready'] is False
    assert result['checks']['evaluation']['http_status'] == 429
    assert client.post('/api/v1/readiness').json() == result
    assert client.get('/api/v1/health').json()['live_check'] == result
    check.assert_awaited_once()


def test_readiness_reports_success_only_after_real_checks(client, monkeypatch):
    monkeypatch.setattr(router, '_readiness', None)
    monkeypatch.setattr(router, 'check_providers', AsyncMock(return_value={
        'search': {'status': 'ok'}, 'evaluation': {'status': 'ok'}}))
    assert client.post('/api/v1/readiness').json()['ready'] is True
