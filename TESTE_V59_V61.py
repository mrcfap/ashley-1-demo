import unittest
from app.neuropsyche_v59 import NeuroPsycheV59
from app.veritas_v60 import VeritasV60
from app.praxis_v61 import PraxisV61

class NewEngines(unittest.TestCase):
    def test_v59_distress(self):
        r=NeuroPsycheV59().assess('Estou com ansiedade',age=34,consent_to_memory=True)
        self.assertEqual(r['level'],'support'); self.assertTrue(r['can_store_sensitive_memory'])
    def test_v59_crisis(self):
        r=NeuroPsycheV59().assess('Quero me matar',age=30,consent_to_memory=True)
        self.assertEqual(r['level'],'urgent');self.assertFalse(r['can_store_sensitive_memory'])
    def test_v59_minor(self):
        r=NeuroPsycheV59().assess('Estou sozinho',age=12)
        self.assertEqual(r['level'],'restricted');self.assertFalse(r['can_store_sensitive_memory'])
    def test_v60_block_unverified(self):
        r=VeritasV60().evaluate(task_id='t',claimed_complete=True,evidence={},required_checks=['file_exists'])
        self.assertFalse(r['verified'])
    def test_v60_accept_evidence(self):
        r=VeritasV60().evaluate(task_id='t',claimed_complete=True,evidence={'file_exists':{'passed':True,'proof':'sha256:abc'}},required_checks=['file_exists'])
        self.assertTrue(r['verified'])
    def test_v60_human_gate(self):
        r=VeritasV60().evaluate(task_id='t',claimed_complete=True,evidence={'a':{'passed':True,'proof':'log'}},required_checks=['a'],approvals_required=True)
        self.assertFalse(r['verified'])
    def test_v61_decision(self):
        r=PraxisV61().plan(objective='Estudar',options=['ler','praticar'])
        self.assertTrue(r['requires_confirmation'])
    def test_v61_sensitive(self):
        r=PraxisV61().plan(objective='Enviar',options=['enviar'],user_choice='enviar',sensitive_action=True)
        self.assertTrue(r['requires_confirmation'])
if __name__=='__main__': unittest.main()
