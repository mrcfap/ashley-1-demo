import unittest, tempfile, pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from app.future_v48_v51 import LearningV48,FinOpsV49,WatchdogV50,SyncV51
from app.synapse_v52.engine import SynapseV52,MotorSpec
class Tests(unittest.TestCase):
 def test_learning(self):
  with tempfile.TemporaryDirectory() as d:
   m=LearningV48(pathlib.Path(d)/'test.db');i=m.propose('a','pattern','case');self.assertEqual(m.approved('a'),[])
   with self.assertRaises(PermissionError):m.approve('a',i)
   self.assertTrue(m.approve('a',i,authorized=True));self.assertEqual(len(m.approved('a')),1);self.assertEqual(m.approved('b'),[])
 def test_finops(self):
  self.assertFalse(FinOpsV49().estimate(1000000,0,2,0,budget_usd=1)['within_budget'])
 def test_watchdog(self):
  self.assertEqual(WatchdogV50().inspect('resposta',[])['status'],'review_required')
 def test_sync(self):
  m=SyncV51(b'a'*32);e=m.pack('a',2,{'x':1});self.assertTrue(m.verify(e,'a',2));e['body']['state']['x']=2;self.assertFalse(m.verify(e,'a',2))
 def test_synapse(self):
  s=SynapseV52();s.register(MotorSpec('V48','48',probe=lambda:True));self.assertTrue(s.audit()['certified'])
if __name__=='__main__':unittest.main()
