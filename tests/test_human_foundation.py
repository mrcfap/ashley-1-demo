import unittest
from app.agents.human_foundation import EloAgent, HorizonteVivoAgent, EssentiaAgent, HumanFoundation
from app.agents.human_foundation.core import HumanCharter

class FoundationTests(unittest.TestCase):
    def setUp(self): self.charter=HumanCharter('tenant-a:user-1',['tempo familiar'],{'hours_week':40,'budget':1000},consent=True)
    def test_elo_consent(self): self.assertEqual(EloAgent().respond_mode('conversa',False)['status'],'CONSENT_REQUIRED')
    def test_elo_invalid(self): self.assertEqual(EloAgent().respond_mode('diagnostico',True)['status'],'INVALID_MODE')
    def test_elo_silence(self): self.assertEqual(EloAgent().respond_mode('silencio',True)['mode'],'silencio')
    def test_horizonte_constraints(self): self.assertEqual(HorizonteVivoAgent().compare([{'name':'A','metrics':{'budget':1100}}],{'budget':1000})['scenarios'][0]['violations'],['budget'])
    def test_horizonte_missing(self): self.assertFalse(HorizonteVivoAgent().compare([{'name':'A','metrics':{}}],{'budget':1000})['scenarios'][0]['within_limits'])
    def test_essentia_conflict(self): self.assertEqual(EssentiaAgent().assess(self.charter,{'metrics':{'hours_week':60,'budget':500}})['conflicts'][0]['metric'],'hours_week')
    def test_essentia_consent(self): self.charter.consent=False;self.assertEqual(EssentiaAgent().assess(self.charter,{})['status'],'CONSENT_REQUIRED')
    def test_essentia_missing(self): self.assertEqual(EssentiaAgent().assess(self.charter,{'metrics':{}})['status'],'REVIEW_REQUIRED')
    def test_no_autonomous_execution(self):
        result=HumanFoundation().review(self.charter,'solucao',[{'name':'A','metrics':{'budget':500,'hours_week':30}}])
        self.assertFalse(result['execution_authorized'])
        self.assertEqual(result['essentia'][0]['status'],'ALIGNED_WITH_DECLARED_LIMITS')
if __name__=='__main__': unittest.main()
