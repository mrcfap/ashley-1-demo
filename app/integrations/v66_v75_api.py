"""Rotas incrementais; reutilizam autenticação adulta da Ashley."""
from __future__ import annotations
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.integrations.v62_v65_api import identity
from app.engines_v66_v75.core import (EngineStore, aletheia, chronos, omni_catalog, ethos,
    impact, provenance, circuit_breaker, readiness)

router=APIRouter(prefix='/api/v1/engines',tags=['Ashley V66-V70 V73-V75'])
def store():
    base=Path(os.environ.get('ASHLEY_ENGINES_DATA_DIR',str(Path(__file__).resolve().parents[2]/'data')))
    return EngineStore(base/'v66_v75.db')
class Source(BaseModel):
    reference:str=Field(max_length=1000)
    excerpt:str=Field(max_length=4000)
    trusted:bool=False
class Claim(BaseModel):
    claim:str=Field(min_length=1,max_length=4000)
    sources:list[Source]=Field(default_factory=list,max_length=20)
class Task(BaseModel):
    id:str=Field(min_length=1,max_length=100)
    critical:bool=True
class Rhythm(BaseModel):
    energy:float=Field(ge=0,le=10)
    consent:bool=False
    tasks:list[Task]=Field(default_factory=list,max_length=100)
class Tool(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    scope:str=Field(min_length=1,max_length=100)
class Catalog(BaseModel):
    tools:list[Tool]=Field(default_factory=list,max_length=100)
class Permission(BaseModel):
    scope:str=Field(min_length=1,max_length=100)
    granted:bool
class Gate(BaseModel):
    scope:str=Field(min_length=1,max_length=100)
    critical:bool=False
    confirmed:bool=False
class Impact(BaseModel):
    title:str=Field(min_length=1,max_length=200)
    milestones:list[str]=Field(min_length=1,max_length=50)
class Risk(BaseModel):
    risk:str
    approved:bool=False
class Checks(BaseModel):
    checks:dict[str,bool]

@router.post('/v66/assess')
def v66(d:Claim,uid:str=Depends(identity)): return aletheia(d.claim,[x.model_dump() for x in d.sources])
@router.post('/v67/plan')
def v67(d:Rhythm,uid:str=Depends(identity)): return chronos([x.model_dump() for x in d.tasks],d.energy,d.consent)
@router.post('/v68/catalog')
def v68(d:Catalog,uid:str=Depends(identity)): return omni_catalog([x.model_dump() for x in d.tools])
@router.post('/v69/permissions')
def v69_permission(d:Permission,uid:str=Depends(identity)): return store().grant(uid,d.scope,d.granted)
@router.post('/v69/check')
def v69_check(d:Gate,uid:str=Depends(identity)): return ethos(store(),uid,d.scope,d.critical,d.confirmed)
@router.post('/v70/projects',status_code=201)
def v70_create(d:Impact,uid:str=Depends(identity)): return impact(store(),uid,d.title,d.milestones)
@router.get('/v70/projects')
def v70_list(uid:str=Depends(identity)): return {'projects':store().list(uid,'impact')}
@router.get('/v70/projects/{project_id}')
def v70_get(project_id:str,uid:str=Depends(identity)):
    item=store().get(uid,'impact',project_id)
    if item is None: raise HTTPException(404,'Projeto não encontrado')
    return item
@router.get('/v73/audit')
def v73(uid:str=Depends(identity)): return provenance(store(),uid)
@router.post('/v74/evaluate')
def v74(d:Risk,uid:str=Depends(identity)):
    try: return circuit_breaker(d.risk,d.approved)
    except ValueError as e: raise HTTPException(422,str(e))
@router.post('/v75/readiness')
def v75(d:Checks,uid:str=Depends(identity)): return readiness(d.checks)
