import tempfile
from pathlib import Path
from app.cognitive_growth import CognitiveGrowthEngine

def test_core():
    with tempfile.TemporaryDirectory() as d:
        e=CognitiveGrowthEngine(Path(d)/'db.sqlite3')
        e.experience('Teste',feedback=1)
        assert e.emotion_state()['satisfacao']==1
        goal=e.add_goal('Revisar testes',9)
        assert e.deliberate()['goals'][0]['id']==goal
        p=e.propose_change('app/example.py','--- a/app/example.py\n+++ b/app/example.py','Melhoria')
        e.review_proposal(p,True)
        assert e.proposals()[0]['status']=='approved_for_manual_testing'
