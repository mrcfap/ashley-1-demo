"""FastAPI autenticada V85–V94, integração sem efeitos externos."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.nextgen.api import identity
from .core import NAMES, run, catalog
router=APIRouter(prefix='/api/v1/engines',tags=['Axyntora V85-V94'])
class RunRequest(BaseModel):
    action:str=Field(min_length=1,max_length=50)
    data:dict=Field(default_factory=dict)
@router.get('/nextgen/catalog')
def get_catalog(user_id:str=Depends(identity)):
    return {'engines':catalog(),'integration':'V84_SYMPHONY_planning_only','user_id':user_id}
@router.get('/nextgen/{engine}/status')
def get_status(engine:int,user_id:str=Depends(identity)):
    if engine not in NAMES: raise HTTPException(404,'Motor não registrado')
    return {'engine':f'V{engine}','name':NAMES[engine],'status':'functional_limited_prototype','user_id':user_id,'autonomous_execution':False}
@router.post('/nextgen/{engine}/run')
def run_engine(engine:int,payload:RunRequest,user_id:str=Depends(identity)):
    if engine not in NAMES: raise HTTPException(404,'Motor não registrado')
    try: return run(engine,payload.action,payload.data,user_id)
    except (ValueError,TypeError,OverflowError) as exc: raise HTTPException(422,str(exc)) from exc
