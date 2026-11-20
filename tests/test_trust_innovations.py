import unittest
from datetime import datetime,timezone,timedelta
from app.agents.trust import Provenance,Covenant,ProceduralMemory,Anima,Vinculum,PolicyError

class TrustTests(unittest.TestCase):
    def contract(self,**kw):
        return Covenant('orgA','report',{'report'},100,datetime.now(timezone.utc)+timedelta(days=1),**kw)
    def test_provenance(self):
        m=Provenance.manifest('orgA','a',b'abc',['source1'],'agent')
        self.assertTrue(Provenance.verify(m,b'abc'))
        self.assertFalse(Provenance.verify(m,b'abd'))
    def test_contract_promotion(self):
        c=self.contract(promotion_threshold=2)
        self.assertEqual(c.record_outcome(True,True),'suggest')
        self.assertEqual(c.record_outcome(True,True),'approve')
        self.assertFalse(c.authorize('orgA','report',10)['allowed'])
        self.assertTrue(c.authorize('orgA','report',10,human_approved=True)['allowed'])
    def test_contract_never_exceeds_cap(self):
        c=self.contract(promotion_threshold=1)
        for _ in range(10):c.record_outcome(True,True)
        self.assertEqual(c.level,'approve')
    def test_contract_demotion(self):
        c=self.contract(level='approve')
        self.assertEqual(c.record_outcome(True,False,severe=True),'suggest')
    def test_contract_tenant_budget(self):
        c=self.contract(level='approve')
        self.assertFalse(c.authorize('orgB','report',1, human_approved=True)['allowed'])
        self.assertFalse(c.authorize('orgA','report',101,human_approved=True)['allowed'])
    def test_unverified_rejected(self):
        with self.assertRaises(PolicyError):self.contract().record_outcome(False,True)
    def test_procedure_tenant_and_regression(self):
        p=ProceduralMemory();p.register('orgA','weekly',1,['step'],True,True)
        self.assertEqual(p.recall('orgA','weekly',1,self.contract(level='approve'),'report',1,True),['step'])
        with self.assertRaises(PolicyError):p.recall('orgB','weekly',1,self.contract(level='approve'),'report',1,True)
        p.deprecate('orgA','weekly',1)
        with self.assertRaises(PolicyError):p.recall('orgA','weekly',1,self.contract(level='approve'),'report',1,True)
    def test_procedure_requires_review(self):
        with self.assertRaises(PolicyError):ProceduralMemory().register('a','b',1,['step'],False,True)
    def test_anima_optin(self):
        self.assertEqual(Anima.calibrate(False,'high','approve')['level'],'approve')
        self.assertEqual(Anima.calibrate(True,'high','approve')['level'],'suggest')
    def test_anima_no_diagnosis(self):
        with self.assertRaises(PolicyError):Anima.calibrate(True,'depressed','approve')
    def test_vinculum_tenant_erase(self):
        v=Vinculum();self.assertEqual(v.charter('orgA','u',{'tone':'short'},True),1)
        v.promise('orgA','u','p','Follow up',True)
        self.assertIn('p',v.outstanding('orgA','u'))
        self.assertEqual(v.outstanding('orgB','u'),{})
        v.erase('orgA','u');self.assertIsNone(v.read('orgA','u'));self.assertEqual(v.outstanding('orgA','u'),{})
    def test_vinculum_no_unconfirmed_promises(self):
        with self.assertRaises(PolicyError):Vinculum().promise('a','u','p','promise',False)
if __name__=='__main__':unittest.main()
