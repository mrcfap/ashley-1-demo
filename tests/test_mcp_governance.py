import unittest
from app.integrations.mcp_governance.policy import PolicyRouter

class MCPGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.router = PolicyRouter({'files.read': 'read', 'files.write': 'write', 'payment.execute': 'sensitive'})
    def test_unknown_tool_denied(self):
        d = self.router.evaluate(tool_name='shell.execute', arguments={}, authenticated_user='1')
        self.assertEqual(d.status, 'BLOQUEADO')
    def test_auth_required(self):
        d = self.router.evaluate(tool_name='files.read', arguments={}, authenticated_user=None)
        self.assertEqual(d.reason_code, 'UNAUTHENTICATED')
    def test_read_can_be_dispatched(self):
        d = self.router.evaluate(tool_name='files.read', arguments={}, authenticated_user='1')
        self.assertEqual(d.status, 'PERMITIDO_PARA_DESPACHO')
    def test_sensitive_requires_approval_even_with_id(self):
        d = self.router.evaluate(tool_name='payment.execute', arguments={}, authenticated_user='1', approved_action_id='fake')
        self.assertEqual(d.status, 'AGUARDANDO_AUTORIZACAO')
    def test_write_requires_approval(self):
        d = self.router.evaluate(tool_name='files.write', arguments={}, authenticated_user='1')
        self.assertTrue(d.approval_required)

if __name__ == '__main__': unittest.main()
