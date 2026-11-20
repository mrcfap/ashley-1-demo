import pytest
from app.axiom_v95_v100 import specialists

def test_names_and_count():
    c = specialists.catalog()
    assert len(c['specialists']) == 5
    assert {s['name'] for s in c['specialists']} == {
        'AXYNTORA SENTINELA', 'AXYNTORA SINTONIA', 'AXYNTORA PRAXIS',
        'AXYNTORA VIGIA', 'AXYNTORA CRIVO'}
    assert not c['all_specialists_operational']

def test_no_execution():
    r = specialists.assess_request({'objective': 'Investigar lentidão'})
    assert not r['execution_authorized']
    assert not r['tools_executed']
    assert not r['production_modified']
    assert r['requires_human_approval']

def test_invalid_specialist():
    with pytest.raises(ValueError):
        specialists.assess_request({'objective': 'teste', 'specialists': ['inexistente']})

def test_invalid_objective():
    with pytest.raises(ValueError):
        specialists.assess_request({'objective': ''})

def test_duplicate_specialist():
    with pytest.raises(ValueError):
        specialists.assess_request({'objective': 'teste', 'specialists': ['crivo','crivo']})
