import unittest
from app.agents.autonomous.phase2 import AutonomousCodingPhase2
class Phase2Tests(unittest.TestCase):
    def test_invalid_file_scope(self):
        import asyncio, tempfile
        with tempfile.TemporaryDirectory() as d:
            agent=AutonomousCodingPhase2(d)
            with self.assertRaises(ValueError):
                asyncio.run(agent.propose("teste", []))
