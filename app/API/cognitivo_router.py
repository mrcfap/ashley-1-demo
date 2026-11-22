"""Rotas cognitivas de diagnóstico: autenticadas e sem execução externa."""
from fastapi import APIRouter, Header
from pydantic import BaseModel, Field
from app.security import auth as ashley_auth
from app.adaptive_director.politica_esforco import planejar_esforco
from app.adaptive_director.recuperacao_contextual import recuperar_contexto

router = APIRouter(prefix="/cognitivo", tags=["cognitivo"])

def _identidade(authorization: str):
    token = authorization.removeprefix("Bearer ").strip()
    return ashley_auth.identity(token)

class PedidoPlano(BaseModel):
    nivel: str = "medio"

class Documento(BaseModel):
    id: str
    usuario_id: int
    texto: str = Field(max_length=12000)
    consentimento: bool = False

class PedidoContexto(BaseModel):
    consulta: str = Field(min_length=1, max_length=2000)
    documentos: list[Documento] = Field(max_length=50)
    limite: int = Field(default=5, ge=1, le=20)

@router.post("/planejar")
def planejar(pedido: PedidoPlano, authorization: str = Header(default="")):
    _identidade(authorization)
    plano = planejar_esforco(pedido.nivel)
    return {"nivel": plano.nivel, "max_etapas": plano.max_etapas,
            "max_revisoes": plano.max_revisoes,
            "exige_aprovacao_externa": plano.exige_aprovacao_externa}

@router.post("/contexto")
def contexto(pedido: PedidoContexto, authorization: str = Header(default="")):
    identidade = _identidade(authorization)
    user_id = int(identidade["id"] if isinstance(identidade, dict) else identidade)
    return {"trechos": recuperar_contexto(pedido.consulta,
            [doc.model_dump() for doc in pedido.documentos],
            usuario_id=user_id, limite=pedido.limite)}
