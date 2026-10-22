import asyncio
import json
from unittest.mock import AsyncMock
import httpx
import pytest
from config import settings
from db.database import Archive, load_records
from services import retrieval


def test_import_is_idempotent_and_search_preserves_numbers(tmp_path):
    archive = Archive(tmp_path / 'archive.db')
    records = load_records(settings.ARCHIVE_SEED)
    assert archive.import_records(records) == 4
    archive.import_records(records)
    assert len(archive.records()) == 4
    assert archive.search(records[0].claim_text)[0]['match_method'] == 'exact'
    assert archive.search('The Philippines has over 7,000 islands.') == []
    assert archive.search('The hospital budget was announced in 2049.') == []
    assert archive.search(records[0].aliases[0])[0]['match_method'] == 'exact'


def test_vectors_are_model_bound_and_invalidate_on_content_change(tmp_path):
    archive = Archive(tmp_path / 'archive.db')
    records = load_records(settings.ARCHIVE_SEED)
    archive.import_records(records)
    identifier = archive.records()[0]['id']
    archive.set_vector(identifier, 'test-model', [1.0, 0.0])
    assert archive.search('unrelated wording', [1,0], 'test-model')[0]['match_method'] == 'vector'
    assert not archive.search('unrelated wording', [1,0], 'other-model')
    archive.import_records(records)
    assert next(row for row in archive.records() if row['id'] == identifier)['embedding'] is not None
    changed = next(record for record in records if record.claim_text == json.loads(next(row for row in archive.records() if row['id'] == identifier)['document'])['claim_text'])
    changed.snippet = 'A revised reviewed summary.'
    archive.import_records([changed])
    assert next(row for row in archive.records() if row['id'] == identifier)['embedding'] is None


def test_dual_streams_run_concurrently_and_deduplicate(monkeypatch):
    async def run():
        archive_started, web_started = asyncio.Event(), asyncio.Event()
        item = {'id': 'one', 'source_url': 'https://verafiles.org/a'}
        async def archive(claim):
            archive_started.set()
            await asyncio.wait_for(web_started.wait(), 0.5)
            return [item], []
        async def web(claim):
            web_started.set()
            await asyncio.wait_for(archive_started.wait(), 0.5)
            return [{**item, 'id': 'web-one'}], []
        monkeypatch.setattr(retrieval, 'archive_search', archive)
        monkeypatch.setattr(retrieval, 'web_search', web)
        result = await retrieval.retrieve_evidence('claim')
        assert len(result['evidence']) == 1
        assert result['warnings'] == []
    asyncio.run(run())


def test_provider_failure_retains_archive(monkeypatch):
    monkeypatch.setattr(retrieval, 'web_search', AsyncMock(side_effect=httpx.ReadTimeout('timeout')))
    result = asyncio.run(retrieval.retrieve_evidence('Tallano gold at BSP'))
    assert result['evidence']
    assert any('failed' in warning for warning in result['warnings'])


@pytest.mark.parametrize('url', ['javascript:alert(1)', 'https://verafiles.org.evil.test/a', 'https://user@verafiles.org/a', 'file:///etc/passwd'])
def test_source_allowlist_rejects_unsafe_urls(url):
    assert not retrieval.allowed_source(url)


def test_search_adapter_request_and_result_filtering(monkeypatch):
    monkeypatch.setattr(settings, 'SEARCH_API_KEY', 'fake-test-key')
    def respond(request):
        assert request.url == 'https://api.tavily.com/search'
        assert request.headers['Authorization'] == 'Bearer fake-test-key'
        assert json.loads(request.content)['include_answer'] is False
        return httpx.Response(200, json={'results': [
            {'url':'https://verafiles.org/articles/a', 'title':'Real result', 'content':'Retrieved text.'},
            {'url':'https://evil.test', 'content':'Untrusted domain'},
        ]})
    factory = httpx.AsyncClient
    monkeypatch.setattr(retrieval.httpx, 'AsyncClient', lambda **kwargs: factory(transport=httpx.MockTransport(respond), **kwargs))
    items, warnings = asyncio.run(retrieval.web_search('claim'))
    assert len(items) == 1 and items[0]['snippet'] == 'Retrieved text.'
    assert warnings == []
