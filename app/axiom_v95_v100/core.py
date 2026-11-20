"""Functional limited prototypes V95-V100. No LLM, external tools, deployment or emotion diagnosis."""
from __future__ import annotations
import ast
import hashlib
import json
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

NAMES={95:'Empathy Core',96:'Proactive Engine',97:'Narrative Memory',98:'OMNIS RESEARCH',99:'GENESIS FORGE',100:'AION SYMPHONY'}
CAPABILITIES={
95:['explicit user preference-based tone','bounded TTS prosody suggestion'],
96:['user-authorized contextual suggestions','persistent proposals and deduplication'],
97:['user-supplied sourced timeline','revisable narrative summary'],
98:['evidence dossier from supplied sources','explicit contradiction and missing evidence'],
99:['sandbox-only code proposal','AST syntax review and human approval queue'],
100:['mission planning across engines','auditable decisions and lifecycle'],
}
DB_PATH=Path(os.environ.get('AXYNTORA_V100_DB',str(Path(__file__).resolve().parents[2]/'data'/'v95_v100.db')))
_LOCK=threading.RLock()
def now(): return datetime.now(timezone.utc).isoformat()
def connect():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(DB_PATH),timeout=10)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA busy_timeout=10000')
    db.executescript("""CREATE TABLE IF NOT EXISTS records (
       id TEXT PRIMARY KEY, user_id TEXT NOT NULL, kind TEXT NOT NULL,
       payload TEXT NOT NULL, created TEXT NOT NULL);
       CREATE INDEX IF NOT EXISTS idx_v100_user_kind ON records(user_id,kind,created);
       CREATE TABLE IF NOT EXISTS preferences(user_id TEXT PRIMARY KEY, payload TEXT NOT NULL);""")
    return db
def catalog():
    return [{'id':f'V{k}','name':v,'capabilities':CAPABILITIES[k], 'status':'functional_limited_prototype',
             'requires_authentication':True,'autonomous_execution':False} for k,v in NAMES.items()]
def _record(user,kind,payload):
    rid=str(uuid.uuid4()); created=now()
    with _LOCK,connect() as db:
        db.execute('INSERT INTO records VALUES(?,?,?,?,?)',(rid,str(user),kind,json.dumps(payload,ensure_ascii=False),created))
    return {'id':rid,'created':created,**payload}
def _items(user,kind,limit=30):
    with _LOCK,connect() as db:
        rows=db.execute('SELECT * FROM records WHERE user_id=? AND kind=? ORDER BY created DESC,id DESC LIMIT ?',
                        (str(user),kind,max(1,min(int(limit),100)))).fetchall()
    return [{'id':r['id'],'created':r['created'],**json.loads(r['payload'])} for r in rows]
def _get(user,kind,rid):
    with _LOCK,connect() as db:
        row=db.execute('SELECT * FROM records WHERE user_id=? AND kind=? AND id=?',(str(user),kind,rid)).fetchone()
    return None if not row else {'id':row['id'],'created':row['created'],**json.loads(row['payload'])}
def _delete(user,kind,rid):
    with _LOCK,connect() as db:
        result=db.execute('DELETE FROM records WHERE user_id=? AND kind=? AND id=?',(str(user),kind,rid))
        return result.rowcount>0
def _require_text(value,field,maxlen=4000):
    if not isinstance(value,str) or not value.strip() or len(value)>maxlen: raise ValueError(f'{field}: texto obrigatório (máximo {maxlen})')
    return value.strip()
def _bool(v): return v is True

def empathy(user,data):
    # Never infer psychological state from pitch, typing or face. User self-report only.
    preference=data.get('preferred_tone','equilibrado')
    if preference not in ('equilibrado','objetivo','acolhedor','tecnico'): raise ValueError('preferred_tone inválido')
    consent=_bool(data.get('consent'))
    if not consent: raise ValueError('Consentimento explícito necessário para adaptação')
    styles={'equilibrado':(1.0,0),'objetivo':(1.08,0),'acolhedor':(0.94,-1),'tecnico':(1.0,0)}
    speed,pitch=styles[preference]
    return {'engine':'V95','user_id':str(user),'recommended_tone':preference,
            'prosody_profile':{'rate':speed,'pitch_semitones':pitch},'applied_to_audio':False,
            'emotion_detected':False,'reason':'preferência declarada pelo usuário','biometric_inference':False}

def proactive(user,data):
    if not _bool(data.get('consent')): raise ValueError('Consentimento explícito necessário')
    context=_require_text(data.get('context'),'context',2000)
    action=_require_text(data.get('suggested_action'),'suggested_action',500)
    dedup=hashlib.sha256((context.casefold()+'|'+action.casefold()).encode()).hexdigest()[:20]
    for row in _items(user,'proposal',100):
        if row.get('dedup_key')==dedup and row.get('status')=='pending':
            return {**row,'deduplicated':True}
    return _record(user,'proposal',{'context':context,'suggested_action':action,'dedup_key':dedup,
             'status':'pending','approved':False,'executed':False,'origin':'user_supplied_context','requires_review':True})
def proposal_review(user,rid,approved):
    if not isinstance(approved,bool): raise ValueError('approved deve ser booleano')
    with _LOCK,connect() as db:
        row=db.execute('SELECT payload FROM records WHERE id=? AND user_id=? AND kind=?',(rid,str(user),'proposal')).fetchone()
        if row is None: raise KeyError('Proposta não encontrada')
        payload=json.loads(row['payload']);payload['status']='approved_for_manual_action' if approved else 'rejected'
        payload['approved']=approved;payload['executed']=False
        db.execute('UPDATE records SET payload=? WHERE id=? AND user_id=?',(json.dumps(payload,ensure_ascii=False),rid,str(user)))
    return {'id':rid,**payload}

def narrative_event(user,data):
    title=_require_text(data.get('title'),'title',160)
    desc=_require_text(data.get('description'),'description',2000)
    source=_require_text(data.get('source'),'source',300)
    if not _bool(data.get('consent')): raise ValueError('Consentimento explícito necessário')
    return _record(user,'timeline',{'title':title,'description':desc,'source':source,
       'event_date':str(data.get('event_date') or '')[:40],'category':str(data.get('category') or 'geral')[:80],
       'verified':False,'is_user_reported':True})
def narrative_arc(user):
    events=list(reversed(_items(user,'timeline',30)))
    return {'engine':'V97','user_id':str(user),'events':events,
      'narrative_summary':('Registros fornecidos pelo usuário: '+ '; '.join(e['title'] for e in events[-8:])) if events else 'Nenhum marco registrado.',
      'generated_from':'user_reported_events_only','psychological_inferences':False}

def research(user,data):
    question=_require_text(data.get('question'),'question',2000)
    sources=data.get('sources',[])
    if not isinstance(sources,list) or len(sources)>20: raise ValueError('sources deve ser lista com até 20 itens')
    accepted=[]
    for s in sources:
        if not isinstance(s,dict): raise ValueError('Fonte inválida')
        title=_require_text(s.get('title'),'source.title',200)
        excerpt=_require_text(s.get('excerpt'),'source.excerpt',2000)
        accepted.append({'title':title,'excerpt':excerpt,'url':str(s.get('url') or '')[:500],
                         'verified_externally':False})
    return _record(user,'investigation',{'question':question,'sources':accepted,'source_count':len(accepted),
      'status':'evidence_supplied_not_independently_verified','answer_generated':False,
      'missing_evidence':[] if accepted else ['Nenhuma fonte fornecida'],
      'external_research_performed':False})

def forge(user,data):
    title=_require_text(data.get('title'),'title',160)
    code=_require_text(data.get('candidate_code'),'candidate_code',15000)
    try: ast.parse(code); syntax={'valid':True,'error':None}
    except SyntaxError as e: syntax={'valid':False,'error':f'{e.msg} (linha {e.lineno})'}
    risk=[]
    for token in ('subprocess','os.system','eval(','exec(','__import__','shutil.rmtree'):
        if token in code: risk.append(token)
    return _record(user,'forge',{'title':title,'sha256':hashlib.sha256(code.encode()).hexdigest(),
        'candidate_code':code,'syntax':syntax,'review_flags':risk,'sandbox_executed':False,
        'tests_executed':False,'production_modified':False,'approval_required':True,
        'status':'awaiting_human_review'})

WORDS={95:('empatia','tom','voz','acolhimento','comunicação'),96:('lembrete','proativo','sugerir','rotina','pendência'),
 97:('história','linha do tempo','memória narrativa','marco'),98:('pesquisar','investigar','fontes','evidências','verificar'),
 99:('programar','código','bug','corrigir','refatorar','teste'),100:('missão','orquestrar','integrar','evoluir','estratégia')}
def select(objective,limit=6):
    text=_require_text(objective,'objective').casefold()
    matches=[]
    for num,words in WORDS.items():
        found=[w for w in words if re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',text)]
        if found: matches.append({'id':f'V{num}','name':NAMES[num],'matched_terms':found,'executed':False,
                                  'selection_method':'keyword_heuristic'})
    return sorted(matches,key=lambda x:(-len(x['matched_terms']),x['id']))[:limit]
def mission(user,data):
    objective=_require_text(data.get('objective'),'objective',4000)
    selected=select(objective)
    return _record(user,'mission',{'objective':objective,'selected_engines':selected,
       'status':'proposed','execution_authorized':False,'external_actions_enabled':False,
       'agent_roles':['Ashley: planejamento e proposta','Ashen: crítica e riscos','Auditor: verificação'],
       'agent_roles_executed':False,'requires_human_approval':True,
       'decision_trace':[{'time':now(),'event':'planned','detail':'seleção heurística sem execução'}]})
def status(user):
    return {'engine':'V100','user_id':str(user),'catalog_range':'V1-V100',
       'mission_count':len(_items(user,'mission',100)),'external_actions_enabled':False,
       'autonomous_code_deployment':False,'continuous_background_reasoning':False,
       'capabilities':'bounded_prototypes'}
