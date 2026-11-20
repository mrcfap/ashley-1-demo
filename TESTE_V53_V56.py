import tempfile, unittest
from pathlib import Path
from app.future_v53_v56 import PrometheusV53, ConductorV54, GuardianV55, HorizonV56

class Tests(unittest.TestCase):
    def test_v53_order(self):
        result = PrometheusV53().compare([
            {"name":"A","benefit":100,"cost":20,"risk":0.1},
            {"name":"B","benefit":80,"cost":30,"risk":0.2}])
        self.assertEqual(result[0]["name"], "A")
    def test_v53_invalid(self):
        with self.assertRaises(ValueError):
            PrometheusV53().compare([{"name":"X","benefit":1,"cost":-1,"risk":0}])
    def test_v54_plan_only(self):
        plan = ConductorV54().plan("Projeto", ["financeiro","mercado"], 10)
        self.assertFalse(plan["executed"])
        self.assertEqual(len(plan["assignments"]), 2)
    def test_v55_safe_recovery(self):
        g=GuardianV55()
        self.assertEqual(g.decide("timeout",0,idempotent=False)["action"],"manual_review")
        self.assertEqual(g.decide("timeout",0,idempotent=True)["action"],"retry_with_backoff")
        self.assertEqual(g.decide("timeout",3,idempotent=True)["action"],"stop")
    def test_v56_approval_flow(self):
        with tempfile.TemporaryDirectory() as d:
            h=HorizonV56(Path(d)/"test.db")
            ident=h.propose("alice","Falta parser","Criar parser","Testar entradas")
            with self.assertRaises(PermissionError):
                h.review("alice",ident,True)
            with self.assertRaises(ValueError):
                h.review("alice",ident,True,authorized=True)
            h.submit_evidence("alice",ident,[{"test":"teste básico","passed":True}])
            self.assertEqual(h.review("alice",ident,True,authorized=True),"APPROVED")
            self.assertIsNone(h.get("bob",ident))
    def test_v56_failed_tests_block(self):
        with tempfile.TemporaryDirectory() as d:
            h=HorizonV56(Path(d)/"test.db")
            ident=h.propose("alice","Falha","Hipótese","Plano")
            h.submit_evidence("alice",ident,[{"test":"regressão","passed":False}])
            with self.assertRaises(ValueError):
                h.review("alice",ident,True,authorized=True)
            self.assertEqual(h.review("alice",ident,False,authorized=True),"REJECTED")

if __name__ == "__main__":
    unittest.main()
