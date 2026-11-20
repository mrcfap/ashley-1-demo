"""Evolução contínua supervisionada: observação -> proposta -> revisão.

Não executa código gerado, não modifica a aplicação e não acessa rede.
A integração ao agendador é opt-in e deve ocorrer em processo controlado.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re

from app.evolution.governed_evolution import propose

ROLES = ("observador", "analista", "arquiteto", "etica_privacidade", "testador", "revisor_humano")
PROTECTED = ("auth", "security", "credential", "secret", "permission", "governance", "governed_evolution", "self_coding", ".env", "database", "postgres")


@dataclass(frozen=True)
class EvolutionCandidate:
    identifier: str
    component: str
    observation: str
    hypothesis: str
    expected_benefit: str
    test_plan: str
    risk: str
    status: str
    created_at: str
    roles: tuple[str, ...] = ROLES


class ContinuousEvolution:
    """Registra candidatos auditáveis; toda promoção depende de processo externo."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.store = self.root / ".ashley_evolution_reviews"

    @staticmethod
    def _validate_text(value: str, name: str, limit: int = 4000) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError(f"{name} inválido")
        return value.strip()

    def observe(self, component: str, observation: str, hypothesis: str,
                expected_benefit: str, test_plan: str, risk: str = "medium") -> dict:
        component = self._validate_text(component, "component", 120)
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", component):
            raise ValueError("Componente inválido")
        if any(word in component.lower() for word in PROTECTED):
            raise PermissionError("Componente protegido exige análise manual externa")
        observation = self._validate_text(observation, "observation")
        hypothesis = self._validate_text(hypothesis, "hypothesis")
        expected_benefit = self._validate_text(expected_benefit, "expected_benefit")
        test_plan = self._validate_text(test_plan, "test_plan")
        if risk not in ("low", "medium", "high", "critical"):
            raise ValueError("Risco inválido")
        digest = sha256(json.dumps([component, observation, hypothesis, expected_benefit, test_plan], ensure_ascii=False).encode()).hexdigest()[:20]
        candidate = EvolutionCandidate(digest, component, observation, hypothesis,
                                       expected_benefit, test_plan, risk,
                                       "pending_human_review", datetime.now(timezone.utc).isoformat())
        self.store.mkdir(parents=True, exist_ok=True)
        path = self.store / (digest + ".json")
        if not path.exists():
            with path.open("x", encoding="utf-8") as f:
                json.dump(asdict(candidate), f, ensure_ascii=False, indent=2)
        return json.loads(path.read_text(encoding="utf-8"))

    def prepare_code_proposal(self, target: str, rationale: str, patch: str) -> dict:
        """Apenas prepara proposta: não aplica o patch."""
        if any(word in target.lower() for word in PROTECTED):
            raise PermissionError("Alvo protegido")
        item = propose(target, rationale, patch, author="continuous_evolution")
        return asdict(item)

    def list_pending(self) -> list[dict]:
        if not self.store.exists():
            return []
        results = []
        for path in sorted(self.store.glob("*.json")):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
                if item.get("status") == "pending_human_review":
                    results.append(item)
            except (OSError, ValueError):
                continue
        return results
