"""Held-out empirical reliability mapping. No fabricated default confidence."""
import json
import math
from config import settings


def calibrated_confidence(score: float, model: str) -> float | None:
    try:
        artifact = json.loads(settings.CALIBRATION_PATH.read_text(encoding='utf-8'))
        if artifact['model'] != model or artifact['sample_count'] < 30 or not artifact['dataset_sha256']:
            return None
        bins = artifact['bins']
        if not bins or not all(0 <= b['upper'] <= 1 and 0 <= b['reliability'] <= 1 and b['count'] > 0 for b in bins):
            return None
        if sum(b['count'] for b in bins) != artifact['sample_count']:
            return None
        if any(a['upper'] >= b['upper'] or a['reliability'] > b['reliability'] for a,b in zip(bins,bins[1:])):
            return None
        if not math.isfinite(score) or not 0 <= score <= 1:
            return None
        return next((b['reliability'] for b in bins if score <= b['upper']), bins[-1]['reliability'])
    except (OSError, ValueError, KeyError, TypeError):
        return None
