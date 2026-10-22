import json
from pathlib import Path
import pytest
from services.preprocessor import normalize_claim
from services.triage import triage_claim

CASES = json.loads((Path(__file__).resolve().parents[2] / 'tests/fixtures/claims.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', CASES)
def test_shared_browser_backend_claim_contract(case):
    normalized = normalize_claim(case['input'])
    assert normalized == case['normalized']
    assert triage_claim(normalized)['category'] == case['category']
