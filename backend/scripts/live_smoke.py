"""Opt-in live checks. Uses configured search/model quota; never prints secrets.

Run from backend: python -m scripts.live_smoke --live
"""
import argparse
import asyncio
import json
from pathlib import Path

import httpx

CASES = [
    ('published_fact', 'The population of the Philippines was 112,729,484 as of July 1, 2024.', 'supported'),
    ('altered_number', 'The population of the Philippines was 12,729,484 as of July 1, 2024.', 'contradicted'),
    ('unverifiable', 'The fictional city of Lunavela opened its first underwater airport on March 14, 2026.', 'insufficient_evidence'),
]


async def main():
    results = []
    async with httpx.AsyncClient(timeout=35, trust_env=False) as client:
        for name, claim, expected in CASES:
            response = await client.post('http://127.0.0.1:8001/api/v1/verifications', json={'claim': claim, 'input_type': 'text'})
            data = response.json()
            if response.status_code == 202:
                identifier = data['id']
                for _ in range(90):
                    await asyncio.sleep(1)
                    response = await client.get('http://127.0.0.1:8001/api/v1/verifications/' + identifier)
                    data = response.json()
                    if data.get('status') != 'pending':
                        data = data.get('result', data)
                        break
            passed = response.status_code == 200 and data.get('verdict') == expected
            results.append({'case': name, 'expected': expected, 'passed': passed, 'http_status': response.status_code, 'result': data})
            print(json.dumps({'case': name, 'passed': passed, 'verdict': data.get('verdict'),
                              'sources': len(data.get('evidence', [])), 'elapsed_ms': data.get('processing_time_ms'),
                              'warnings': data.get('warnings', [])}), flush=True)
    output = Path(__file__).resolve().parents[2] / 'test-results' / 'live-api.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding='utf-8')
    return all(item['passed'] for item in results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Allow real provider requests')
    if not parser.parse_args().live:
        parser.error('--live is required because these checks consume provider quota')
    raise SystemExit(0 if asyncio.run(main()) else 1)
