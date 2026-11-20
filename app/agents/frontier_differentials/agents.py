"""Three differentiated, bounded agents for Axyntora.
No external execution or unverified factual claims are made by these components.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List
import json


def _digest(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


class ParallaxAgent:
    """Structured independent-perspective challenge of proposed decisions."""
    ID = "FRONTIER_10"
    NAME = "PARALLAX"
    PERSPECTIVES = ("seguranca", "cliente", "operacao", "financeiro", "etica")

    def challenge(self, proposal: Dict[str, Any], assessments: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(proposal, dict) or not proposal.get("objective"):
            raise ValueError("Proposal must contain an objective")
        if not isinstance(assessments, dict):
            raise ValueError("Assessments must be a mapping")
        unknown = set(assessments) - set(self.PERSPECTIVES)
        if unknown:
            raise ValueError("Unknown perspectives: " + ','.join(sorted(unknown)))
        findings = []
        for perspective in self.PERSPECTIVES:
            assessment = assessments.get(perspective)
            if assessment is None:
                findings.append({"perspective": perspective, "status": "NOT_EVALUATED"})
                continue
            risk = assessment.get("risk")
            if not isinstance(risk, (int, float)) or isinstance(risk, bool) or not 0 <= risk <= 1:
                raise ValueError("Risk must be between 0 and 1")
            findings.append({"perspective": perspective, "status": "EVALUATED", "risk": risk,
                             "evidence": assessment.get("evidence", [])})
        high = [f["perspective"] for f in findings if f.get("risk", 0) >= .7]
        missing = [f["perspective"] for f in findings if f["status"] == "NOT_EVALUATED"]
        result = {"agent": self.NAME, "proposal_id": _digest(proposal), "findings": findings,
                  "high_risk": high, "missing_perspectives": missing,
                  "recommendation": "HUMAN_REVIEW" if high or missing else "READY_FOR_EXTERNAL_VALIDATION",
                  "automatic_execution": False}
        result["record_hash"] = _digest(result)
        return result


class SeedbankAgent:
    """Tenant-scoped knowledge capsules, explicit grants, revocation and export."""
    ID = "FRONTIER_11"
    NAME = "SEEDBANK"

    def __init__(self):
        self._capsules: Dict[str, Dict[str, Any]] = {}
        self._audit: List[Dict[str, str]] = []

    def _event(self, action: str, capsule_id: str):
        self._audit.append({"action": action, "capsule_id": capsule_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()})

    def create(self, tenant_id: str, owner_id: str, content: Dict[str, Any], purpose: str) -> str:
        if not all(isinstance(x, str) and x.strip() for x in (tenant_id, owner_id, purpose)):
            raise ValueError("Tenant, owner and purpose required")
        if not isinstance(content, dict):
            raise ValueError("Content must be a dictionary")
        cid = _digest({"tenant": tenant_id, "owner": owner_id, "content": content,
                       "purpose": purpose, "index": len(self._capsules)})
        self._capsules[cid] = {"tenant": tenant_id, "owner": owner_id, "content": dict(content),
                               "purpose": purpose, "grants": set(), "revoked": False}
        self._event("CREATE", cid)
        return cid

    def grant(self, capsule_id: str, tenant_id: str, actor_id: str, recipient_id: str):
        c = self._authorize_owner(capsule_id, tenant_id, actor_id)
        if not recipient_id:
            raise ValueError("Recipient required")
        c["grants"].add(recipient_id)
        self._event("GRANT", capsule_id)

    def _authorize_owner(self, cid, tenant, actor):
        c = self._capsules.get(cid)
        if not c or c["revoked"] or c["tenant"] != tenant or c["owner"] != actor:
            raise PermissionError("Access denied")
        return c

    def read(self, capsule_id: str, tenant_id: str, actor_id: str) -> Dict[str, Any]:
        c = self._capsules.get(capsule_id)
        if not c or c["revoked"] or c["tenant"] != tenant_id or (actor_id != c["owner"] and actor_id not in c["grants"]):
            raise PermissionError("Access denied")
        self._event("READ", capsule_id)
        return {"content": dict(c["content"]), "purpose": c["purpose"], "capsule_id": capsule_id}

    def revoke(self, capsule_id: str, tenant_id: str, actor_id: str):
        c = self._authorize_owner(capsule_id, tenant_id, actor_id)
        c["revoked"] = True
        c["grants"].clear()
        self._event("REVOKE", capsule_id)

    def audit_events(self):
        return [dict(event) for event in self._audit]


class SymbiosisAgent:
    """Measure whether human users can perform tasks without the assistant."""
    ID = "FRONTIER_12"
    NAME = "SYMBIOSIS"

    def evaluate(self, task_id: str, baseline: Dict[str, Any], followup: Dict[str, Any]) -> Dict[str, Any]:
        if not task_id:
            raise ValueError("Task identifier required")
        for item in (baseline, followup):
            if not isinstance(item, dict):
                raise ValueError("Measurements must be dictionaries")
            for key in ("independent_success", "quality_score"):
                value = item.get(key)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                    raise ValueError(f"{key} must be between 0 and 1")
        change = round(followup["independent_success"] - baseline["independent_success"], 4)
        quality_change = round(followup["quality_score"] - baseline["quality_score"], 4)
        result = {"agent": self.NAME, "task_id": task_id,
                  "independence_change": change, "quality_change": quality_change,
                  "interpretation": "IMPROVED" if change > 0 and quality_change >= 0 else
                                    "MIXED_OR_UNCHANGED", "causal_claim": False,
                  "next_step": "Collect repeated independent assessments"}
        result["record_hash"] = _digest(result)
        return result
