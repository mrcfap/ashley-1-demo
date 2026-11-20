"""Integração opt-in entre agentes, prompts versionados e memória com escopo de usuário.
Não chama modelos, não executa ferramentas e não modifica código de produção.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

PROMPTS = {
    "observador": "Observe métricas e fatos verificáveis. Não invente resultados nem execute ações.",
    "analista": "Analise causas e incertezas. Separe evidências de hipóteses.",
    "arquiteto": "Proponha melhorias pequenas, reversíveis e compatíveis com a arquitetura.",
    "etica_privacidade": "Avalie consentimento, minimização de dados, direitos do usuário e riscos.",
    "testador": "Especifique testes reproduzíveis, casos adversos e critérios de aceitação.",
    "revisor_humano": "Prepare decisão para revisão humana. Nunca aprove mudanças automaticamente.",
}
PROMPT_VERSION = "1.0.0"
MAX_CONTEXT_ITEMS = 5

@dataclass(frozen=True)
class AgentContext:
    agent: str
    user_id: int
    prompt_version: str
    system_prompt: str
    memories: tuple[str, ...]
    review_required: bool = True

def build_context(agent: str, user_id: int, query: str, memory=None) -> AgentContext:
    if agent not in PROMPTS:
        raise ValueError("Agente desconhecido")
    if type(user_id) is not int or user_id <= 0:
        raise ValueError("Identificador de usuário inválido")
    if not isinstance(query, str) or len(query) > 2000:
        raise ValueError("Consulta inválida")
    excerpts = []
    if memory is not None:
        # A API existente exige user_id e aplica filtro no banco.
        results = memory.buscar(user_id=user_id, consulta=query, limite=MAX_CONTEXT_ITEMS)
        if not isinstance(results, list):
            raise ValueError("Resultado de memória inválido")
        for item in results[:MAX_CONTEXT_ITEMS]:
            if not isinstance(item, dict) or item.get("user_id") != user_id:
                raise PermissionError("Memória fora do escopo do usuário")
            content = item.get("conteudo", "")
            if isinstance(content, str):
                excerpts.append(content[:800])
    return AgentContext(agent, user_id, PROMPT_VERSION, PROMPTS[agent], tuple(excerpts))

def propose_with_context(project_root, context: AgentContext, component: str, observation: str,
                         hypothesis: str, benefit: str, test_plan: str, risk="medium") -> dict:
    from app.evolution.continuous_agent_architecture import ContinuousEvolution
    if not isinstance(context, AgentContext) or not context.review_required:
        raise PermissionError("Revisão humana obrigatória")
    engine = ContinuousEvolution(project_root)
    candidate = engine.observe(component, observation, hypothesis, benefit, test_plan, risk)
    # O registro guarda metadados, jamais conteúdos pessoais recuperados da memória.
    audit = Path(project_root).resolve() / ".ashley_evolution_reviews" / "agent_context_audit.jsonl"
    audit.parent.mkdir(parents=True, exist_ok=True)
    entry = {"candidate_id": candidate["identifier"], "agent": context.agent,
             "prompt_version": context.prompt_version, "user_scope_hash": sha256(str(context.user_id).encode()).hexdigest()[:12],
             "memory_items_used": len(context.memories), "status": "pending_human_review"}
    with audit.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return candidate
