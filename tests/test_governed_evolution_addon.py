import tempfile
import unittest
from app.evolution.governed_evolution import propose, export_review

class GovernedEvolutionTests(unittest.TestCase):
    def test_proposal_never_applies_code(self):
        with tempfile.TemporaryDirectory() as folder:
            p = propose("app/demo.py", "Improve response", "print(1)")
            output = export_review(p, folder)
            self.assertTrue(output.exists())
            self.assertEqual(p.status, "pending_review")
    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            propose("../secret", "reason", "patch")
    def test_requires_explanation(self):
        with self.assertRaises(ValueError):
            propose("app/demo.py", "", "patch")
