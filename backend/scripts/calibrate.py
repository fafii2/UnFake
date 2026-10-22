"""Fit an isotonic reliability mapping to labeled calibration-only predictions."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def fit(rows: list[dict], model: str) -> dict:
    if len(rows) < 30 or len({row['claim_id'] for row in rows}) != len(rows):
        raise ValueError('Need at least 30 uniquely identified calibration claims')
    if any(row.get('split') != 'calibration' or row.get('model') != model or type(row.get('correct')) is not bool
           or not isinstance(row.get('raw_confidence'), (int, float)) or not math.isfinite(row['raw_confidence'])
           or not 0 <= row['raw_confidence'] <= 1 for row in rows):
        raise ValueError('Rows must be labeled calibration-only predictions from the same model')
    if len({row['correct'] for row in rows}) < 2:
        raise ValueError('Both correct and incorrect predictions are required')
    grouped = {}
    for row in rows:
        total, count = grouped.get(row['raw_confidence'], (0, 0))
        grouped[row['raw_confidence']] = (total + int(row['correct']), count + 1)
    blocks = []
    for upper, (total, count) in sorted(grouped.items()):
        blocks.append({'upper': upper, 'total': total, 'count': count})
        while len(blocks) >= 2 and blocks[-2]['total']/blocks[-2]['count'] > blocks[-1]['total']/blocks[-1]['count']:
            right, left = blocks.pop(), blocks.pop()
            blocks.append({'upper': right['upper'], 'total': left['total']+right['total'], 'count': left['count']+right['count']})
    return {'model': model, 'sample_count': len(rows), 'method': 'isotonic',
            'dataset_sha256': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            'bins': [{'upper': b['upper'], 'reliability': b['total']/b['count'], 'count': b['count']} for b in blocks]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('predictions', type=Path)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', type=Path, default=Path('data/calibration.json'))
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.predictions.read_text(encoding='utf-8').splitlines() if line.strip()]
    artifact = fit(rows, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2), encoding='utf-8')
    print(f'Wrote calibration mapping for {artifact["sample_count"]} labeled claims')
