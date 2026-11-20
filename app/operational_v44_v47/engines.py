"""Ashley V44-V47: analogia verificável, resiliência, governança e decisão orientada a resultados.
Sem autoedição, execução de ações sensíveis ou promessas de consciência.
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from collections import deque
from typing import Any, Callable, Awaitable
import logging
import time
import re

log = logging.getLogger('ashley.v44_v47')

class SinapseEngineV44:
    """Mapeia padrões declarados entre domínios; analogias são hipóteses, nunca fatos."""
    DOMAINS = {'codigo', 'casos', 'musica', 'gestao', 'pesquisa', 'geral'}
    PATTERNS = {
        'decomposicao': ('dividir em etapas', 'definir entradas e saídas', 'validar cada etapa'),
        'feedback': ('registrar resultado', 'comparar com objetivo', 'ajustar próxima tentativa'),
        'dependencias': ('identificar pré-requisitos', 'ordenar tarefas', 'verificar bloqueios'),
        'variacao': ('propor alternativas', 'comparar critérios', 'selecionar opção justificada'),
    }
    def transfer_analogical_context_sync(self, source_domain: str, target_domain: str, context_data: dict[str, Any]) -> dict[str, Any]:
        src = str(source_domain).lower().strip()
        dst = str(target_domain).lower().strip()
        if src not in self.DOMAINS or dst not in self.DOMAINS:
            return {'status':'invalid_domain','analogies':[], 'requires_validation':True}
        supplied = context_data.get('patterns', [])
        if not isinstance(supplied, list):
            supplied = []
        matched = [p for p in supplied if isinstance(p,str) and p in self.PATTERNS]
        analogies = [{'pattern':p, 'steps':list(self.PATTERNS[p]), 'source':src, 'target':dst,
                      'note':'Hipótese de transferência; validar no domínio de destino.'} for p in matched[:4]]
        return {'status':'success','source':src,'target':dst,'analogies':analogies,
                'requires_validation':True,'applied':False}
    async def transfer_analogical_context(self, source_domain: str, target_domain: str, context_data: dict[str,Any]) -> dict[str,Any]:
        return self.transfer_analogical_context_sync(source_domain,target_domain,context_data)

class NexusEngineV45:
    """Isolamento de falhas, timeout, limite de concorrência e circuito por serviço."""
    def __init__(self, max_concurrency:int=8, failure_threshold:int=3, cooldown_seconds:float=30.0):
        self._sem=asyncio.Semaphore(max_concurrency)
        self._failure_threshold=max(1,failure_threshold)
        self._cooldown=max(0.1,cooldown_seconds)
        self._failures:dict[str,int]={}
        self._open_until:dict[str,float]={}
        self._active=0
        self._recent=deque(maxlen=100)
    async def execute_safe_async(self, coro_or_factory: Any, fallback_value:Any=None, timeout:float=10.0,
                                 service:str='default', retries:int=0) -> Any:
        # Factory is needed for retries: a coroutine instance cannot be awaited twice.
        now=time.monotonic()
        if self._open_until.get(service,0)>now:
            if asyncio.iscoroutine(coro_or_factory): coro_or_factory.close()
            return fallback_value
        async with self._sem:
            self._active+=1
            try:
                for attempt in range(max(0,min(retries,2))+1):
                    try:
                        awaitable=coro_or_factory() if callable(coro_or_factory) else coro_or_factory
                        result=await asyncio.wait_for(awaitable, timeout=max(0.01,timeout))
                        self._failures[service]=0
                        return result
                    except asyncio.CancelledError:
                        raise
                    except (TimeoutError, ConnectionError, OSError) as exc:
                        self._recent.append({'service':service,'kind':type(exc).__name__})
                        if attempt<retries and callable(coro_or_factory):
                            await asyncio.sleep(min(0.5*(2**attempt),2.0))
                            continue
                        break
                    except Exception as exc:
                        self._recent.append({'service':service,'kind':type(exc).__name__})
                        log.exception('V45 failure in service=%s',service)
                        break
                count=self._failures.get(service,0)+1
                self._failures[service]=count
                if count>=self._failure_threshold:
                    self._open_until[service]=time.monotonic()+self._cooldown
                return fallback_value
            finally:
                self._active-=1
    def get_health_status(self)->dict[str,Any]:
        now=time.monotonic()
        open_services=[k for k,v in self._open_until.items() if v>now]
        return {'status':'DEGRADED' if open_services else 'HEALTHY',
                'active_tasks_count':self._active,'open_circuits':open_services,
                'recent_error_count':len(self._recent)}

@dataclass(frozen=True)
class AxiomPolicy:
    protected_actions:frozenset[str]=frozenset({'modify_code','deploy','delete_data','change_permissions',
                                               'send_message','financial_transaction','external_write'})
    forbidden_actions:frozenset[str]=frozenset({'bypass_auth','disable_audit','exfiltrate_secrets'})

class AxiomEngineV46:
    """Decisões estruturadas. A política não pode ser alterada por texto de prompt."""
    def __init__(self,policy:AxiomPolicy|None=None):
        self._policy=policy or AxiomPolicy()
    def validate_action_alignment(self,proposed_action:dict[str,Any])->dict[str,Any]:
        kind=str(proposed_action.get('type','unknown')).lower().strip()
        approved=proposed_action.get('approved_by_user') is True
        description=str(proposed_action.get('description',''))
        # Defense-in-depth: texto livre jamais concede permissões.
        if kind in self._policy.forbidden_actions:
            return {'aligned':False,'decision':'deny','reason':'Ação proibida','action':kind}
        if kind in self._policy.protected_actions and not approved:
            return {'aligned':False,'decision':'requires_approval','reason':'Requer aprovação explícita','action':kind}
        if kind=='unknown':
            return {'aligned':False,'decision':'requires_review','reason':'Tipo de ação não reconhecido','action':kind}
        return {'aligned':True,'decision':'allow','reason':'Ação compatível com política local; demais verificações continuam necessárias','action':kind}

class MaestriaEngineV47:
    """V47 MAESTRIA: transforma intenção em plano verificável, evidência e próximo passo consentido.
    Não executa ações, não cria objetivos próprios e não inventa resultados.
    """
    def __init__(self,axiom:AxiomEngineV46,sinapse:SinapseEngineV44):
        self.axiom=axiom;self.sinapse=sinapse
    def deliberate(self,request:str,*,domain:str='geral',evidence:list[dict]|None=None,
                   proposed_action:dict|None=None,source_domain:str|None=None)->dict[str,Any]:
        request=(request or '').strip()[:1500]
        if not request:
            return {'status':'insufficient_input','goal':'','next_step':'Pedir objetivo ao usuário','evidence':[]}
        items=[{'claim':str(e.get('claim',''))[:300], 'source':str(e.get('source',''))[:180]} for e in (evidence or [])[:5] if isinstance(e,dict) and e.get('source')]
        action=proposed_action or {'type':'respond','description':'Responder sem executar ações externas'}
        decision=self.axiom.validate_action_alignment(action)
        analogy=self.sinapse.transfer_analogical_context_sync(source_domain,domain,{'patterns':['decomposicao','feedback']}) if source_domain else None
        return {'status':'ready' if decision['aligned'] else 'review_required',
                'goal':request,'evidence':items,'evidence_verified':False,
                'action_decision':decision,'analogical_hypothesis':analogy,
                'next_step':'Solicitar autorização antes de executar' if not decision['aligned'] else 'Responder com plano, critério de sucesso e próximos passos',
                'success_criterion':'Resultado observável confirmado pelo usuário ou por ferramenta autorizada',
                'uncertainty':'Sem evidência externa verificada nesta etapa',
                'execution_performed':False}
    def instructions(self,result:dict[str,Any])->str:
        return ('V47 MAESTRIA: responda orientado ao objetivo declarado, separe fatos de hipóteses, '
                'indique critério verificável de sucesso e um próximo passo concreto. '
                'Não afirme ter executado ações, comprovado evidências ou concluído tarefas sem confirmação. '
                'Ações externas e alterações sensíveis exigem autorização. '
                f"Decisão local: {result.get('action_decision',{}).get('decision','requires_review')}.")

class OperationalExcellenceSuite:
    def __init__(self):
        self.v44_sinapse=SinapseEngineV44()
        self.v45_nexus=NexusEngineV45()
        self.v46_axiom=AxiomEngineV46()
        self.v47_maestria=MaestriaEngineV47(self.v46_axiom,self.v44_sinapse)
    async def initialize(self)->dict[str,bool]:
        return {'v44_sinapse':True,'v45_nexus':True,'v46_axiom':True,'v47_maestria':True}
    def status(self)->dict[str,Any]:
        return {'registered':['V44 SINAPSE','V45 NEXUS','V46 AXIOM','V47 MAESTRIA'],
                'runtime':self.v45_nexus.get_health_status(),
                'note':'Registro e diagnóstico local não comprovam integrações externas.'}
