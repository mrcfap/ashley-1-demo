import unittest
from app.nextgen.engines import LumenV81, PraxisV82, SentinelV83, SymphonyV84, Risk

class NextgenTests(unittest.TestCase):
    def test_lumen_consent_and_change(self):
        l=LumenV81()
        self.assertFalse(l.observe('a',event='camera',consent=False)['analyze'])
        self.assertTrue(l.observe('a',event='objeto',fingerprint='a',consent=True)['analyze'])
        self.assertFalse(l.observe('a',event='objeto',fingerprint='a',consent=True)['analyze'])
        self.assertTrue(l.observe('a',event='olha',user_trigger=True,consent=True)['analyze'])
        l.clear('a'); self.assertEqual(l.context('a',consent=True),[])
    def test_praxis_approval(self):
        p=PraxisV82().propose('email',Risk.EXTERNAL,preview='Olá',user_id='1')
        with self.assertRaises(PermissionError): PraxisV82().approve(p,authenticated_user_id='2',explicit_confirmation=True)
        self.assertFalse(PraxisV82().approve(p,authenticated_user_id='1',explicit_confirmation=True)['executed'])
    def test_sentinel(self):
        s=SentinelV83()
        self.assertFalse(s.inspect_upload('x.exe',2,b'MZ')['allowed'])
        self.assertFalse(s.inspect_upload('../x.pdf',10,b'%PDF')['allowed'])
        self.assertTrue(s.precheck_request('como clonar cartão de crédito')['blocked'])
    def test_symphony(self):
        s=SymphonyV84()
        self.assertEqual(s.route(consent=True,safety_allowed=True,requested_action='email')['state'],'AWAITING_APPROVAL')
        self.assertEqual(s.route(consent=True,safety_allowed=False,requested_action='read')['state'],'DENIED')

if __name__=='__main__':unittest.main()
