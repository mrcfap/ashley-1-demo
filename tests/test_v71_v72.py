import tempfile
import unittest
from pathlib import Path
from app.humanization.engines import AnamnesisV71, ResonanceSilenceV72

class HumanizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = AnamnesisV71(Path(self.temp.name) / 'human.db')

    def tearDown(self):
        self.temp.cleanup()

    def test_consent_required(self):
        with self.assertRaises(PermissionError):
            self.engine.add('a', 'Marco sem permissao')

    def test_isolation(self):
        self.engine.add('a', 'Conquista', consent=True)
        self.assertEqual(self.engine.list('b'), [])

    def test_delete_own_only(self):
        item = self.engine.add('a', 'Conquista', consent=True)
        self.assertFalse(self.engine.delete('b', item['id']))
        self.assertTrue(self.engine.delete('a', item['id']))
        self.assertEqual(self.engine.list('a'), [])

    def test_no_fake_emotion(self):
        plan = ResonanceSilenceV72().plan(preference='quiet')
        self.assertEqual(plan['mode'], 'quiet')
        self.assertFalse(plan['allow_followup'])

    def test_safety_override(self):
        plan = ResonanceSilenceV72().plan(preference='quiet', urgent=True)
        self.assertEqual(plan['mode'], 'safety_priority')

if __name__ == '__main__':
    unittest.main()
