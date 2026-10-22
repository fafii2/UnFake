"""Compute OCR CER/WER grouped by resolution from recorded recognition runs."""
import argparse
import json
from pathlib import Path


def distance(a, b):
    previous = list(range(len(b)+1))
    for i, left in enumerate(a, 1):
        current = [i]
        for j, right in enumerate(b, 1):
            current.append(min(current[-1]+1, previous[j]+1, previous[j-1]+(left != right)))
        previous = current
    return previous[-1]


def measure(rows):
    groups = {}
    for row in rows:
        reference, hypothesis = row['reference'], row['hypothesis']
        if not reference:
            raise ValueError('OCR references must be nonempty')
        group = groups.setdefault(str(row['resolution']), {'samples':0,'characters':0,'words':0,'character_errors':0,'word_errors':0})
        group['samples'] += 1
        group['characters'] += len(reference)
        group['words'] += len(reference.split())
        group['character_errors'] += distance(reference,hypothesis)
        group['word_errors'] += distance(reference.split(),hypothesis.split())
    return {key:{**group,'cer':group['character_errors']/group['characters'],
                 'wer':group['word_errors']/max(1,group['words'])} for key,group in groups.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.runs.read_text(encoding='utf-8').splitlines() if line.strip()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(measure(rows),indent=2),encoding='utf-8')
