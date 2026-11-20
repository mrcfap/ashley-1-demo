import pytest
from app.axiom_v95_v100 import core, supervised

@pytest.fixture(autouse=True)
def temp_db(tmp_path,monkeypatch):
    monkeypatch.setattr(core,'DB_PATH',tmp_path/'test.db')

def test_deliberation_persistent_and_safe():
    m=core.mission('1',{'objective':'Investigar lentidão das respostas'})
    d=supervised.deliberate('1',m['id'],{'consent':True,'sources':[{'title':'Log','excerpt':'Resposta demorou 5s'}]})
    assert d['status']=='deliberated' and d['execution_authorized'] is False
    assert {'V98','V99'} <= {x['id'] for x in d['selected_engines']}
    assert d['deliberation']['mode']=='offline_rules'
    assert d['production_modified'] is False
    r=supervised.report('1',m['id'])
    assert r['last_deliberation']['id']==d['id']
    assert r['mission']['status']=='deliberated'
    assert r['mission']['execution_authorized'] is False

def test_isolation():
    m=core.mission('1',{'objective':'Investigar erro'})
    with pytest.raises(KeyError):supervised.deliberate('2',m['id'],{'consent':True})
    with pytest.raises(KeyError):supervised.report('2',m['id'])

def test_consent_and_limits():
    m=core.mission('1',{'objective':'Investigar erro'})
    with pytest.raises(ValueError):supervised.deliberate('1',m['id'],{})
    with pytest.raises(ValueError):supervised.deliberate('1',m['id'],{'consent':True,'sources':[{}]})
    assert core._get('1','mission',m['id'])['status']=='proposed'

def test_local_model_mock(monkeypatch):
    m=core.mission('1',{'objective':'Investigar erro'})
    monkeypatch.setattr(supervised,'_model_response',lambda role,objective,evidence,timeout:f'{role} análise simulada')
    d=supervised.deliberate('1',m['id'],{'consent':True,'use_local_model':True})
    assert d['deliberation']['roles_executed'] is True
    assert d['deliberation']['mode']=='local_ollama'

def test_local_model_fallback(monkeypatch):
    m=core.mission('1',{'objective':'Investigar erro'})
    def fail(*args):raise TimeoutError('timeout')
    monkeypatch.setattr(supervised,'_model_response',fail)
    d=supervised.deliberate('1',m['id'],{'consent':True,'use_local_model':True})
    assert d['deliberation']['mode']=='offline_rules_fallback'
    assert d['deliberation']['roles_executed'] is False
