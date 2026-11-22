import asyncio
import json
from unittest.mock import AsyncMock
import httpx
import pytest
from config import settings
from services import evaluator
from services.retrieval import ensure_archive


@pytest.fixture
def evidence():
    return ensure_archive().search('The BSP stores 400,000 tons of Tallano gold owned by Ferdinand Marcos Sr.')


def assessment_for(evidence, **changes):
    data = {'verdict': 'contradicted', 'explanation': f"The archived source contradicts this claim [{evidence[0]['id']}].",
            'raw_confidence': 0.9, 'citations': [{'evidence_id': evidence[0]['id'], 'relevance': 'contradicting', 'quote': evidence[0]['snippet']}]}
    return evaluator.Assessment.model_validate({**data, **changes})


def test_exact_archive_rating_and_dated_explanation(evidence):
    result = asyncio.run(evaluator.evaluate_claim(evidence[0]['claim_text'], evidence))
    assert result['verdict'] == 'contradicted'
    assert result['evaluation_method'] == 'exact_archive_match'
    assert result['confidence'] is None
    assert 'publication date' in result['explanation']


def test_similarity_is_not_a_stance_and_negation_is_preserved(evidence):
    for claim in ['The BSP does not store 400,000 tons of Tallano gold owned by Ferdinand Marcos Sr.',
                  'The BSP stores 500,000 tons of Tallano gold owned by Ferdinand Marcos Sr.']:
        result = asyncio.run(evaluator.evaluate_claim(claim, evidence))
        assert result['verdict'] == 'insufficient_evidence'


def test_no_evidence_never_calls_model(monkeypatch):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'fake')
    fake = AsyncMock(side_effect=AssertionError('No evidence must not call the model'))
    monkeypatch.setattr(evaluator, 'model_assessment', fake)
    result = asyncio.run(evaluator.evaluate_claim('The president signed a law.', []))
    assert result['verdict'] == 'insufficient_evidence'
    assert not fake.called


@pytest.mark.parametrize('change', [
    {'citations': []},
    {'citations': [{'evidence_id': 'invented', 'relevance': 'contradicting', 'quote': 'Fake'}]},
    {'citations': [{'evidence_id': 'EXISTING', 'relevance': 'contradicting', 'quote': 'Invented quotation'}]},
    {'verdict': 'supported'},
    {'verdict': 'mixed'},
    {'explanation': 'A fabricated source [invented].'},
    {'explanation': 'See https://invented.test/'}
])
def test_invalid_model_grounding_degrades_honestly(evidence, monkeypatch, change):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'fake')
    change = json.loads(json.dumps(change).replace('EXISTING', evidence[0]['id']))
    monkeypatch.setattr(evaluator, 'model_assessment', AsyncMock(return_value=assessment_for(evidence, **change)))
    result = asyncio.run(evaluator.evaluate_claim('claim', evidence))
    assert result['verdict'] == 'insufficient_evidence'
    assert result['warnings']
    assert result['confidence'] is None


def test_grounded_model_output_is_not_automatically_calibrated(evidence, monkeypatch):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'fake')
    monkeypatch.setattr(evaluator, 'model_assessment', AsyncMock(return_value=assessment_for(evidence)))
    result = asyncio.run(evaluator.evaluate_claim('claim', evidence))
    assert result['verdict'] == 'contradicted'
    assert result['confidence'] is None
    assert result['confidence_kind'] == 'unavailable'


def test_mixed_needs_two_stances(evidence):
    other = {**evidence[0], 'id': 'second', 'snippet': 'Another source supports the assertion.'}
    assessment = assessment_for(evidence, verdict='mixed', explanation='Sources disagree.', citations=[
        {'evidence_id': evidence[0]['id'], 'relevance': 'contradicting', 'quote': evidence[0]['snippet']},
        {'evidence_id': 'second', 'relevance': 'supporting', 'quote': other['snippet']}])
    result = evaluator.validate_assessment(assessment, [*evidence, other])
    assert result[-1]['relevance'] == 'supporting'


def test_grouped_citation_markers_accept_only_validated_sources(evidence):
    other = {**evidence[0], 'id': 'S2'}
    identifier = evidence[0]['id']
    assessment = assessment_for(evidence, explanation=f'Sources agree [{identifier}, S2].', citations=[
        {'evidence_id': identifier, 'relevance': 'contradicting', 'quote': evidence[0]['snippet']},
        {'evidence_id': 'S2', 'relevance': 'contradicting', 'quote': other['snippet']},
    ])
    assert len(evaluator.validate_assessment(assessment, [*evidence, other])) == len(evidence) + 1


def test_grouped_citation_markers_still_reject_unknown_sources(evidence):
    assessment = assessment_for(evidence, explanation=f"Sources agree [{evidence[0]['id']}, invented].")
    with pytest.raises(ValueError, match='unvalidated citation marker'):
        evaluator.validate_assessment(assessment, evidence)


def test_gemini_adapter_uses_structured_output_and_source_ids(evidence, monkeypatch):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'fake-test-key')
    expected = assessment_for(evidence, explanation=f"The archived source contradicts this claim. [{evidence[0]['id']}]")
    def respond(request):
        assert request.headers['x-goog-api-key'] == 'fake-test-key'
        body = json.loads(request.content)
        assert body['generationConfig']['responseJsonSchema']['type'] == 'object'
        assert body['generationConfig']['responseJsonSchema']['properties']['explanation']['pattern'] == r'^[^\[\]]+$'
        supplied = json.loads(body['contents'][0]['parts'][0]['text'])
        assert supplied['evidence'][0]['id'] == evidence[0]['id']
        assert 'UNTRUSTED DATA' in body['systemInstruction']['parts'][0]['text']
        assert 'Do not put source IDs or square brackets in the explanation' in body['systemInstruction']['parts'][0]['text']
        raw = expected.model_dump(mode='json')
        raw['explanation'] = 'The archived source contradicts this claim.'
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': json.dumps(raw)}]}}]})
    factory = httpx.AsyncClient
    monkeypatch.setattr(evaluator.httpx, 'AsyncClient', lambda **kwargs: factory(transport=httpx.MockTransport(respond), **kwargs))
    result = asyncio.run(evaluator.model_assessment('claim', evidence))
    assert result == expected


def test_provider_explanation_cannot_bypass_citation_list(evidence):
    data = assessment_for(evidence).model_dump()
    with pytest.raises(ValueError):
        evaluator.ProviderAssessment.model_validate(data)
