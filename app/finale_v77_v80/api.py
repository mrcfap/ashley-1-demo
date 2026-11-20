"""V77-V80 supervised MVP. Does not claim full multilingual audio or enterprise certification."""
from __future__ import annotations
import json, os, sqlite3, time, uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.integrations.v62_v65_api import identity

router = APIRouter(prefix='/api/v1/engines', tags=['Ashley V77-V80'])
DB = Path(os.getenv('ASHLEY_FINALE_DB', str(Path(__file__).resolve().parents[2] / 'data' / 'v77_v80.db')))

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(str(DB),timeout=15)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA busy_timeout=15000')
    con.executescript('''CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, owner TEXT NOT NULL, engine TEXT NOT NULL, mission TEXT NOT NULL, outcome TEXT NOT NULL, cost REAL NOT NULL, latency REAL NOT NULL, approved INTEGER, created REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS organizations(id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL, budget REAL NOT NULL, created REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS memberships(org TEXT NOT NULL, uid TEXT NOT NULL, role TEXT NOT NULL, PRIMARY KEY(org,uid));
    CREATE TABLE IF NOT EXISTS consent(org TEXT NOT NULL, uid TEXT NOT NULL, scope TEXT NOT NULL, granted INTEGER NOT NULL, PRIMARY KEY(org,uid,scope));''')
    return con

class Evidence(BaseModel):
    engine:str=Field(min_length=1,max_length=80)
    mission:str=Field(min_length=1,max_length=200)
    outcome:str=Field(min_length=1,max_length=1000)
    cost:float=Field(default=0,ge=0)
    latency:float=Field(default=0,ge=0)
    approved:bool|None=None

@router.post('/v77/evidence',status_code=201)
def add_evidence(d:Evidence,uid:str=Depends(identity)):
    item=str(uuid.uuid4())
    with connect() as c:c.execute('INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?)',(item,str(uid),d.engine,d.mission,d.outcome,d.cost,d.latency,None if d.approved is None else int(d.approved),time.time()))
    return {'id':item,'recorded':True,'source':'user_supplied_not_independently_verified'}

@router.get('/v77/metrics')
def metrics(uid:str=Depends(identity)):
    with connect() as c:
        rows=c.execute('SELECT engine,COUNT(*) n,SUM(cost) cost,AVG(latency) latency, SUM(CASE WHEN approved=1 THEN 1 ELSE 0 END) approved, SUM(CASE WHEN approved IS NOT NULL THEN 1 ELSE 0 END) reviewed FROM evidence WHERE owner=? GROUP BY engine',(str(uid),)).fetchall()
    return {'metrics':[dict(x) for x in rows],'note':'Somente evidências registradas; não representa pilotos homologados.'}

class Organization(BaseModel):
    name:str=Field(min_length=1,max_length=150)
    budget:float=Field(default=0,ge=0)

@router.post('/v78/organizations',status_code=201)
def create_org(d:Organization,uid:str=Depends(identity)):
    org=str(uuid.uuid4())
    with connect() as c:
        c.execute('INSERT INTO organizations VALUES(?,?,?,?,?)',(org,str(uid),d.name,d.budget,time.time()))
        c.execute('INSERT INTO memberships VALUES(?,?,?)',(org,str(uid),'owner'))
    return {'organization_id':org,'name':d.name,'budget':d.budget}

@router.get('/v78/organizations')
def list_org(uid:str=Depends(identity)):
    with connect() as c: rows=c.execute('SELECT id,name,budget FROM organizations WHERE owner=?',(str(uid),)).fetchall()
    return {'organizations':[dict(r) for r in rows]}

class Consent(BaseModel):
    scope:str=Field(min_length=1,max_length=100)
    granted:bool

@router.post('/v78/organizations/{org}/consent')
def set_consent(org:str,d:Consent,uid:str=Depends(identity)):
    with connect() as c:
        if not c.execute('SELECT 1 FROM memberships WHERE org=? AND uid=?',(org,str(uid))).fetchone():raise HTTPException(404,'Organização não encontrada')
        c.execute('INSERT INTO consent VALUES(?,?,?,?) ON CONFLICT(org,uid,scope) DO UPDATE SET granted=excluded.granted',(org,str(uid),d.scope,int(d.granted)))
    return {'organization_id':org,'scope':d.scope,'granted':d.granted,'note':'Revogação registrada neste módulo; não interrompe automaticamente tarefas externas.'}

@router.delete('/v78/my-data')
def erase(uid:str=Depends(identity)):
    with connect() as c:
        c.execute('DELETE FROM evidence WHERE owner=?',(str(uid),))
        c.execute('DELETE FROM consent WHERE uid=?',(str(uid),))
        orgs=[r[0] for r in c.execute('SELECT id FROM organizations WHERE owner=?',(str(uid),)).fetchall()]
        for org in orgs:
            c.execute('DELETE FROM consent WHERE org=?',(org,))
            c.execute('DELETE FROM memberships WHERE org=?',(org,))
        c.execute('DELETE FROM organizations WHERE owner=?',(str(uid),))
        c.execute('DELETE FROM memberships WHERE uid=?',(str(uid),))
    return {'deleted_from':'v77_v80_local_store','external_systems_untouched':True}

from app.finale_v77_v80.multilingual import MultilingualV79, LANGUAGES

class LanguageRequest(BaseModel):
    text:str=Field(min_length=1,max_length=10000)
    preferred_language:str=Field(default='auto',max_length=40)

@router.get('/v79/languages')
def v79_languages(uid:str=Depends(identity)):
    return {'languages':LANGUAGES,'text_routing':True,'automatic_detection':'script_hints_only','translation':'provider_required','speech':'stt_tts_provider_required'}

@router.post('/v79/language/prepare')
def language_prepare(d:LanguageRequest,uid:str=Depends(identity)):
    try:
        plan=MultilingualV79().prepare(d.text,d.preferred_language)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    return {'text':d.text,'preferred_language':plan.requested_language,
        'detected_language':plan.detected_language,'response_language':plan.response_language,
        'detection_method':plan.detection_method,'instruction':plan.instruction,
        'translation_performed':False,'speech_enabled':False,
        'requires':'LLM integration for actual responses; STT/TTS providers for speech'}

class TranslationRequest(BaseModel):
    text:str=Field(min_length=1,max_length=10000)
    source_language:str=Field(min_length=2,max_length=40)
    target_language:str=Field(min_length=2,max_length=40)

@router.post('/v79/language/translate')
def v79_translate(d:TranslationRequest,uid:str=Depends(identity)):
    try:
        result=MultilingualV79().translate(d.text,d.source_language,d.target_language)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    if result.get('error'):
        raise HTTPException(503,'Provedor de tradução não configurado')
    return result

class Mission(BaseModel):
    goal:str=Field(min_length=1,max_length=2000)
    evidence_ids:list[str]=Field(default_factory=list,max_length=30)
    human_approval:bool=False

@router.post('/v80/mission/review')
def mission_review(d:Mission,uid:str=Depends(identity)):
    with connect() as c:
        rows=[]
        for eid in d.evidence_ids:
            row=c.execute('SELECT id,engine,approved,outcome FROM evidence WHERE id=? AND owner=?',(eid,str(uid))).fetchone()
            if row is None:raise HTTPException(404,'Evidência não encontrada ou sem acesso')
            rows.append(dict(row))
    return {'goal':d.goal,'evidence':rows,'evidence_count':len(rows),'human_approval':d.human_approval,'execution_authorized':False,'status':'needs_human_review' if not d.human_approval else 'review_only','warnings':(['Nenhuma evidência associada'] if not rows else [])+(['Evidência não aprovada'] if any(x['approved']!=1 for x in rows) else []),'note':'Revisão determinística inicial, sem autonomia ou simulação de consciência.'}

@router.get('/v77-v80/status')
def status(uid:str=Depends(identity)):
    return {'v77':'evidence_mvp','v78':'organization_consent_mvp','v79':'language_routing_stub','v80':'supervised_review_mvp','production_ready':False}
