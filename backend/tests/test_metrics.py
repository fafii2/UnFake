from scripts.evaluate_ocr import distance, measure


def test_ocr_edit_distance_and_aggregated_rates():
    assert distance('kitten','sitting') == 3
    result = measure([{'resolution':'1920x1080','reference':'the cat','hypothesis':'the bat'}])
    assert result['1920x1080']['cer'] == 1/7
    assert result['1920x1080']['wer'] == 1/2
