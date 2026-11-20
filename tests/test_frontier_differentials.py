import unittest
from app.agents.frontier_differentials.agents import ParallaxAgent, SeedbankAgent, SymbiosisAgent

class TestDifferentials(unittest.TestCase):
    def test_parallax_requires_review_when_missing(self):
        r = ParallaxAgent().challenge({"objective":"reduce cost"}, {"financeiro":{"risk":.1}})
        self.assertEqual(r["recommendation"], "HUMAN_REVIEW")
        self.assertEqual(len(r["missing_perspectives"]), 4)
    def test_parallax_high_risk(self):
        a={p:{"risk":.1} for p in ParallaxAgent.PERSPECTIVES}
        a["seguranca"]["risk"] = .9
        self.assertIn("seguranca", ParallaxAgent().challenge({"objective":"ship"},a)["high_risk"])
    def test_parallax_complete(self):
        a={p:{"risk":.1} for p in ParallaxAgent.PERSPECTIVES}
        self.assertEqual(ParallaxAgent().challenge({"objective":"ship"},a)["recommendation"],"READY_FOR_EXTERNAL_VALIDATION")
    def test_seedbank_tenant_isolation(self):
        s=SeedbankAgent(); c=s.create("a","alice",{"secret":"x"},"research")
        with self.assertRaises(PermissionError): s.read(c,"b","alice")
        with self.assertRaises(PermissionError): s.read(c,"a","bob")
        s.grant(c,"a","alice","bob")
        self.assertEqual(s.read(c,"a","bob")["content"]["secret"],"x")
    def test_seedbank_revoke(self):
        s=SeedbankAgent(); c=s.create("a","alice",{"x":1},"research")
        s.revoke(c,"a","alice")
        with self.assertRaises(PermissionError): s.read(c,"a","alice")
    def test_seedbank_grant_cannot_cross_tenant(self):
        s=SeedbankAgent(); c=s.create("a","alice",{},"research")
        with self.assertRaises(PermissionError): s.grant(c,"b","alice","bob")
    def test_symbiosis_improvement(self):
        r=SymbiosisAgent().evaluate("t",{"independent_success":.2,"quality_score":.7},
                                     {"independent_success":.8,"quality_score":.9})
        self.assertEqual(r["interpretation"],"IMPROVED")
        self.assertFalse(r["causal_claim"])
    def test_symbiosis_validation(self):
        with self.assertRaises(ValueError):
            SymbiosisAgent().evaluate("t",{"independent_success":2,"quality_score":.7},
                                     {"independent_success":.8,"quality_score":.9})
if __name__ == "__main__": unittest.main()
