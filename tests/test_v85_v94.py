import pytest
from app.axiom_v85_v94.core import run,catalog

def test_catalog(): assert [x['id'] for x in catalog()]==[f'V{i}' for i in range(85,95)]
def test_neuroplastic_consent():
    with pytest.raises(ValueError): run(85,'consolidate',{'fact':'hello','verified':True},'a')
    assert run(85,'consolidate',{'fact':'hello','verified':True,'consent':True},'a')['stored']
    assert run(85,'status',{},'b')['facts']==0

def test_causal(): assert run(86,'simulate',{'scenarios':[{'name':'a','probability':.5,'impact':10}]},'u')['scenarios'][0]['expected_value']==5

def test_metaforge_no_execution(): assert not run(87,'propose',{'issue':'latency'},'u')['code_executed']
def test_chronos():
    r=run(88,'commit',{'goal':'latency','expected':10},'u')
    assert run(88,'observe',{'id':r['id'],'observed':8},'u')['deviation']==-2

def test_eureka(): assert not run(89,'investigate',{'question':'why'},'u')['research_performed']
def test_neuropulse(): assert not run(90,'budget',{'event_changed':False,'estimated_cost_ms':20,'budget_ms':10},'u')['within_budget']
def test_privacy(): assert run(91,'assess',{'fields':['email','name']},'u')['requires_explicit_consent']
def test_affect_consent():
    with pytest.raises(ValueError): run(92,'modulate',{},'u')
def test_swarm(): assert len(run(93,'partition',{'tasks':['a','b']},'u')['agents'])==2
def test_prism(): assert len(run(94,'compose',{'objective':'test','engines':['V85','V86']},'u')['steps'])==2
