import asyncio
import tempfile
import unittest
from pathlib import Path
from app.agents.autonomous.phase4 import CodingV22Bridge

class FakeCoder:
    async def propose_and_review(self, goal, files):
        return {'id':'test-mission', 'workspace':'isolated-test', 'phase3_review':{'syntax_ok':True}}

class Phase4Tests(unittest.TestCase):
    def test_approval_and_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'sample.py').write_text('x=1\n')
            bridge=CodingV22Bridge(root,coder=FakeCoder())
            task=bridge.submit(1,'Melhorar código',['sample.py'])
            self.assertEqual(task['status'],'AGUARDANDO_APROVACAO')
            with self.assertRaises(ValueError): asyncio.run(bridge.run_approved(task['id'],1))
            bridge.approve_generation(task['id'],1)
            result=asyncio.run(bridge.run_approved(task['id'],1))
            self.assertFalse(result['production_modified'])
            self.assertEqual(bridge.queue.obter(task['id'],1)['status'],'CONCLUIDA')
            self.assertEqual((root/'sample.py').read_text(),'x=1\n')
    def test_reject_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            bridge=CodingV22Bridge(tmp,coder=FakeCoder())
            with self.assertRaises(ValueError): bridge.submit(1,'teste',['../outside.py'])
if __name__=='__main__': unittest.main()
