"""Check configured live APIs without printing credentials or provider error bodies.

Run from backend: python -m scripts.check_providers
Uses one small model request and one live search when the keys are configured.
"""
import asyncio
import argparse
import json
import httpx
from config import settings
from services.evaluator import model_assessment, validate_assessment
from services.retrieval import web_search


async def check(provider='both'):
    result = {}
    async def search():
        if not settings.SEARCH_API_KEY:
            return {'status': 'not_configured'}
        try:
            items, _ = await web_search('BSP Tallano gold fact check')
            return {'status': 'ok', 'source_count': len(items)}
        except httpx.HTTPStatusError as exc:
            return {'status': 'http_error', 'http_status': exc.response.status_code}
        except httpx.RequestError as exc:
            return {'status': 'connection_error', 'error_type': type(exc).__name__}
        except (ImportError, ValueError, KeyError, TypeError) as exc:
            return {'status': 'configuration_error', 'error_type': type(exc).__name__}

    async def evaluation():
        if not settings.GEMINI_API_KEY:
            return {'status': 'not_configured', 'model': settings.LLM_MODEL}
        evidence = [{'id': 'S1', 'title': 'Synthetic API connection test',
                     'publisher': 'UnFake test fixture', 'published_date': '2026-01-01',
                     'snippet': 'In this synthetic test, the fictional counter is 12.'}]
        try:
            assessment = await model_assessment('In this synthetic test, the fictional counter is 12.', evidence)
            validate_assessment(assessment, evidence)
            return {'status': 'ok', 'model': settings.LLM_MODEL, 'verdict': assessment.verdict.value}
        except httpx.HTTPStatusError as exc:
            return {'status': 'http_error', 'http_status': exc.response.status_code, 'model': settings.LLM_MODEL}
        except httpx.RequestError as exc:
            return {'status': 'connection_error', 'error_type': type(exc).__name__, 'model': settings.LLM_MODEL}
        except (ImportError, ValueError, KeyError, IndexError, TypeError) as exc:
            return {'status': 'invalid_response', 'error_type': type(exc).__name__, 'model': settings.LLM_MODEL}

    if provider == 'both':
        result['search'], result['evaluation'] = await asyncio.gather(search(), evaluation())
    elif provider == 'search':
        result['search'] = await search()
    else:
        result['evaluation'] = await evaluation()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['both', 'search', 'evaluation'], default='both')
    parser.add_argument('--model', help='Test a different Gemini model without changing .env')
    args = parser.parse_args()
    if args.model:
        settings.LLM_MODEL = args.model
    outcome = asyncio.run(check(args.provider))
    print(json.dumps(outcome, indent=2))
    raise SystemExit(0 if all(item['status'] == 'ok' for item in outcome.values()) else 1)
