from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.hub.cognitive_hub import AshleyCognitiveHub
from app.nextgen.api import identity
from app.nextgen.symphony_bridge import SymphonyOrchestratorBridge
from app.core.orquestrador import OrquestradorAshley
from app.nextgen.integration_registry import inventory, agent_catalog
from app.nextgen.nextgen_planning import extended_inventory


router = APIRouter(prefix="/api/v1/engines/v84", tags=["V84 SYMPHONY"])


class SymphonyPlanRequest(BaseModel):
    objective: str = Field(min_length=1, max_length=4000)
    complexity: str = Field(default="baixa", pattern="^(baixa|media|alta)$")


def build_planning_orchestrator():
    """
    Instancia somente o seletor cognitivo.
    Não inicializa o orquestrador completo.
    """
    hub = object.__new__(AshleyCognitiveHub)

    hub.continuidade = None
    hub.raciocinio_causal = None
    hub.bom_senso = None
    hub.criatividade = None
    hub.diretor_adaptativo = None

    orchestrator = object.__new__(OrquestradorAshley)
    orchestrator.hub = hub
    return orchestrator


@router.post("/plan")
def plan_v84(
    payload: SymphonyPlanRequest,
    user_id=Depends(identity),
):
    orchestrator = build_planning_orchestrator()
    bridge = SymphonyOrchestratorBridge(orchestrator)

    result = bridge.prepare(
        objective=payload.objective,
        complexity=payload.complexity,
    )

    return {
        **result,
        "integration": {"catalog_endpoint": "/api/v1/engines/v84/integration-catalog", "agents": agent_catalog(), "mode": "inventory_and_planning_only"},
        "user_authenticated": True,
        "execution_authorized": False,
        "external_actions_enabled": False,
        "status": "planning_only",
    }


@router.get("/integration-catalog")
def integration_catalog_v84(user_id=Depends(identity)):
    """Inventário somente leitura, autenticado; não executa motores."""
    return {"motor": "V84 SYMPHONY", "inventory": extended_inventory(inventory()),
            "agents": agent_catalog(), "execution_authorized": False}
