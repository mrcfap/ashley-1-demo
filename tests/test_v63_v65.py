import unittest
from app.engines_v63_v65 import PsycheSynapseV63, RealityBridgeV64, EpistemicCoreV65

class NewEngineTests(unittest.TestCase):
    def test_v63_requires_consent(self):
        with self.assertRaises(PermissionError): PsycheSynapseV63().suggest(8, consent=False)
    def test_v63_no_diagnosis(self):
        x=PsycheSynapseV63().suggest(9, consent=True)
        self.assertFalse(x.clinical_diagnosis)
    def test_v64_needs_evidence_and_confirmation(self):
        m=RealityBridgeV64(); item=m.plan('u1','Organizar atividade')
        self.assertEqual(item['status'],'PLANEJADO')
        m.submit_evidence('u1',item['id'],'Registro da atividade')
        self.assertEqual(m.verify('u1',item['id'],approved_by_human=False)['status'],'AGUARDANDO_VERIFICACAO')
        self.assertEqual(m.verify('u1',item['id'],approved_by_human=True)['status'],'CONFIRMADO_POR_PESSOA')
    def test_v64_isolation(self):
        m=RealityBridgeV64(); item=m.plan('u1','Tarefa')
        with self.assertRaises(KeyError): m.submit_evidence('u2',item['id'],'prova')
    def test_v65_no_fake_certainty(self):
        m=EpistemicCoreV65()
        self.assertTrue(m.assess('Algo ocorreu','inferencia')['requires_review'])
        with self.assertRaises(ValueError): m.assess('Algo ocorreu','inferencia',evidence='acho',independently_verified=True)

if __name__=='__main__': unittest.main()
