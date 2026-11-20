"""Router opcional, nao montado automaticamente na Ashley.

Conectar somente com dependencia de autenticacao REAL da aplicacao principal.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from .policy import PolicyRouter

router = APIRouter(prefix='/api/v1/mcp-governance', tags=['MCP Governance'])
_policy = PolicyRouter({})  # fail-closed por padrao; configurar pelo backend

class EvaluationRequest(BaseModel):
    tool_name: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)

# Nao declarar endpoint publico sem injetar a dependencia de autenticacao real.
# Exemplo de integracao: avaliar chamada via service interno com user_id validado.

def evaluate_authenticated(request: EvaluationRequest, authenticated_user: str):
    return _policy.evaluate(tool_name=request.tool_name,
                            arguments=request.arguments,
                            authenticated_user=authenticated_user)
