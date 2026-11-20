import unittest,tempfile
from pathlib import Path
from app.fortress_v57 import CircuitBreaker,MemoryBudget,Telemetry,SafeRelease
from app.legacy_v58 import LegacyTracker
class Tests(unittest.TestCase):
 def test_circuit(self):
  t=[0];c=CircuitBreaker(2,10,lambda:t[0]);self.assertTrue(c.allow());c.failure();c.failure()
  self.assertEqual(c.state,'OPEN');self.assertFalse(c.allow());t[0]=11
  self.assertTrue(c.allow());self.assertFalse(c.allow());c.success();self.assertEqual(c.state,'CLOSED')
 def test_memory(self):
  m=MemoryBudget();r=m.select([{'id':1,'text':'critical'},{'id':2,'text':'other'}],8,[1]);self.assertEqual(r['chunks'][0]['id'],1)
  with self.assertRaises(ValueError):m.select([{'id':1,'text':'critical'}],2,[1])
 def test_telemetry(self):
  with tempfile.TemporaryDirectory() as d:
   t=Telemetry(Path(d)/'events.db');t.emit('t','v57','timeout',{'error_code':'429','secret':'never'})
   self.assertNotIn('secret',str(t.by_trace('t')))
 def test_release(self):
  s=SafeRelease();self.assertFalse(s.check_python('def :')['syntax_ok'])
  self.assertEqual(s.rollback_plan('0'*64,'1'*64)['action'],'require_authorization')
  self.assertFalse(s.rollback_plan('0'*64,'1'*64,True)['executed'])
 def test_legacy(self):
  with tempfile.TemporaryDirectory() as d:
   l=LegacyTracker(Path(d)/'goals.db')
   with self.assertRaises(PermissionError):l.create('u','job','interviews',0,3)
   g=l.create('u','job','interviews',0,3,True);l.review('u',g,1,'first')
   self.assertEqual(l.status('u',g)['last_review']['observed'],1)
   self.assertIsNone(l.status('another',g));l.set_status('u',g,'PAUSED')
   with self.assertRaises(ValueError):l.review('u',g,2,'paused')
if __name__=='__main__':unittest.main()
