"""Embedding adapters. Cloud requests require configuration; local inference is optional."""
import asyncio
import math
from functools import lru_cache
import httpx
from config import settings


def model_signature() -> str:
    model = settings.LOCAL_EMBEDDING_MODEL if settings.EMBEDDING_PROVIDER == 'local' else settings.EMBEDDING_MODEL
    return f'{settings.EMBEDDING_PROVIDER}:{model}'


@lru_cache(maxsize=1)
def local_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)


async def embed_text(text: str, query: bool = True) -> list[float] | None:
    if settings.EMBEDDING_PROVIDER == 'none':
        return None
    if settings.EMBEDDING_PROVIDER == 'local':
        vector = await asyncio.to_thread(lambda: local_model().encode(text, normalize_embeddings=True).tolist())
    elif settings.EMBEDDING_PROVIDER == 'gemini' and settings.GEMINI_API_KEY:
        async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/{settings.EMBEDDING_MODEL}:embedContent',
                headers={'x-goog-api-key': settings.GEMINI_API_KEY},
                json={'content': {'parts': [{'text': text}]},
                      'taskType': 'RETRIEVAL_QUERY' if query else 'RETRIEVAL_DOCUMENT'})
            response.raise_for_status()
            vector = response.json()['embedding']['values']
    else:
        raise ValueError('Embedding provider is unavailable or not configured')
    if not vector or not all(isinstance(x, (float, int)) and math.isfinite(x) for x in vector):
        raise ValueError('Invalid embedding response')
    return vector
