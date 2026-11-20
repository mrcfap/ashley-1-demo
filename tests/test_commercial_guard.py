import unittest
from app.security.commercial_guard import forbidden_identity_in_url, multipart_user_id

class CommercialGuardTests(unittest.TestCase):
    def test_path_user_isolation(self):
        self.assertTrue(forbidden_identity_in_url('/casos/7/12', {}, 8))
        self.assertFalse(forbidden_identity_in_url('/casos/7/12', {}, 7))
        self.assertTrue(forbidden_identity_in_url('/vision/cognitive-hub/7', {}, 8))
        self.assertTrue(forbidden_identity_in_url('/vision/presence/status/7', {}, 8))
        self.assertTrue(forbidden_identity_in_url('/vision/presence/stop/7', {}, 8))
    def test_query_user_isolation(self):
        self.assertTrue(forbidden_identity_in_url('/memoria/guardar', {'user_id':'9'}, 8))
        self.assertFalse(forbidden_identity_in_url('/memoria/guardar', {'user_id':'8'}, 8))
        self.assertTrue(forbidden_identity_in_url('/memoria/guardar', {'user_id':'x'}, 8))
    def test_multipart_identity(self):
        boundary='ASHLEY_TEST'
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="user_id"\r\n\r\n5\r\n--{boundary}--\r\n').encode()
        self.assertEqual(multipart_user_id(body, f'multipart/form-data; boundary={boundary}'), 5)
        self.assertIsNone(multipart_user_id(b'bad', f'multipart/form-data; boundary={boundary}'))
    def test_unknown_path_is_not_mistaken_for_user_id(self):
        self.assertFalse(forbidden_identity_in_url('/casos/7/12', {}, 7))
        self.assertFalse(forbidden_identity_in_url('/api/v1/engines/v76/goals/12/progress', {}, 7))

if __name__ == '__main__': unittest.main()

class CommercialAgeGateTests(unittest.TestCase):
    def test_registration_of_minor_rejected_in_commercial_mode(self):
        import os
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.security import auth
        with patch.dict(os.environ, {'ASHLEY_COMMERCIAL_MODE':'1'}):
            with self.assertRaises(HTTPException) as caught:
                auth.register_user('minor@example.test','longpassword123','Pessoa Teste','2014-01-01','guardian@example.test')
        self.assertEqual(caught.exception.status_code,403)
    def test_profile_change_to_minor_rejected_in_commercial_mode(self):
        import os
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.security import auth
        with patch.dict(os.environ, {'ASHLEY_COMMERCIAL_MODE':'1'}):
            with self.assertRaises(HTTPException) as caught:
                auth.update_profile(1,'Pessoa Teste','2014-01-01','guardian@example.test')
        self.assertEqual(caught.exception.status_code,403)
