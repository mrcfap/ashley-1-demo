import unittest
from pathlib import Path

class V76RouteRegistrationTests(unittest.TestCase):
    def test_v76_registered_with_authenticated_identity(self):
        source = (Path(__file__).resolve().parents[1] / 'app' / 'API' / 'app.py').read_text(encoding='utf-8-sig')
        self.assertIn('make_v76_router(HumanityCoreV76(', source)
        self.assertIn('identity as v76_authenticated_identity', source)

    def test_v76_endpoints_require_dependency(self):
        source = (Path(__file__).resolve().parents[1] / 'app' / 'humanity_v76' / 'api.py').read_text(encoding='utf-8-sig')
        self.assertEqual(source.count('Depends(get_authenticated_user_id)'), 7)

if __name__ == '__main__':
    unittest.main()
