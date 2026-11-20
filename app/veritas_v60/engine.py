"""V60: verificação de pós-condições com evidência independente e gates de aprovação."""
from dataclasses import dataclass, asdict
from hashlib import sha256
import json

@dataclass(frozen=True)
class Verdict:
    status: str
    verified: bool
    reasons: tuple[str,...]
    evidence_digest: str | None

class VeritasV60:
    def evaluate(self, *, task_id: str, claimed_complete: bool, evidence: dict | None,
                 required_checks: list[str], approvals_required: bool = False,
                 approved: bool = False) -> dict:
        if not isinstance(task_id,str) or not task_id.strip(): raise ValueError('task_id obrigatório')
        if not isinstance(required_checks,list) or not required_checks or not all(isinstance(x,str) and x for x in required_checks):
            raise ValueError('required_checks obrigatório')
        reasons=[]
        if approvals_required and not approved: reasons.append('Aprovação humana pendente')
        if not claimed_complete: reasons.append('Executor não declarou conclusão')
        if not isinstance(evidence,dict):
            reasons.append('Sem evidências estruturadas'); evidence={}
        for name in required_checks:
            entry=evidence.get(name)
            if not isinstance(entry,dict) or entry.get('passed') is not True or not entry.get('proof'):
                reasons.append(f'Verificação não comprovada: {name}')
        digest=sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest() if evidence else None
        return asdict(Verdict('verified' if not reasons else 'blocked',not reasons,tuple(reasons),digest))
