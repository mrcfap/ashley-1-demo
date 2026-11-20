import json
import pytest
from app.evolution.evolution_cycle import run_cycle

def test_generates_review_without_code_changes(tmp_path):
    source = tmp_path / 'metrics.json'
    source.write_text(json.dumps({'vision_latency_ms': 1800, 'language_mismatch_rate': 0.2, 'memory_recall_rate': 0.5}), encoding='utf-8')
    result = run_cycle(tmp_path, source)
    assert len(result['proposals']) == 3
    assert result['applied_changes'] == 0
    assert len(list((tmp_path / '.ashley_evolution_reviews').glob('*.json'))) == 3

def test_no_proposals_for_healthy_metrics(tmp_path):
    source = tmp_path / 'metrics.json'
    source.write_text(json.dumps({'vision_latency_ms': 200, 'language_mismatch_rate': 0, 'memory_recall_rate': 1}), encoding='utf-8')
    assert run_cycle(tmp_path, source)['proposals'] == []

def test_rejects_invalid_metrics(tmp_path):
    source = tmp_path / 'metrics.json'
    source.write_text('{"vision_latency_ms": true}', encoding='utf-8')
    with pytest.raises(ValueError):
        run_cycle(tmp_path, source)
