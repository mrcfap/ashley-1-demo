"""API V62-V65; user ID comes only from Ashley's verified bearer token."""
from __future__ import annotations
import os, sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from app.security import auth as ashley_auth
from app.engines_v62.nexus import NexusEngine
from app.engines_v63_v65.engines import PsycheSynapseV63, EpistemicCoreV65

router = APIRouter(prefix='/api/v1/engines', tags=['Ashley V62-V65'])
DATA = Path(os.environ.get('ASHLEY_ENGINES_DATA_DIR', str(Path(__file__).resolve().parents[3] / 'data')))

def identity(request: Request) -> str:
    token = request.headers.get('authorization','').removeprefix('Bearer ').strip()
    if not token: raise HTTPException(401, 'Autenticacao necessaria')
    try:
        uid = ashley_auth.identity(token)
        profile = ashley_auth.profile(uid)
    except HTTPException: raise
    except Exception: raise HTTPException(401, 'Sessao invalida')
    if not profile.get('access_ready') or profile.get('age_group') != 'adult':
        raise HTTPException(403, 'Funcao disponivel apenas a adultos autorizados')
    return str(uid)

def nexus(): return NexusEngine(DATA / 'v62_nexus.db')
class ProjectIn(BaseModel):
    title: str = Field(min_length=1,max_length=200)
    purpose: str = Field(min_length=1,max_length=1000)
    community: str = Field(min_length=1,max_length=200)
    steps: list[str] = Field(min_length=1,max_length=100)
class EvidenceIn(BaseModel):
    evidence: str = Field(min_length=1,max_length=4000)
class WorkloadIn(BaseModel):
    workload: float = Field(ge=0,le=10)
    consent: bool
    context: str = 'pessoal'
class OutcomeIn(BaseModel):
    objective: str = Field(min_length=1,max_length=1000)
class ClaimIn(BaseModel):
    claim: str = Field(min_length=1,max_length=2000)
    source: str
    evidence: str | None = None
    independently_verified: bool = False

@router.post('/v62/projects',status_code=201)
def create_project(data: ProjectIn,uid: str=Depends(identity)):
    try: return nexus().create_project(owner_id=uid,title=data.title,purpose=data.purpose,community=data.community,steps=data.steps)
    except ValueError as e: raise HTTPException(422,str(e))
@router.get('/v62/projects')
def list_projects(uid: str=Depends(identity)):
    return {'projects':nexus().list_projects(owner_id=uid)}
@router.get('/v62/projects/{project_id}')
def get_project(project_id: str,uid: str=Depends(identity)):
    p=nexus().get_project(owner_id=uid,project_id=project_id)
    if p is None: raise HTTPException(404,'Projeto nao encontrado')
    return p
@router.post('/v62/projects/{project_id}/steps/{step_id}/evidence')
def report_step(project_id: str,step_id: str,data: EvidenceIn,uid: str=Depends(identity)):
    if not nexus().report_step(owner_id=uid,project_id=project_id,step_id=step_id,evidence=data.evidence):
        raise HTTPException(404,'Etapa nao encontrada')
    return {'status':'AGUARDANDO_CONFIRMACAO'}
@router.post('/v62/projects/{project_id}/steps/{step_id}/confirm')
def confirm_step(project_id: str,step_id: str,uid: str=Depends(identity)):
    if not nexus().confirm_step(owner_id=uid,project_id=project_id,step_id=step_id,approver_id=uid):
        raise HTTPException(409,'Etapa inexistente ou sem evidencia pendente')
    return {'status':'CONFIRMADA_POR_PESSOA'}
@router.post('/v63/suggest')
def suggest(data: WorkloadIn,uid: str=Depends(identity)):
    try:
        s=PsycheSynapseV63().suggest(data.workload,consent=data.consent,context=data.context)
        return {'level':s.level,'explanation':s.explanation,'options':list(s.options),'clinical_diagnosis':False,'executed_actions':0}
    except PermissionError as e: raise HTTPException(403,str(e))
    except ValueError as e: raise HTTPException(422,str(e))

@contextmanager
def outcome_db():
    DATA.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(str(DATA/'v64_outcomes.db'),timeout=30)
    conn.row_factory=sqlite3.Row
    try:
        with conn:
            conn.execute('CREATE TABLE IF NOT EXISTS outcomes (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, objective TEXT NOT NULL, status TEXT NOT NULL, evidence TEXT, updated_at TEXT NOT NULL)')
            yield conn
    finally: conn.close()
def now(): return datetime.now(timezone.utc).isoformat()
@router.post('/v64/outcomes',status_code=201)
def plan_outcome(data: OutcomeIn,uid: str=Depends(identity)):
    oid=str(uuid4())
    with outcome_db() as conn: conn.execute('INSERT INTO outcomes VALUES (?,?,?,?,?,?)',(oid,uid,data.objective.strip(),'PLANEJADO',None,now()))
    return get_outcome(oid,uid)
@router.get('/v64/outcomes/{outcome_id}')
def get_outcome(outcome_id: str,uid: str=Depends(identity)):
    with outcome_db() as conn: row=conn.execute('SELECT * FROM outcomes WHERE id=? AND owner_id=?',(outcome_id,uid)).fetchone()
    if row is None: raise HTTPException(404,'Resultado nao encontrado')
    return dict(row)
@router.post('/v64/outcomes/{outcome_id}/evidence')
def outcome_evidence(outcome_id: str,data: EvidenceIn,uid: str=Depends(identity)):
    with outcome_db() as conn:
        cur=conn.execute("UPDATE outcomes SET evidence=?,status='AGUARDANDO_VERIFICACAO',updated_at=? WHERE id=? AND owner_id=? AND status='PLANEJADO'",(data.evidence.strip(),now(),outcome_id,uid))
    if cur.rowcount!=1: raise HTTPException(409,'Resultado inexistente ou estado incompativel')
    return get_outcome(outcome_id,uid)
@router.post('/v64/outcomes/{outcome_id}/confirm')
def outcome_confirm(outcome_id: str,uid: str=Depends(identity)):
    with outcome_db() as conn:
        cur=conn.execute("UPDATE outcomes SET status='CONFIRMADO_POR_PESSOA',updated_at=? WHERE id=? AND owner_id=? AND status='AGUARDANDO_VERIFICACAO' AND length(trim(evidence))>0",(now(),outcome_id,uid))
    if cur.rowcount!=1: raise HTTPException(409,'Evidencia pendente ou registro inexistente')
    return get_outcome(outcome_id,uid)
@router.post('/v65/assess')
def assess(data: ClaimIn,uid: str=Depends(identity)):
    try:
        result=EpistemicCoreV65().assess(data.claim,data.source,evidence=data.evidence,independently_verified=False)
        result['note']='Evidencia declarada nao constitui verificacao independente.'
        return result
    except ValueError as e: raise HTTPException(422,str(e))
