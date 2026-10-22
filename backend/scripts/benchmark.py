"""Measure labeled claim outcomes and latency; smoke fixtures are not thesis results."""
import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path
import httpx
from main import app
from config import settings


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered)-1, int((len(ordered)-1)*fraction))] if ordered else None


async def run(dataset: Path, output: Path, live=False):
    if not live:
        settings.SEARCH_API_KEY = None
        settings.GEMINI_API_KEY = None
        settings.EMBEDDING_PROVIDER = 'none'
    cases = [json.loads(line) for line in dataset.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not cases:
        raise ValueError('Dataset is empty')
    results, latencies, tp, fp, fn, correct, verdict_count = [], [], 0, 0, 0, 0, 0
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://benchmark') as client:
        for case in cases:
            started = time.perf_counter()
            response = await client.post('/api/v1/verify', json={'claim':case['claim'], 'input_type':case.get('input_type','text')})
            elapsed = (time.perf_counter()-started)*1000
            latencies.append(elapsed)
            body = response.json()
            accepted = body.get('triage',{}).get('is_verifiable',False)
            expected = case['expected_verifiable']
            tp += int(accepted and expected)
            fp += int(accepted and not expected)
            fn += int(not accepted and expected)
            if 'expected_verdict' in case:
                verdict_count += 1
                correct += int(body.get('verdict') == case['expected_verdict'])
            relevant = set(case.get('relevant_urls',[]))
            retrieved = {item['source_url'] for item in body.get('evidence',[])}
            results.append({'id':case['id'], 'http_status':response.status_code, 'elapsed_ms':round(elapsed,3),
                'verifiable':accepted, 'verdict':body.get('verdict'), 'timings':body.get('timings',{}),
                'retrieval_recall':len(relevant & retrieved)/len(relevant) if relevant else None,
                'warnings':body.get('warnings',[])})
    artifact = {'dataset':str(dataset), 'mode':'live' if live else 'offline', 'case_count':len(cases),
        'notice':'Development measurements only; a representative held-out dataset and participant study are required for thesis conclusions.',
        'triage_precision':tp/(tp+fp) if tp+fp else None, 'triage_recall':tp/(tp+fn) if tp+fn else None,
        'verdict_accuracy':correct/verdict_count if verdict_count else None,
        'latency_ms':{'median':statistics.median(latencies),'p95':percentile(latencies,0.95)}, 'results':results}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2), encoding='utf-8')
    print(json.dumps({key:value for key,value in artifact.items() if key != 'results'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--live',action='store_true',help='Use configured providers; may incur their normal charges')
    args = parser.parse_args()
    asyncio.run(run(args.dataset,args.output,args.live))
