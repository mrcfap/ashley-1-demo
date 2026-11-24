"""Ponto de entrada único mantendo rotas e autenticação do projeto original."""
import hmac
import os

from fastapi import HTTPException, Request

from app.API.app import app
from orquestrador_tudo_ligado import OrquestradorTudoLigado


@app.get("/master/status", include_in_schema=False)
def master_status(request: Request):
    key = os.getenv("AXYNTORA_MASTER_ADMIN_KEY", "")
    provided = request.headers.get("x-master-admin-key", "")
    if not key or not hmac.compare_digest(provided.encode("utf-8"), key.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Acesso administrativo não autorizado")
    return OrquestradorTudoLigado().status_completo()
