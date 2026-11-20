"""Authenticated, bounded V95-V100 endpoints. No user_id accepted from client."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.nextgen.api import identity
from . import core

router=APIRouter(prefix='/api/v1/engines',tags=['Axyntora V95-V100'])
class Payload(BaseModel):
    data:dict=Field(default_factory=dict)
def _safe(call,*args):
    try:return call(*args)
    except (ValueError,TypeError,OverflowError) as exc: raise HTTPException(422,str(exc)) from exc
    except KeyError as exc: raise HTTPException(404,str(exc)) from exc

@router.get('/v95-v100/catalog')
def catalog(user_id:str=Depends(identity)):return {'engines':core.catalog(),'user_id':user_id}
@router.post('/v95/affective-state')
def v95(payload:Payload,user_id:str=Depends(identity)):return _safe(core.empathy,user_id,payload.data)
@router.post('/v95/voice-synthesis/adaptive')
def v95_tts(payload:Payload,user_id:str=Depends(identity)):return _safe(core.empathy,user_id,payload.data)
@router.post('/v96/proactive/trigger')
def v96(payload:Payload,user_id:str=Depends(identity)):return _safe(core.proactive,user_id,payload.data)
@router.get('/v96/proposals')
def v96_list(user_id:str=Depends(identity)):return {'proposals':core._items(user_id,'proposal')}
@router.post('/v96/proposals/{proposal_id}/review')
def v96_review(proposal_id:str,approved:bool,user_id:str=Depends(identity)):return _safe(core.proposal_review,user_id,proposal_id,approved)
@router.post('/v97/narrative/event')
def v97_event(payload:Payload,user_id:str=Depends(identity)):return _safe(core.narrative_event,user_id,payload.data)
@router.get('/v97/narrative/arc')
def v97_arc(user_id:str=Depends(identity)):return core.narrative_arc(user_id)
@router.delete('/v97/narrative/event/{event_id}')
def v97_delete(event_id:str,user_id:str=Depends(identity)):
    if not core._delete(user_id,'timeline',event_id):raise HTTPException(404,'Marco não encontrado')
    return {'deleted':True}
@router.post('/v98/investigations')
def v98(payload:Payload,user_id:str=Depends(identity)):return _safe(core.research,user_id,payload.data)
@router.get('/v98/investigations/{investigation_id}')
def v98_get(investigation_id:str,user_id:str=Depends(identity)):
    result=core._get(user_id,'investigation',investigation_id)
    if not result:raise HTTPException(404,'Investigação não encontrada')
    return result
@router.post('/v99/improvements/propose')
def v99(payload:Payload,user_id:str=Depends(identity)):return _safe(core.forge,user_id,payload.data)
@router.get('/v99/improvements/{proposal_id}')
def v99_get(proposal_id:str,user_id:str=Depends(identity)):
    result=core._get(user_id,'forge',proposal_id)
    if not result:raise HTTPException(404,'Melhoria não encontrada')
    return result
@router.post('/v100/mission')
def v100(payload:Payload,user_id:str=Depends(identity)):return _safe(core.mission,user_id,payload.data)
@router.get('/v100/mission/{mission_id}')
def v100_get(mission_id:str,user_id:str=Depends(identity)):
    result=core._get(user_id,'mission',mission_id)
    if not result:raise HTTPException(404,'Missão não encontrada')
    return result
@router.get('/v100/system-health')
def v100_health(user_id:str=Depends(identity)):return core.status(user_id)

# Phase 2: supervised deliberation; no production writes, shell or external research.
from . import supervised
@router.post('/v100/mission/{mission_id}/deliberate')
def v100_deliberate(mission_id:str,payload:Payload,user_id:str=Depends(identity)):
    return _safe(supervised.deliberate,user_id,mission_id,payload.data)

@router.get('/v100/mission/{mission_id}/report')
def v100_report(mission_id:str,user_id:str=Depends(identity)):
    return _safe(supervised.report,user_id,mission_id)

# Specialist governance layer: read-only catalog and bounded planning endpoint.
from . import specialists

@router.get('/v100/specialists/catalog')
def v100_specialists_catalog(user_id: str = Depends(identity)):
    return {'user_id': user_id, **specialists.catalog()}

@router.post('/v100/specialists/assess')
def v100_specialists_assess(payload: Payload, user_id: str = Depends(identity)):
    return {'user_id': user_id, **_safe(specialists.assess_request, payload.data)}
