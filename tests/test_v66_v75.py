import tempfile
import unittest
from pathlib import Path
from app.engines_v66_v75.core import EngineStore, aletheia, chronos, omni_catalog, ethos, impact, provenance, circuit_breaker, readiness

class MotorsTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=EngineStore(Path(self.temp.name)/'motors.db')
    def tearDown(self): self.temp.cleanup()
    def test_v66_no_unverified_guarantee(self):
        r=aletheia('Lucro 10%',[{'reference':'relatorio','excerpt':'10%','trusted':True}])
        self.assertFalse(r['usable_for_official_report'])
    def test_v67_no_automatic_rescheduling(self):
        r=chronos([{'id':'a','critical':False}],2,True)
        self.assertEqual(r['executed'],0);self.assertEqual(len(r['proposals']),1)
    def test_v68_catalog_no_calls(self):
        self.assertEqual(omni_catalog([{'name':'erp','scope':'read'}])['remote_calls'],0)
    def test_v69_denies_and_isolates(self):
        self.assertFalse(ethos(self.db,'a','finance')['allowed'])
        self.db.grant('a','finance',True)
        self.assertTrue(ethos(self.db,'a','finance')['allowed'])
        self.assertFalse(ethos(self.db,'b','finance')['allowed'])
        self.assertFalse(ethos(self.db,'a','finance',critical=True)['allowed'])
    def test_v70_tenant_isolation(self):
        p=impact(self.db,'a','Cozinha',['Contato com voluntários'])
        self.assertIsNone(self.db.get('b','impact',p['id']))
        self.assertEqual(len(self.db.list('a','impact')),1)
    def test_v73_digest_only(self):
        self.db.audit('a','test',{'secret':'senha'})
        events=provenance(self.db,'a')['events']
        self.assertNotIn('senha',str(events))
    def test_v74_no_execution(self):
        self.assertFalse(circuit_breaker('high',True)['allowed_to_execute'])
        self.assertFalse(circuit_breaker('medium',False)['allowed_to_plan'])
    def test_v75_readiness(self):
        self.assertFalse(readiness({'authentication':True})['ready_for_production'])
        self.assertTrue(readiness({k:True for k in ('authentication','tenant_isolation','consent','tests','observability','rollback')})['ready_for_production'])
if __name__=='__main__': unittest.main()
