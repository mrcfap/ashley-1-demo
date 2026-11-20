import tempfile
import unittest
from pathlib import Path
from app.humanity_v76 import HumanityCoreV76

class HumanityCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = HumanityCoreV76(Path(self.temp.name) / 'v76.db')

    def tearDown(self):
        self.temp.cleanup()

    def test_consent_required(self):
        with self.assertRaises(PermissionError):
            self.engine.create_goal('a', 'Aprender')

    def test_isolation(self):
        self.engine.consent('a', True)
        self.engine.consent('b', True)
        g = self.engine.create_goal('a', 'Aprender')
        self.assertEqual(self.engine.list_goals('b'), [])
        with self.assertRaises(LookupError):
            self.engine.progress('b', g['id'])

    def test_evidence_distinction(self):
        self.engine.consent('a', True)
        g = self.engine.create_goal('a', 'Projeto')
        self.engine.record_progress('a', g['id'], 'Avancei', confirmed=True)
        self.assertEqual(self.engine.progress('a', g['id'])['verified_outcomes'], 0)
        self.engine.record_progress('a', g['id'], 'Concluído', evidence='Registro do usuário', confirmed=True)
        self.assertEqual(self.engine.progress('a', g['id'])['verified_outcomes'], 1)

    def test_no_autonomous_execution(self):
        self.engine.consent('a', True)
        self.assertFalse(self.engine.propose('a', 'Me ajude', requested_action='plan')['executed'])
        self.assertEqual(self.engine.propose('a', 'Me ajude', requested_action='transfer_money')['decision'], 'deny')

    def test_revoke_and_delete(self):
        self.engine.consent('a', True)
        self.engine.create_goal('a', 'Meta')
        self.engine.consent('a', False)
        with self.assertRaises(PermissionError):
            self.engine.list_goals('a')
        self.engine.delete_my_data('a')
        self.engine.consent('a', True)
        self.assertEqual(self.engine.list_goals('a'), [])

if __name__ == '__main__':
    unittest.main()
