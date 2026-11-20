"""Ledger experimental de decisões auditáveis da Axyntora.

Não coleta dados automaticamente, não toma decisões e não executa ações.
O chamador escolhe o que registrar; não armazene segredos ou dados pessoais.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any


class LedgerIntegrityError(ValueError):
    pass


def _canonical(data: dict[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


class DecisionLedger:
    """Log local JSONL encadeado por hashes, sem autenticação criptográfica.

    Uso experimental. Armazenamento em disco confiável é responsabilidade
    do operador. Não é imutável contra um administrador malicioso.
    """
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def verify(self) -> dict[str, Any]:
        previous = "GENESIS"
        count = 0
        if not self.path.exists():
            return {"valid": True, "count": 0, "last_hash": previous}
        with self.path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    if not isinstance(entry, dict):
                        raise ValueError("registro não é objeto")
                    digest = entry.pop("hash")
                    if entry.get("previous_hash") != previous:
                        raise LedgerIntegrityError("cadeia de hashes interrompida")
                    calculated = sha256(_canonical(entry)).hexdigest()
                    if digest != calculated:
                        raise LedgerIntegrityError("conteúdo alterado")
                    previous = digest
                    count += 1
                except (ValueError, KeyError, TypeError) as exc:
                    raise LedgerIntegrityError(f"Registro {line_number} inválido: {exc}") from exc
        return {"valid": True, "count": count, "last_hash": previous}

    def record(self, *, case_id: str, decision: str, evidence_refs: list[str],
               approved_by: str | None = None, status: str = "proposed") -> dict[str, Any]:
        """Registra metadados mínimos; não registra texto integral de evidências."""
        if status not in {"proposed", "approved", "rejected", "executed"}:
            raise ValueError("status inválido")
        if status in {"approved", "executed"} and not approved_by:
            raise ValueError("aprovação humana exigida para esse status")
        if not case_id.strip() or not decision.strip():
            raise ValueError("case_id e decision são obrigatórios")
        if not isinstance(evidence_refs, list) or any(not isinstance(v, str) for v in evidence_refs):
            raise ValueError("evidence_refs deve ser lista de strings")
        # Em implantação concorrente, adicionar lock transacional por processo/host.
        state = self.verify()
        entry = {
            "schema_version": 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "case_id": case_id,
            "decision": decision,
            "evidence_refs": evidence_refs,
            "approved_by": approved_by,
            "status": status,
            "previous_hash": state["last_hash"],
        }
        entry["hash"] = sha256(_canonical(entry)).hexdigest()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(_canonical(entry).decode("utf-8") + "\n")
            f.flush()
            os.fsync(f.fileno())
        return entry
