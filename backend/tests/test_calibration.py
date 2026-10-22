import json
import pytest
from config import settings
from scripts.calibrate import fit
from services.calibration import calibrated_confidence


def rows():
    return [{'claim_id': f'c{i}', 'split': 'calibration', 'model': 'test-model',
             'raw_confidence': i/30, 'correct': i % 4 != 0} for i in range(30)]


def test_fitted_calibration_is_monotonic_and_model_bound():
    artifact = fit(rows(), 'test-model')
    settings.CALIBRATION_PATH.write_text(json.dumps(artifact), encoding='utf-8')
    assert calibrated_confidence(0.8, 'test-model') is not None
    assert calibrated_confidence(0.8, 'different-model') is None
    assert all(a['reliability'] <= b['reliability'] for a,b in zip(artifact['bins'], artifact['bins'][1:]))


def test_no_calibration_artifact_means_no_confidence():
    assert calibrated_confidence(0.99, 'test-model') is None


@pytest.mark.parametrize('change', ['test_split', 'few', 'duplicates', 'single_class'])
def test_calibration_rejects_invalid_training_data(change):
    data = rows()
    if change == 'test_split': data[0]['split'] = 'test'
    if change == 'few': data = data[:10]
    if change == 'duplicates': data[1]['claim_id'] = data[0]['claim_id']
    if change == 'single_class':
        for row in data: row['correct'] = True
    with pytest.raises(ValueError): fit(data, 'test-model')
