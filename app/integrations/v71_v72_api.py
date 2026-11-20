from __future__ import annotations
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.integrations.v62_v65_api import identity
from app.humanization.engines import AnamnesisV71, ResonanceSilenceV72

router = APIRouter(prefix='/api/v1/engines', tags=['Ashley V71-V72'])
DATA = Path(os.environ.get('ASHLEY_ENGINES_DATA_DIR', str(Path(__file__).resolve().parents[2] / 'data')))

class MilestoneIn(BaseModel):
    label: str = Field(min_length=1, max_length=300)
    event_date: str | None = None
    sensitivity: str = 'personal'
    consent: bool = False

class PacingIn(BaseModel):
    preference: str = 'normal'
    message: str = Field(default='', max_length=4000)
    urgent: bool = False  # Client hint only: never a replacement for server-side safety screening

def memory():
    return AnamnesisV71(DATA / 'v71_anamnesis.db')

@router.post('/v71/milestones', status_code=201)
def add_milestone(data: MilestoneIn, uid: str = Depends(identity)):
    try:
        return memory().add(uid, data.label, consent=data.consent,
                            event_date=data.event_date, sensitivity=data.sensitivity)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))

@router.get('/v71/milestones')
def list_milestones(uid: str = Depends(identity)):
    return {'milestones': memory().list(uid)}

@router.delete('/v71/milestones/{record_id}')
def delete_milestone(record_id: str, uid: str = Depends(identity)):
    if not memory().delete(uid, record_id):
        raise HTTPException(404, 'Marco nao encontrado')
    return {'deleted': True}

@router.post('/v72/response-plan')
def response_plan(data: PacingIn, uid: str = Depends(identity)):
    try:
        return ResonanceSilenceV72().plan(preference=data.preference,
                                         message=data.message, urgent=data.urgent)
    except ValueError as e:
        raise HTTPException(422, str(e))
