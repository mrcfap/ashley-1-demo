"""Gate fail-closed: avalia pedidos, mas NAO executa ferramentas MCP.

A identidade deve vir do backend autenticado, nunca de agent_id/user_id do payload.
"""
from dataclasses import dataclass
from typing import Any, Mapping
import re
import uuid

TOOL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.:-]{0,127}$")

@dataclass(frozen=True)
class Decision:
    action_id: str
    status: str
    reason_code: str
    explanation: str
    approval_required: bool

class PolicyRouter:
    def __init__(self, allowed_tools: Mapping[str, str] | None = None):
        # ferramenta -> classe de risco, definida pelo administrador, nao pelo agente
        self._allowed = dict(allowed_tools or {})
        if any(v not in ('read', 'write', 'sensitive') for v in self._allowed.values()):
            raise ValueError('Classe de risco invalida')

    def evaluate(self, *, tool_name: str, arguments: Mapping[str, Any],
                 authenticated_user: str | None, approved_action_id: str | None = None) -> Decision:
        action_id = str(uuid.uuid4())
        def result(status, code, explanation, approval=False):
            return Decision(action_id, status, code, explanation, approval)
        if not authenticated_user:
            return result('BLOQUEADO', 'UNAUTHENTICATED', 'Autenticacao obrigatoria')
        if not isinstance(tool_name, str) or not TOOL_RE.fullmatch(tool_name):
            return result('BLOQUEADO', 'INVALID_TOOL', 'Nome de ferramenta invalido')
        if not isinstance(arguments, Mapping):
            return result('BLOQUEADO', 'INVALID_ARGS', 'Argumentos invalidos')
        risk = self._allowed.get(tool_name)
        if risk is None:
            return result('BLOQUEADO', 'NOT_ALLOWLISTED', 'Ferramenta nao autorizada')
        if risk != 'read':
            # Um ID de aprovacao nao basta: precisa ser validado e consumido no V22,
            # associado ao usuario, ferramenta, argumentos, expiracao e versao da politica.
            return result('AGUARDANDO_AUTORIZACAO', 'APPROVAL_REQUIRED',
                          'Requer aprovacao validada no backend V22', True)
        return result('PERMITIDO_PARA_DESPACHO', 'POLICY_ALLOW',
                      'Apenas leitura permitida; execucao requer adaptador MCP confiavel')
