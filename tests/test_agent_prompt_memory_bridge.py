from pathlib import Path
import pytest
from app.agents.agent_prompt_memory_bridge import build_context, propose_with_context, PROMPTS

class Memory:
    def buscar(self, user_id, consulta, limite):
        return [{"user_id": user_id, "conteudo": "Preferência autorizada"}]

class LeakyMemory:
    def buscar(self, user_id, consulta, limite):
        return [{"user_id": user_id + 1, "conteudo": "Dado de outra pessoa"}]

def test_all_agents_have_versioned_prompts():
    for agent in PROMPTS:
        ctx = build_context(agent, 12, "projeto", Memory())
        assert ctx.prompt_version == "1.0.0"
        assert ctx.memories == ("Preferência autorizada",)
        assert ctx.review_required

def test_cross_user_memory_rejected():
    with pytest.raises(PermissionError):
        build_context("analista", 12, "projeto", LeakyMemory())

def test_invalid_agent_and_user_rejected():
    with pytest.raises(ValueError): build_context("root", 12, "", Memory())
    with pytest.raises(ValueError): build_context("analista", 0, "", Memory())

def test_proposal_requires_human_review_and_no_memory_leak(tmp_path):
    ctx = build_context("analista", 12, "projeto", Memory())
    candidate = propose_with_context(tmp_path, ctx, "chat_latency", "resposta lenta", "gargalo", "menor latência", "medir p95")
    assert candidate["status"] == "pending_human_review"
    audit = (tmp_path / ".ashley_evolution_reviews" / "agent_context_audit.jsonl").read_text()
    assert "Preferência autorizada" not in audit
    assert "pending_human_review" in audit
