import unittest
from app.agents.enhancement.agents import *

class EnhancementTests(unittest.TestCase):
    def test_memory(self):
        a=MNEMOSYNE()
        with self.assertRaises(PermissionError): a.remember('u1','fact','ref',consent=False)
        ident=a.remember('u1','fact','ref',consent=True)
        self.assertEqual(a.review(ident,verified=True,approved=True)['status'],'verified')
        self.assertEqual(len(a.recall('u2')),0)
        self.assertTrue(a.forget(ident))
    def test_atlas(self):
        a=ATLAS(); ident=a.create('goal')
        with self.assertRaises(PermissionError): a.transition(ident,'approved')
        a.transition(ident,'approved',approved=True)
        a.transition(ident,'running',approved=True)
        self.assertEqual(a.transition(ident,'completed')['status'],'completed')
    def test_spectra(self):
        a=SPECTRA();a.ingest_reference('audio','r2',200,consent=True);a.ingest_reference('text','r1',100,consent=True)
        self.assertEqual(a.timeline()[0]['ref'],'r1')
    def test_darwin(self):
        a=DARWIN(); checks=dict.fromkeys(['syntax','tests','security','rollback'],True)
        self.assertFalse(a.assess('c',checks,human_approved=False)['eligible_for_manual_review'])
        self.assertTrue(a.assess('c',checks,human_approved=True)['eligible_for_manual_review'])
    def test_impact(self):
        self.assertEqual(IMPACT().compare('hours',10,8,'r')['delta'],-2)
    def test_oracle(self):
        self.assertEqual(ORACLE().scenarios(100,{'growth':.2})['scenarios']['growth'],120)
    def test_immunis(self):
        a=IMMUNIS();self.assertFalse(a.authorize('deploy',{'deploy'})['allowed'])
        self.assertTrue(a.authorize('deploy',{'deploy'},human_approved=True)['allowed'])
    def test_metacore(self):
        self.assertAlmostEqual(METACORE().evaluate({'accuracy':.7},{'accuracy':.9})['findings'][0]['gap'],.2)
if __name__=='__main__': unittest.main()
