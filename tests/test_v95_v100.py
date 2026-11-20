import pytest
from app.axiom_v95_v100 import core

@pytest.fixture(autouse=True)
def temp_db(tmp_path,monkeypatch):
    monkeypatch.setattr(core,'DB_PATH',tmp_path/'test.db')

def test_catalog():
    assert [e['id'] for e in core.catalog()]==[f'V{i}' for i in range(95,101)]

def test_empathy_explicit_preference():
    x=core.empathy('1',{'consent':True,'preferred_tone':'acolhedor','voice_pitch_mean':300})
    assert x['emotion_detected'] is False and x['prosody_profile']['rate']<1

def test_empathy_requires_consent():
    with pytest.raises(ValueError):core.empathy('1',{'preferred_tone':'objetivo'})

def test_proactive_persistent_and_dedup():
    d={'consent':True,'context':'Revisar projeto','suggested_action':'Conferir testes'}
    a=core.proactive('1',d);b=core.proactive('1',d)
    assert a['id']==b['id'] and b['deduplicated']
    assert len(core._items('1','proposal'))==1

def test_proactive_user_isolation():
    d={'consent':True,'context':'Revisar projeto','suggested_action':'Conferir testes'}
    core.proactive('1',d)
    assert core._items('2','proposal')==[]

def test_proactive_review():
    d={'consent':True,'context':'Tarefa','suggested_action':'Revisar'}
    x=core.proactive('1',d)
    assert core.proposal_review('1',x['id'],True)['executed'] is False
    with pytest.raises(KeyError):core.proposal_review('2',x['id'],True)

def test_narrative_persist_delete():
    e=core.narrative_event('1',{'consent':True,'title':'Teste','description':'Marco real','source':'relato'})
    assert 'Teste' in core.narrative_arc('1')['narrative_summary']
    assert core.narrative_arc('2')['events']==[]
    assert core._delete('1','timeline',e['id'])
    assert core.narrative_arc('1')['events']==[]

def test_narrative_consent():
    with pytest.raises(ValueError):core.narrative_event('1',{'title':'x','description':'y','source':'z'})

def test_research_evidence():
    x=core.research('1',{'question':'O que aconteceu?','sources':[{'title':'Relatório','excerpt':'Resultado parcial'}]})
    assert x['source_count']==1 and x['external_research_performed'] is False
    assert core._get('1','investigation',x['id'])
    assert core._get('2','investigation',x['id']) is None

def test_research_limits():
    with pytest.raises(ValueError):core.research('1',{'question':'x','sources':[{}]})

def test_forge_ast_no_execution():
    x=core.forge('1',{'title':'Ajuste','candidate_code':'print(1)'})
    assert x['syntax']['valid'] and x['production_modified'] is False
    assert x['sandbox_executed'] is False

def test_forge_flags():
    x=core.forge('1',{'title':'Perigo','candidate_code':'eval("2+2")'})
    assert 'eval(' in x['review_flags']

def test_forge_syntax():
    x=core.forge('1',{'title':'Erro','candidate_code':'def :'})
    assert x['syntax']['valid'] is False

def test_mission_selects():
    x=core.mission('1',{'objective':'Pesquisar evidências e corrigir código'})
    ids={e['id'] for e in x['selected_engines']}
    assert {'V98','V99'}<=ids
    assert x['execution_authorized'] is False
    assert core._get('1','mission',x['id'])

def test_mission_isolation():
    x=core.mission('1',{'objective':'Missão estratégica'})
    assert core._get('2','mission',x['id']) is None

def test_status():
    assert core.status('1')['autonomous_code_deployment'] is False
