"""Axyntora trust layer: deterministic, local, policy-oriented reference implementation.
No external actions, medical inference, legal certification, or autonomous elevation of permissions.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

class PolicyError(ValueError):
    pass

def digest(data: dict) -> str:
    return sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()

class Provenance:
    """Manifest with source identifiers and content digests, not a cryptographic certificate."""
    @staticmethod
    def manifest(tenant: str, artifact_id: str, content: bytes, sources: list[str], actor: str) -> dict:
        if not all([tenant, artifact_id, actor]) or not isinstance(content, bytes):
            raise PolicyError('Identidade, artefato, ator e bytes são obrigatórios')
        record = {'tenant':tenant,'artifact_id':artifact_id,'content_sha256':sha256(content).hexdigest(),
                  'sources':list(sources),'actor':actor,'created_at':datetime.now(timezone.utc).isoformat()}
        return {**record,'manifest_sha256':digest(record)}
    @staticmethod
    def verify(manifest: dict, content: bytes) -> bool:
        data={k:v for k,v in manifest.items() if k!='manifest_sha256'}
        return (sha256(content).hexdigest()==manifest.get('content_sha256') and
                digest(data)==manifest.get('manifest_sha256'))

LEVELS=('suggest','approve','execute_notify')
@dataclass
class Covenant:
    tenant: str
    task_class: str
    allowed_tools: set[str]
    budget_limit: float
    expires_at: datetime
    level: str='suggest'
    success_count: int=0
    failures: int=0
    max_level: str='approve'
    promotion_threshold: int=3
    history: list[dict]=field(default_factory=list)

    def authorize(self, tenant: str, tool: str, amount: float, now: datetime|None=None, human_approved: bool=False) -> dict:
        now=now or datetime.now(timezone.utc)
        if now.tzinfo is None or self.expires_at.tzinfo is None:raise PolicyError('Datas precisam de fuso horário')
        if tenant!=self.tenant or now>=self.expires_at or tool not in self.allowed_tools or amount<0 or amount>self.budget_limit:
            return {'allowed':False,'reason':'scope_or_budget_or_expiry'}
        if self.level=='suggest':return {'allowed':False,'reason':'suggest_only'}
        if self.level=='approve' and not human_approved:return {'allowed':False,'reason':'human_approval_required'}
        return {'allowed':True,'reason':'authorized','notify':self.level=='execute_notify'}

    def record_outcome(self, verified: bool, success: bool, severe: bool=False) -> str:
        if not verified:raise PolicyError('Resultado não verificado não altera autonomia')
        if severe or not success:
            self.failures+=1;self.success_count=0;self.level='suggest'
        else:
            self.success_count+=1
            if self.success_count>=self.promotion_threshold:
                next_level=min(LEVELS.index(self.level)+1,LEVELS.index(self.max_level))
                self.level=LEVELS[next_level];self.success_count=0
        self.history.append({'verified':verified,'success':success,'severe':severe,'level':self.level})
        return self.level

class ProceduralMemory:
    """In-memory tenant-scoped skill registry. Requires independent test evidence."""
    def __init__(self):self._skills={}
    def register(self, tenant:str, name:str, version:int, steps:list[str], tests_passed:bool, approved:bool):
        if not tenant or not name or version<1 or not steps or not tests_passed or not approved:
            raise PolicyError('Habilidade exige escopo, revisão e regressão aprovada')
        key=(tenant,name,version)
        if key in self._skills:raise PolicyError('Versão já existe')
        self._skills[key]={'steps':tuple(steps),'status':'active'}
    def recall(self, tenant:str, name:str, version:int, covenant:Covenant, tool:str, amount:float, human_approved:bool=False):
        key=(tenant,name,version);skill=self._skills.get(key)
        if not skill or skill['status']!='active':raise PolicyError('Habilidade ausente ou obsoleta')
        decision=covenant.authorize(tenant,tool,amount,human_approved=human_approved)
        if not decision['allowed']:raise PolicyError(decision['reason'])
        return list(skill['steps'])
    def deprecate(self,tenant:str,name:str,version:int):
        self._skills[(tenant,name,version)]['status']='deprecated'

class Anima:
    """Only explicit opt-in and declared preferences; no emotional or clinical inference."""
    @staticmethod
    def calibrate(consent:bool, declared_load:str|None, base_level:str, user_requested_review:bool=False)->dict:
        if base_level not in LEVELS:raise PolicyError('Nível desconhecido')
        if not consent:return {'level':base_level,'reason':'no_personalization','stored_state':None}
        if declared_load not in (None,'normal','high'):raise PolicyError('Estado deve ser declarado')
        if declared_load=='high' or user_requested_review:
            level=LEVELS[max(0,LEVELS.index(base_level)-1)]
            return {'level':level,'reason':'user_declared_preference','stored_state':declared_load,'contestable':True}
        return {'level':base_level,'reason':'no_change','stored_state':declared_load,'contestable':True}
    @staticmethod
    def impact_record(tenant:str, mission:str, consent:bool, adjustment:dict, observed:dict)->dict:
        return {'tenant':tenant,'mission':mission,'consent':consent,'adjustment':adjustment,
                'observed':observed if consent else {},'timestamp':datetime.now(timezone.utc).isoformat()}

class Vinculum:
    """Explicit user-controlled charter and task promises, without emotional debt scoring."""
    def __init__(self):self._charters={};self._promises={}
    def charter(self, tenant:str, user:str, preferences:dict, consent:bool):
        if not consent:raise PolicyError('Consentimento obrigatório')
        key=(tenant,user);old=self._charters.get(key,{});version=old.get('version',0)+1
        self._charters[key]={'version':version,'preferences':dict(preferences)}
        return version
    def read(self,tenant:str,user:str):return self._charters.get((tenant,user))
    def promise(self,tenant:str,user:str,promise_id:str,description:str,confirmed:bool):
        if not confirmed or not description:raise PolicyError('Promessa precisa de confirmação explícita')
        key=(tenant,user,promise_id)
        if key in self._promises:raise PolicyError('Promessa duplicada')
        self._promises[key]={'description':description,'status':'open'}
    def resolve(self,tenant:str,user:str,promise_id:str):self._promises[(tenant,user,promise_id)]['status']='done'
    def outstanding(self,tenant:str,user:str):
        return {k[2]:dict(v) for k,v in self._promises.items() if k[:2]==(tenant,user) and v['status']=='open'}
    def erase(self,tenant:str,user:str):
        self._charters.pop((tenant,user),None)
        for key in list(self._promises):
            if key[:2]==(tenant,user):del self._promises[key]
