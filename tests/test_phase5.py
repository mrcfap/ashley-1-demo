import tempfile
import unittest
from pathlib import Path
from app.memory.semantic_memory_safe import SemanticMemoryStore
from app.agents.autonomous.phase5 import AutonomousCodingPhase5

class Phase5Tests(unittest.TestCase):
    def test_memory_isolation_and_similarity(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SemanticMemoryStore(Path(tmp)/'memory.db')
            store.store(user_id='1',content='comprar café',vector=[1,0],embedding_model='test')
            store.store(user_id='2',content='privado',vector=[1,0],embedding_model='test')
            self.assertEqual([x['content'] for x in store.search(user_id='1',vector=[1,0],embedding_model='test')], ['comprar café'])
            self.assertEqual(store.search(user_id='1',vector=[1,0],embedding_model='outro'), [])

    def test_zero_vector_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SemanticMemoryStore(Path(tmp)/'memory.db')
            with self.assertRaises(ValueError):
                store.store(user_id='1',content='x',vector=[0,0],embedding_model='test')

    def test_phase5_plan_no_production_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'module.py').write_text('x = 1\n',encoding='utf-8')
            class StubBridge: pass
            phase = AutonomousCodingPhase5(root,bridge=StubBridge())
            plan = phase.plan('Melhorar módulo',['module.py'])
            self.assertFalse(plan['production_changes_allowed'])
            self.assertTrue(plan['requires_human_approval'])
            self.assertEqual((root/'module.py').read_text(), 'x = 1\n')
            with self.assertRaises(ValueError):
                phase.plan('Alterar',['../outside.py'])

if __name__ == '__main__': unittest.main()
