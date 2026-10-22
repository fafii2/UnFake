"""Concurrent archive and live-search retrieval, with explicit partial failures."""
import asyncio
import hashlib
from urllib.parse import urlparse
import httpx
from config import settings
from db.database import Archive, load_records
from services.embeddings import embed_text, model_signature


def allowed_source(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    return parsed.scheme in {'http', 'https'} and not parsed.username and any(
        host == domain or host.endswith('.' + domain) for domain in settings.SEARCH_DOMAINS)


def ensure_archive() -> Archive:
    archive = Archive(settings.ARCHIVE_PATH)
    archive.initialize()
    if not archive.records() and settings.ARCHIVE_SEED.exists():
        archive.import_records(load_records(settings.ARCHIVE_SEED))
    return archive


async def archive_search(claim: str) -> tuple[list[dict], list[str]]:
    archive = await asyncio.to_thread(ensure_archive)
    notices, vector = [], None
    signature = model_signature()
    rows = await asyncio.to_thread(archive.records)
    has_vectors = any(row['embedding_model'] == signature and row['embedding'] for row in rows)
    if has_vectors:
        try:
            vector = await embed_text(claim)
        except (httpx.HTTPError, ValueError, KeyError, ImportError):
            notices.append('Semantic matching is unavailable; archive results use wording matches.')
    else:
        notices.append('Archive search currently uses wording matches; semantic matching has not been enabled.')
    return await asyncio.to_thread(archive.search, claim, vector, signature, settings.MAX_EVIDENCE), notices


async def web_search(claim: str) -> tuple[list[dict], list[str]]:
    if not settings.SEARCH_API_KEY:
        return [], ['Live search is not configured; only the local archive was searched.']
    async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
        response = await client.post('https://api.tavily.com/search',
            headers={'Authorization': f'Bearer {settings.SEARCH_API_KEY}'},
            json={'query': claim, 'max_results': 5, 'search_depth': 'basic',
                  'include_domains': settings.SEARCH_DOMAINS, 'include_answer': False, 'include_raw_content': False})
        response.raise_for_status()
        items = response.json().get('results', [])
    evidence = []
    for item in items:
        url = item.get('url', '')
        if not allowed_source(url) or not item.get('content'):
            continue
        evidence.append({'id': 'web-' + hashlib.sha256(url.encode()).hexdigest()[:16],
            'title': str(item.get('title') or url)[:500], 'source_url': url,
            'publisher': urlparse(url).hostname, 'published_date': item.get('published_date'),
            'snippet': str(item['content'])[:3500], 'source_type': 'web_search',
            'relevance': 'contextual', 'match_method': 'web'})
    return evidence, []


async def retrieve_evidence(claim: str) -> dict:
    results = await asyncio.gather(archive_search(claim), web_search(claim), return_exceptions=True)
    evidence, warnings, seen = [], [], set()
    for name, result in zip(('Archive search', 'Live search'), results):
        if isinstance(result, Exception):
            warnings.append(f'{name} failed; results from that source are unavailable.')
            continue
        items, notices = result
        warnings.extend(notices)
        for item in items:
            canonical = item['source_url'].rstrip('/').split('#')[0]
            if canonical not in seen:
                seen.add(canonical)
                evidence.append(item)
    selected = evidence[:settings.MAX_EVIDENCE]
    for index, item in enumerate(selected, 1):
        item['archive_id'] = item['id']
        item['id'] = f'S{index}'
    return {'evidence': selected, 'warnings': warnings}
