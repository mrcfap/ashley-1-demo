"""Human-centered decision support. No external execution, diagnosis or inferred values."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List
import hashlib
import json

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

@dataclass
class HumanCharter:
    owner_id: str
    values: List[str]
    limits: Dict[str, float]
    version: int = 1
    consent: bool = False

class EloAgent:
    """Explicit conversational preferences; never infers emotional state."""
    MODES = {'conversa', 'solucao', 'reflexao', 'silencio'}
    def respond_mode(self, selected: str, consent: bool):
        if not consent: return {'status':'CONSENT_REQUIRED','mode':None}
        if selected not in self.MODES: return {'status':'INVALID_MODE','mode':None}
        return {'status':'OK','mode':selected,'action':'NO_AUTOMATIC_EXECUTION'}

class HorizonteVivoAgent:
    """Compares user-provided scenarios, without fabricating forecasts."""
    def compare(self, options: List[dict], constraints: Dict[str,float]):
        results=[]
        for item in options:
            name=item.get('name','')
            costs=item.get('metrics',{})
            if not name or not isinstance(costs,dict): raise ValueError('Invalid scenario')
            violations=[key for key,limit in constraints.items() if key in costs and costs[key]>limit]
            missing=[key for key in constraints if key not in costs]
            results.append({'name':name,'within_limits':not violations and not missing,
                            'violations':violations,'missing_evidence':missing})
        return {'scenarios':results,'decision':'USER_REQUIRED'}

class EssentiaAgent:
    """Checks declared priorities against explicit plan metadata, not personal worth."""
    def assess(self, charter: HumanCharter, plan: dict):
        if not charter.consent: return {'status':'CONSENT_REQUIRED'}
        if not charter.owner_id: raise ValueError('Owner required')
        metrics=plan.get('metrics',{})
        if not isinstance(metrics,dict): raise ValueError('Invalid metrics')
        conflicts=[{'metric':key,'limit':limit,'proposed':metrics[key]} for key,limit in charter.limits.items()
                   if key in metrics and metrics[key]>limit]
        unknown=[key for key in charter.limits if key not in metrics]
        return {'status':'REVIEW_REQUIRED' if conflicts or unknown else 'ALIGNED_WITH_DECLARED_LIMITS',
                'conflicts':conflicts,'missing_metrics':unknown,'charter_version':charter.version,
                'charter_digest':digest({'owner':charter.owner_id,'values':charter.values,'limits':charter.limits,'version':charter.version}),
                'decision':'USER_REQUIRED','timestamp':datetime.now(timezone.utc).isoformat()}

class HumanFoundation:
    """Coordinates three advisors without overriding existing authorization layers."""
    def __init__(self):
        self.elo=EloAgent();self.horizonte=HorizonteVivoAgent();self.essentia=EssentiaAgent()
    def review(self, charter: HumanCharter, mode: str, options: List[dict]):
        return {'elo':self.elo.respond_mode(mode,charter.consent),
                'horizonte':self.horizonte.compare(options,charter.limits),
                'essentia':[self.essentia.assess(charter,option) for option in options],
                'execution_authorized':False}
