import asyncio
import json
import httpx
from config import settings
from services import embeddings


def test_disabled_embeddings_do_not_call_external_services():
    assert asyncio.run(embeddings.embed_text('claim')) is None


def test_gemini_embedding_request_and_task_type(monkeypatch):
    monkeypatch.setattr(settings, 'EMBEDDING_PROVIDER', 'gemini')
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'fake')
    def respond(request):
        assert json.loads(request.content)['taskType'] == 'RETRIEVAL_DOCUMENT'
        return httpx.Response(200, json={'embedding': {'values': [0.2, 0.7]}})
    factory = httpx.AsyncClient
    monkeypatch.setattr(embeddings.httpx, 'AsyncClient', lambda **kwargs: factory(transport=httpx.MockTransport(respond), **kwargs))
    assert asyncio.run(embeddings.embed_text('claim', query=False)) == [0.2, 0.7]
