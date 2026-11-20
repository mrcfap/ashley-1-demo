"""V100 supervised deliberation: evidence-first, no arbitrary code execution/deployment.
Optional Ollama on loopback, opt-in per request. No background execution.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request
import urllib.error
from urllib.parse import urlparse
from . import core

ROLES = ('Ashley', 'Ashen', 'Auditor')

def _model_response(role: str, objective: str, evidence: list[dict], timeout: int) -> str:
    endpoint = os.environ.get('AXYNTORA_OLLAMA_URL', 'http://127.0.0.1:11434/api/chat')
    parsed = urlparse(endpoint)
    if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost') or parsed.port != 11434 or parsed.path != '/api/chat':
        raise ValueError('Ollama somente em http://127.0.0.1:11434/api/chat')
    model = os.environ.get('AXYNTORA_OLLAMA_MODEL', 'qwen3:1.7b')
    evidence_text = '\n'.join(f"[{i+1}] {s['title']}: {s['excerpt']}" for i, s in enumerate(evidence))
    instructions = {
        'Ashley': 'Produza um plano prÃ¡tico de investigaÃ§Ã£o e validaÃ§Ã£o. NÃ£o afirme que executou tarefas. Cite somente fontes fornecidas.',
        'Ashen': 'Analise criticamente o objetivo e as evidÃªncias. Identifique riscos, lacunas, hipÃ³teses alternativas e condiÃ§Ãµes de falha.',
        'Auditor': 'Diferencie fatos, hipÃ³teses e tarefas pendentes. NÃ£o declare execuÃ§Ã£o, testes, fontes verificadas ou aprovaÃ§Ã£o sem evidÃªncias.'
    }
    prompt = f"Objetivo: {objective}\nEvidÃªncias fornecidas (nÃ£o verificadas):\n{evidence_text or '(nenhuma)'}\nResponda em portuguÃªs em atÃ© 200 palavras."
    data = json.dumps({'model': model, 'stream': False, 'think': False,
                       'options': {'num_predict': 350, 'temperature': 0.2},
                       'messages': [{'role': 'system', 'content': instructions[role]},
                                    {'role': 'user', 'content': prompt}]}).encode()
    req = urllib.request.Request(endpoint, data=data, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        result = json.loads(response.read(128000))
    content = result.get('message', {}).get('content')
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Modelo local nÃ£o retornou conteÃºdo')
    return content.strip()[:5000]

def _sources(value):
    if value is None: return []
    if not isinstance(value, list) or len(value)>10: raise ValueError('sources: lista com atÃ© 10 fontes')
    result=[]
    for item in value:
        if not isinstance(item,dict): raise ValueError('Fonte invÃ¡lida')
        result.append({'title':core._require_text(item.get('title'),'source.title',160),
                       'excerpt':core._require_text(item.get('excerpt'),'source.excerpt',1500),
                       'verified_externally':False})
    return result

def deliberate(user, mission_id, data):
    mission = core._get(user, 'mission', mission_id)
    if not mission: raise KeyError('MissÃ£o nÃ£o encontrada')
    if mission.get('status') not in ('proposed', 'deliberated'):
        raise ValueError('Estado da missÃ£o nÃ£o permite deliberaÃ§Ã£o')
    if data.get('consent') is not True:
        raise ValueError('consent: autorizaÃ§Ã£o explÃ­cita obrigatÃ³ria')
    sources = _sources(data.get('sources', []))
    use_model = data.get('use_local_model', False)
    if not isinstance(use_model,bool): raise ValueError('use_local_model deve ser booleano')
    if len(str(data)) > 25000: raise ValueError('Dados excedem limite')
    objective=mission['objective']
    selected=list(mission['selected_engines'])
    ids={e['id'] for e in selected}
    # Mission-specific dependency selection; explicit, auditable rules, not semantic AI.
    if any(w in objective.casefold() for w in ('lentid', 'latÃªncia', 'resposta', 'cÃ³digo', 'corrig', 'bug', 'otimiz')):
        if 'V99' not in ids:
            selected.append({'id':'V99','name':core.NAMES[99], 'matched_terms':['regra_de_diagnostico'],
                             'executed':False,'selection_method':'supervised_diagnostic_rule'})
    if 'V98' not in ids:
        selected.append({'id':'V98','name':core.NAMES[98], 'matched_terms':['evidence_first'],
                         'executed':False,'selection_method':'supervised_evidence_rule'})
    gaps=['MÃ©tricas de latÃªncia, logs e testes de regressÃ£o ainda nÃ£o fornecidos'] if 'lentid' in objective.casefold() else []
    if not sources: gaps.append('Nenhuma evidÃªncia fornecida; hipÃ³teses nÃ£o confirmadas')
    report={'mode':'offline_rules','roles_executed':False,
            'Ashley':{'proposal':'Coletar evidÃªncias, medir situaÃ§Ã£o atual e propor uma alteraÃ§Ã£o mÃ­nima verificÃ¡vel.',
                      'next_steps':['Obter logs e mÃ©tricas','Formular hipÃ³teses','Preparar plano de teste']},
            'Ashen':{'critique':'Sem mediÃ§Ãµes comparativas nÃ£o Ã© possÃ­vel afirmar a causa ou eficÃ¡cia de uma correÃ§Ã£o.',
                     'risks':['RegressÃµes funcionais','ConclusÃµes sem evidÃªncias','AlteraÃ§Ãµes em produÃ§Ã£o sem aprovaÃ§Ã£o']},
            'Auditor':{'finding':'Planejamento apenas; nenhum cÃ³digo executado ou alterado.',
                       'missing_evidence':gaps}}
    if use_model:
        report['mode']='local_ollama'
        # Each role gets independent context, not a claim of autonomous background agents.
        try:
            for role in ROLES:
                report[role]={'text':_model_response(role,objective,sources,90)}
            report['roles_executed']=True
        except (OSError,ValueError,TimeoutError,urllib.error.URLError,json.JSONDecodeError) as exc:
            report['mode']='offline_rules_fallback'
            report['model_error']=type(exc).__name__
            report['roles_executed']=False
    output={'mission_id':mission_id,'objective':objective,'selected_engines':selected,
            'evidence':sources,'evidence_verified_externally':False,
            'deliberation':report,'status':'deliberated', 'requires_human_approval':True,
            'execution_authorized':False,'production_modified':False,
            'tools_executed':bool(report['roles_executed']),
            'decision_trace':[{'time':core.now(),'event':'supervised_deliberation',
                               'detail':report['mode']}]}
    result=core._record(user,'deliberation',output)
    # Update mission without changing execution flags.
    with core._LOCK,core.connect() as db:
        row=db.execute('SELECT payload FROM records WHERE id=? AND user_id=? AND kind=?',
                       (mission_id,str(user),'mission')).fetchone()
        if not row: raise KeyError('MissÃ£o nÃ£o encontrada')
        stored=json.loads(row['payload'])
        stored['status']='deliberated';stored['last_deliberation_id']=result['id']
        stored['decision_trace'].append({'time':core.now(),'event':'deliberated',
                                         'detail':report['mode']})
        db.execute('UPDATE records SET payload=? WHERE id=? AND user_id=? AND kind=?',
                   (json.dumps(stored,ensure_ascii=False),mission_id,str(user),'mission'))
    return result

def report(user, mission_id):
    mission=core._get(user,'mission',mission_id)
    if not mission: raise KeyError('MissÃ£o nÃ£o encontrada')
    did=mission.get('last_deliberation_id')
    return {'mission':mission,'last_deliberation':core._get(user,'deliberation',did) if did else None,
            'external_actions_enabled':False,'deployment_authorized':False}
