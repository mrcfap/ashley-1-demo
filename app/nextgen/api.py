"""V81-V84: integração supervisionada e autenticada, sem ações externas."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from app.security import auth
from app.nextgen.engines import LumenV81, PraxisV82, SentinelV83, SymphonyV84, Risk

router = APIRouter(prefix="/api/v1", tags=["V81-V84"])
lumen = LumenV81()
praxis = PraxisV82()
sentinel = SentinelV83()
symphony = SymphonyV84()

def identity(request: Request) -> str:
    token = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    try:
        uid = auth.identity(token)
        profile = auth.profile(uid)
        if not profile.get("access_ready"):
            raise HTTPException(403, "Acesso pendente")
        return str(uid)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, "Autenticação necessária")

class VisualEvent(BaseModel):
    event: str = Field(min_length=1, max_length=160)
    fingerprint: str | None = Field(default=None, max_length=128)
    user_trigger: bool = False
    consent: bool = False

class UploadCheck(BaseModel):
    filename: str
    size: int = Field(ge=0)
    header_hex: str = Field(default="", max_length=128)

class SafetyCheck(BaseModel):
    text: str = Field(max_length=10000)

class ActionProposal(BaseModel):
    action: str = Field(min_length=1, max_length=100)
    risk: Risk
    preview: str = Field(min_length=1, max_length=2000)

class RouteCheck(BaseModel):
    consent: bool = False
    safety_allowed: bool = False
    requested_action: str = Field(min_length=1, max_length=100)
    approved: bool = False

@router.get("/engines/v81/status")
def v81_status(user_id: str = Depends(identity)):
    return {"motor":"V81 LUMEN", "state":"prototype_integrated", "streaming":False, "user":user_id, "notes":"Eventos visuais; sem vídeo contínuo."}

@router.get("/engines/v82/status")
def v82_status(user_id: str = Depends(identity)):
    return {"motor":"V82 PRAXIS", "state":"prototype_integrated", "external_execution":False, "user":user_id}

@router.get("/engines/v83/status")
def v83_status(user_id: str = Depends(identity)):
    return {"motor":"V83 SENTINEL", "state":"precheck_integrated", "antivirus":False, "user":user_id}

@router.get("/engines/v84/status")
def v84_status(user_id: str = Depends(identity)):
    return {"motor":"V84 SYMPHONY", "state":"prototype_integrated", "orchestration":"policy_gate_only", "user":user_id}

@router.post("/vision/lumen/observe")
def lumen_observe(payload: VisualEvent, user_id: str = Depends(identity)):
    return lumen.observe(user_id, event=payload.event, fingerprint=payload.fingerprint, user_trigger=payload.user_trigger, consent=payload.consent)

@router.get("/vision/lumen/context")
def lumen_context(consent: bool = False, user_id: str = Depends(identity)):
    return {"events":lumen.context(user_id, consent=consent)}

@router.delete("/vision/lumen/context")
def lumen_clear(user_id: str = Depends(identity)):
    lumen.clear(user_id)
    return {"cleared":True}

@router.post("/security/v83/request-check")
def request_check(payload: SafetyCheck, user_id: str = Depends(identity)):
    return sentinel.precheck_request(payload.text)

@router.post("/security/v83/file-check")
def file_check(payload: UploadCheck, user_id: str = Depends(identity)):
    try:
        head=bytes.fromhex(payload.header_hex)
    except ValueError:
        raise HTTPException(422, "Cabeçalho hexadecimal inválido")
    return sentinel.inspect_upload(payload.filename,payload.size,head)

@router.post("/engines/v82/propose")
def propose(payload: ActionProposal, user_id: str = Depends(identity)):
    return praxis.propose(payload.action,payload.risk,preview=payload.preview,user_id=user_id)

@router.post("/engines/v84/route-check")
def route_check(payload: RouteCheck, user_id: str = Depends(identity)):
    # Flags do cliente não constituem consentimento nem aprovação confiável.
    # Este endpoint é apenas uma simulação informativa; nunca libera execução.
    preview = symphony.route(**payload.model_dump())
    return {"state": "ADVISORY_ONLY", "reason": "untrusted_client_assertions",
            "hypothetical_result": preview, "execution_authorized": False,
            "external_actions_enabled": False}
