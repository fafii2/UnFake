"""Collect grounded Gemini predictions on independently labeled calibration claims."""
import argparse
import asyncio
import json
from pathlib import Path
from config import settings
from services.retrieval import retrieve_evidence
from services.evaluator import model_assessment, validate_assessment


async def run(dataset, output):
    if not settings.GEMINI_API_KEY:
        raise SystemExit('Configure GEMINI_API_KEY in backend/.env first.')
    rows = [json.loads(line) for line in dataset.read_text(encoding='utf-8').splitlines() if line.strip()]
    if any(row.get('split') != 'calibration' for row in rows):
        raise ValueError('Use a calibration-only dataset, separate from final evaluation claims.')
    predictions = []
    for row in rows:
        retrieved = await retrieve_evidence(row['claim'])
        if not retrieved['evidence']:
            continue
        assessment = await model_assessment(row['claim'], retrieved['evidence'])
        validate_assessment(assessment,retrieved['evidence'])
        predictions.append({'claim_id':row['id'],'split':'calibration','model':f'gemini:{settings.LLM_MODEL}',
            'raw_confidence':assessment.raw_confidence,'correct':assessment.verdict.value == row['expected_verdict']})
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(''.join(json.dumps(row)+'\n' for row in predictions),encoding='utf-8')
    print(f'Collected {len(predictions)} grounded calibration predictions.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    asyncio.run(run(args.dataset,args.output))
