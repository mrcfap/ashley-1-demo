import tempfile
import unittest
from pathlib import Path
from app.engines_v62 import NexusEngine

class NexusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = NexusEngine(Path(self.tmp.name) / 'nexus.db')
    def tearDown(self):
        self.tmp.cleanup()
    def test_create_and_isolate(self):
        p = self.engine.create_project(owner_id='a', title='Horta', purpose='Alimentos', community='Bairro', steps=['Preparar solo'])
        self.assertEqual(p['project']['status'], 'PLANEJADO')
        self.assertIsNone(self.engine.get_project(owner_id='b', project_id=p['project']['id']))
        self.assertEqual(self.engine.list_projects(owner_id='b'), [])
    def test_evidence_requires_confirmation(self):
        p = self.engine.create_project(owner_id='a', title='Horta', purpose='Alimentos', community='Bairro', steps=['Plantar'])
        pid, sid = p['project']['id'], p['steps'][0]['id']
        self.assertTrue(self.engine.report_step(owner_id='a', project_id=pid, step_id=sid, evidence='Foto e ata'))
        self.assertEqual(self.engine.get_project(owner_id='a', project_id=pid)['steps'][0]['status'], 'AGUARDANDO_CONFIRMACAO')
        with self.assertRaises(PermissionError):
            self.engine.confirm_step(owner_id='a', project_id=pid, step_id=sid, approver_id='b')
        self.assertTrue(self.engine.confirm_step(owner_id='a', project_id=pid, step_id=sid, approver_id='a'))
        self.assertEqual(self.engine.get_project(owner_id='a', project_id=pid)['steps'][0]['status'], 'CONFIRMADA')
    def test_reject_invalid_steps(self):
        with self.assertRaises(ValueError):
            self.engine.create_project(owner_id='a', title='Horta', purpose='Alimentos', community='Bairro', steps=[])
    def test_cross_user_cannot_report(self):
        p = self.engine.create_project(owner_id='a', title='Horta', purpose='Alimentos', community='Bairro', steps=['Plantar'])
        self.assertFalse(self.engine.report_step(owner_id='b', project_id=p['project']['id'], step_id=p['steps'][0]['id'], evidence='Feito'))

if __name__ == '__main__': unittest.main()
