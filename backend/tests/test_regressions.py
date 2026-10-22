import pytest
from services.preprocessor import normalize_claim
from services.triage import triage_claim


@pytest.mark.parametrize('claim', ['Updated population figures were released.', 'Alertness during storms saves lives.', 'Updates on the budget are pending.'])
def test_normalizer_preserves_complete_words(claim):
    assert normalize_claim(claim) == claim


def test_remove_only_whole_ui_lines():
    assert normalize_claim('Like\n[12:45 PM]\nMarcos signed a law in 2023.\nShare') == 'Marcos signed a law in 2023.'
    assert normalize_claim('Share prices rose at 12:45 PM.') == 'Share prices rose at 12:45 PM.'


@pytest.mark.parametrize('claim', ['The rate is 5%.', 'Earth is round.', 'I think Marcos signed the law in 2023.'])
def test_checkable_short_and_qualified_claims(claim):
    assert triage_claim(claim)['is_verifiable']


def test_health_endpoint_and_validation_contract(client):
    assert client.get('/api/v1/health').json()['version'] == '0.4.0'
    result = client.post('/api/v1/verify', json={'claim': '', 'input_type': 'text'})
    assert result.status_code == 422
    assert result.json()['error_code'] == 'EMPTY_CLAIM'


def test_triage_never_retrieves(client, monkeypatch):
    async def fail(*args):
        raise AssertionError('Non-factual input reached retrieval')
    monkeypatch.setattr('api.router.retrieve_evidence', fail)
    response = client.post('/api/v1/verify', json={'claim': 'Sa tingin ko mas masarap ang adobo.', 'input_type': 'text'})
    assert response.json()['status'] == 'triage_rejected'


def test_pipeline_deadline(client, monkeypatch):
    import asyncio
    from config import settings
    async def slow(*args):
        await asyncio.sleep(1)
    monkeypatch.setattr(settings, 'VERIFY_TIMEOUT_SECONDS', 0.01)
    monkeypatch.setattr('api.router.retrieve_evidence', slow)
    response = client.post('/api/v1/verify', json={'claim': 'The BSP stores gold in Manila.', 'input_type': 'text'})
    assert response.status_code == 504
    assert response.json()['error_code'] == 'PROCESSING_TIMEOUT'
