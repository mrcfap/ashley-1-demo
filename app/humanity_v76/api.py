"""Optional FastAPI router. IMPORTANT: identity must be supplied by existing authenticated backend.
Never trust a user_id supplied in request body. Mount only after binding auth dependency.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from .engine import HumanityCoreV76


def make_router(engine: HumanityCoreV76, get_authenticated_user_id):
    router = APIRouter(prefix='/api/v1/engines/v76', tags=['V76 Humanity Core'])
    class ConsentPayload(BaseModel):
        enabled: bool
    class GoalPayload(BaseModel):
        title: str = Field(min_length=1, max_length=300)
    class ProgressPayload(BaseModel):
        note: str = Field(min_length=1, max_length=2000)
        evidence: str | None = Field(default=None, max_length=2000)
        confirmed: bool = False
    class ProposalPayload(BaseModel):
        message: str = Field(min_length=1)
        requested_action: str = 'reflect'

    def call(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PermissionError as e:
            raise HTTPException(403, str(e))
        except LookupError as e:
            raise HTTPException(404, str(e))
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.post('/consent')
    def consent(data: ConsentPayload, uid: str = Depends(get_authenticated_user_id)):
        return call(engine.consent, uid, data.enabled)

    @router.post('/goals')
    def create_goal(data: GoalPayload, uid: str = Depends(get_authenticated_user_id)):
        return call(engine.create_goal, uid, data.title)

    @router.get('/goals')
    def list_goals(uid: str = Depends(get_authenticated_user_id)):
        return call(engine.list_goals, uid)

    @router.post('/goals/{goal_id}/progress')
    def record_progress(goal_id: str, data: ProgressPayload, uid: str = Depends(get_authenticated_user_id)):
        return call(engine.record_progress, uid, goal_id, data.note, evidence=data.evidence, confirmed=data.confirmed)

    @router.get('/goals/{goal_id}/progress')
    def progress(goal_id: str, uid: str = Depends(get_authenticated_user_id)):
        return call(engine.progress, uid, goal_id)

    @router.post('/propose')
    def propose(data: ProposalPayload, uid: str = Depends(get_authenticated_user_id)):
        return call(engine.propose, uid, data.message, requested_action=data.requested_action)

    @router.delete('/my-data')
    def delete(uid: str = Depends(get_authenticated_user_id)):
        return call(engine.delete_my_data, uid)

    return router
