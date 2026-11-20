"""Implementações determinísticas e auditáveis V85–V94; sem execução externa."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import Counter
from hashlib import sha256
import json, math, re, threading, time

NAMES = {85:'NeuroPlastic',86:'CausalWorld',87:'MetaForge',88:'CHRONOS',89:'EUREKA',90:'NeuroPulse',91:'PrivacyVault',92:'AffectiveBalance',93:'SwarmMesh',94:'PRISM'}
CAPABILITIES = {
 85:('consolidar memória validada','registrar fatos verificáveis'),
 86:('comparar cenários explícitos','avaliar contrafactuais'),
 87:('propor alterações de código','revisão humana obrigatória'),
 88:('acompanhar previsões e observações','calcular desvios'),
 89:('formular hipóteses','planejar coleta de evidências'),
 90:('selecionar processamento por evento','orçar recursos'),
 91:('minimizar dados','verificar política de privacidade'),
 92:('adaptar tom com consentimento','modular estilo'),
 93:('dividir tarefas em agentes lógicos','limitar paralelismo'),
 94:('compor capacidades','gerar plano de competências'),
}

class MemoryStore:
    """Estado volátil por usuário, limitado; nunca misturar usuários."""
    def __init__(self):
        self._lock=threading.RLock(); self._data={}
    def append(self, uid, category, value, limit=100):
        with self._lock:
            key=(str(uid),category)
            self._data.setdefault(key,[]).append(value)
            self._data[key]=self._data[key][-limit:]
            return len(self._data[key])
    def read(self, uid, category):
        with self._lock: return list(self._data.get((str(uid),category),[]))
STORE=MemoryStore()

def _now(): return datetime.now(timezone.utc).isoformat()
def _words(s): return set(re.findall(r'\w+',s.casefold()))
def _bounded(s,n=1000): return str(s).strip()[:n]

def run(engine:int, action:str, data:dict, uid:str)->dict:
    if engine not in NAMES: raise ValueError('Motor inexistente')
    if not isinstance(data,dict): raise ValueError('Dados inválidos')
    base={'engine':f'V{engine}', 'name':NAMES[engine], 'action':action, 'user_id':str(uid),
          'mode':'supervised_local_prototype','external_actions':False,'autonomous_execution':False}
    result={}
    if engine==85:
        if action=='consolidate':
            if not data.get('verified') or not data.get('consent'): raise ValueError('Consolidação exige verificação e consentimento')
            fact=_bounded(data.get('fact',''))
            if len(fact)<3: raise ValueError('Fato inválido')
            result={'stored':True,'count':STORE.append(uid,'verified_facts',{'fact':fact,'at':_now()}),'weight_updates':False}
        elif action=='status': result={'facts':len(STORE.read(uid,'verified_facts')),'weight_updates':False,'persistent':False}
        else: raise ValueError('Ação inválida')
    elif engine==86:
        if action!='simulate': raise ValueError('Ação inválida')
        scenarios=data.get('scenarios',[])
        if not isinstance(scenarios,list) or not 1<=len(scenarios)<=12: raise ValueError('Forneça 1 a 12 cenários')
        rows=[]
        for s in scenarios:
            if not isinstance(s,dict): raise ValueError('Cenário inválido')
            p=float(s.get('probability',0));impact=float(s.get('impact',0))
            if not math.isfinite(p) or not 0<=p<=1 or not math.isfinite(impact) or abs(impact)>1e9: raise ValueError('Parâmetros fora dos limites')
            rows.append({'name':_bounded(s.get('name','cenário'),100),'expected_value':round(p*impact,4),'probability':p})
        result={'scenarios':rows,'best_by_expected_value':max(rows,key=lambda x:x['expected_value'])['name'],'causal_model_trained':False,'assumptions_user_supplied':True}
    elif engine==87:
        if action!='propose': raise ValueError('Ação inválida')
        issue=_bounded(data.get('issue',''))
        if not issue: raise ValueError('Informe o problema')
        result={'proposal':{'issue':issue,'required_checks':['unit_tests','integration_tests','security_review','human_approval'],'status':'draft'},'code_executed':False,'formal_proof':False,'deployment':False}
    elif engine==88:
        if action=='commit':
            goal=_bounded(data.get('goal',''));expected=data.get('expected')
            if not goal or not isinstance(expected,(int,float)) or not math.isfinite(expected): raise ValueError('Objetivo e previsão numérica necessários')
            ident=sha256(f'{uid}:{time.time_ns()}:{goal}'.encode()).hexdigest()[:16]
            STORE.append(uid,'commitments',{'id':ident,'goal':goal,'expected':expected,'observed':None})
            result={'id':ident,'recorded':True,'persistent':False}
        elif action=='observe':
            ident=data.get('id'); observed=data.get('observed')
            if not isinstance(observed,(int,float)) or not math.isfinite(observed): raise ValueError('Observação numérica inválida')
            with STORE._lock:
                matches=[x for x in STORE._data.get((str(uid),'commitments'),[]) if x['id']==ident]
                if not matches: raise ValueError('Compromisso não encontrado')
                matches[0]['observed']=observed
                result={'id':ident,'deviation':round(observed-matches[0]['expected'],6),'observation_user_supplied':True}
        elif action=='status': result={'commitments':STORE.read(uid,'commitments')}
        else: raise ValueError('Ação inválida')
    elif engine==89:
        if action!='investigate': raise ValueError('Ação inválida')
        question=_bounded(data.get('question',''))
        if not question: raise ValueError('Informe a questão')
        result={'question':question,'hypotheses':[_bounded(x,200) for x in data.get('hypotheses',[])[:5] if isinstance(x,str)],'investigation_steps':['definir evidências observáveis','identificar fonte autorizada','coletar medições','comparar hipóteses','registrar incertezas'],'research_performed':False}
    elif engine==90:
        if action!='budget': raise ValueError('Ação inválida')
        cost=float(data.get('estimated_cost_ms',0));budget=float(data.get('budget_ms',1000))
        if not all(map(math.isfinite,[cost,budget])) or cost<0 or budget<=0: raise ValueError('Orçamento inválido')
        result={'trigger':bool(data.get('event_changed',False)),'within_budget':cost<=budget,'budget_ms':budget,'estimated_cost_ms':cost,'energy_measured':False,'neuromorphic_hardware':False}
    elif engine==91:
        if action!='assess': raise ValueError('Ação inválida')
        fields=data.get('fields',[])
        if not isinstance(fields,list) or len(fields)>100: raise ValueError('Campos inválidos')
        sensitive={'password','token','secret','health','medical','cpf','email','biometric','finance'}
        flagged=[str(f)[:60] for f in fields if isinstance(f,str) and _words(f)&sensitive]
        result={'sensitive_fields':flagged,'requires_explicit_consent':bool(flagged),'recommended_controls':['data_minimization','access_control','encryption_at_rest','retention_policy'],'encrypted_inference':False,'zk_proof':False,'absolute_privacy_claim':False}
    elif engine==92:
        if action!='modulate': raise ValueError('Ação inválida')
        if not data.get('consent'): raise ValueError('Consentimento necessário')
        signal=str(data.get('user_preference','neutral')).lower()
        tone=signal if signal in ('neutral','calm','direct','supportive') else 'neutral'
        result={'tone':tone,'emotion_detection':False,'biometrics_used':False,'simulated_state':{'load':min(1,max(0,float(data.get('load',0))))}}
    elif engine==93:
        if action!='partition': raise ValueError('Ação inválida')
        tasks=data.get('tasks',[])
        if not isinstance(tasks,list) or not 1<=len(tasks)<=20: raise ValueError('Forneça 1 a 20 tarefas')
        result={'agents':[{'id':i+1,'task':_bounded(t,300),'status':'planned'} for i,t in enumerate(tasks)],'parallel_execution':False,'peer_to_peer':False}
    elif engine==94:
        if action!='compose': raise ValueError('Ação inválida')
        objective=_bounded(data.get('objective',''))
        if not objective: raise ValueError('Informe o objetivo')
        requested=data.get('engines',[])
        if not isinstance(requested,list) or len(requested)>10: raise ValueError('Seleção inválida')
        selected=[]
        for n in requested:
            try: k=int(str(n).upper().removeprefix('V'))
            except ValueError: raise ValueError('Motor inválido')
            if k not in NAMES: raise ValueError('Motor não registrado')
            if k!=94 and k not in selected: selected.append(k)
        result={'objective':objective,'steps':[{'engine':f'V{k}','capability':CAPABILITIES[k][0],'status':'proposed'} for k in selected],'requires_human_review':True,'executed':False}
    return {**base,**result}

def catalog():
    return [{'id':f'V{i}','name':name,'capabilities':CAPABILITIES[i],'status':'functional_limited_prototype','requires_authentication':True} for i,name in NAMES.items()]
