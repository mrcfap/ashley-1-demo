import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.agents.autonomous.coordinator import CodingCoordinator

class TestCoordinator(unittest.TestCase):
    def test_mission_creation_and_no_production_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'demo.py').write_text('x = 1\n', encoding='utf8')
            c = CodingCoordinator(root)
            mission = c.create_mission('Melhorar demo', ['demo.py'])
            self.assertEqual(mission['status'], 'AGUARDANDO_CANDIDATO')
            self.assertEqual((root / 'demo.py').read_text(), 'x = 1\n')
            with self.assertRaises(ValueError):
                c.analyze(mission['id'], {'../outside.py': 'x = 2'})
            self.assertEqual((root / 'demo.py').read_text(), 'x = 1\n')

if __name__ == '__main__':
    unittest.main()
