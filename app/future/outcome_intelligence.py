"""Motor experimental: aprendizado por resultados observáveis.

Não executa tarefas, não altera modelos e não coleta dados sem chamada explícita.
Usar identificadores pseudônimos e evitar dados pessoais nos eventos.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
import os

@dataclass(frozen=True)
class OutcomeEvent:
    goal_id: str
    metric: str
    predicted: float
    observed: Optional[float] = None
    evidence_ref: str = ""
    approved: bool = False
    timestamp: str = ""

    def validate(self) -> None:
        if not self.goal_id or not self.metric:
            raise ValueError("goal_id e metric são obrigatórios")
        if not self.approved:
            raise PermissionError("Registro requer autorização explícita")
        if self.observed is not None and not self.evidence_ref:
            raise ValueError("Resultado observado requer referência de evidência")
        for value in (self.predicted, self.observed):
            if value is not None:
                import math
                if not math.isfinite(value):
                    raise ValueError("Métricas devem ser finitas")

class OutcomeTracker:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def record(self, event: OutcomeEvent) -> dict:
        event.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(event)
        payload["timestamp"] = event.timestamp or datetime.now(timezone.utc).isoformat()
        # O arquivo não deve conter segredos ou dados sensíveis.
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return payload

    def summary(self, goal_id: str) -> dict:
        entries = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("goal_id") == goal_id and item.get("observed") is not None:
                    entries.append(item)
        return {"goal_id": goal_id, "observations": len(entries),
                "mean_absolute_error": (sum(abs(e["observed"] - e["predicted"]) for e in entries) / len(entries)) if entries else None}
