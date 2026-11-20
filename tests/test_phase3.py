import unittest
from app.agents.autonomous.phase3 import AutonomousCodingPhase3

class Phase3Tests(unittest.TestCase):
    def test_safe_code(self):
        agent = AutonomousCodingPhase3.__new__(AutonomousCodingPhase3)
        report = agent.review_static({'app/demo.py': 'def f(x):\n    return x + 1\n'})
        self.assertTrue(report['syntax_ok'])
        self.assertFalse(report['approved_for_production'])
    def test_invalid_syntax(self):
        agent = AutonomousCodingPhase3.__new__(AutonomousCodingPhase3)
        self.assertFalse(agent.review_static({'x.py': 'def ('})['syntax_ok'])
    def test_sensitive_call(self):
        agent = AutonomousCodingPhase3.__new__(AutonomousCodingPhase3)
        report = agent.review_static({'x.py': 'eval("1+1")'})
        self.assertTrue(report['static_findings'])
