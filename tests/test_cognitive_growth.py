from app.cognitive_growth import CognitiveGrowth, EmotionalState

def test_state_bounds():
    s=EmotionalState()
    for _ in range(50): s.update(False,2,-3)
    assert all(0<=x<=1 for x in vars(s).values())

def test_reflection_and_proposal(tmp_path):
    c=CognitiveGrowth(tmp_path/'growth.db')
    c.record('feedback',{'success':False})
    assert c.reflect()['success_rate']==0
    p=c.propose('Melhorar validação','Adicionar testes de regressão antes de qualquer alteração')
    assert p['requires_human_review']
    assert c.list_proposals()[0]['status']=='pending'
