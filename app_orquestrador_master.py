"""Ponto de entrada único mantendo rotas e autenticação do projeto original."""
from app.API.app import app
from orquestrador_tudo_ligado import OrquestradorTudoLigado
from fastapi import Request, HTTPException
import os,hmac
@app.get('/master/status', include_in_schema=False)
def master_status(request:Request):
    key=os.getenv('AXYNTORA_MASTER_ADMIN_KEY','')
    provided=request.headers.get('x-master-admin-key','')
    if not key or not hmac.compare_digest(provided,key):
        raise HTTPException(status_code=403,detail='Acesso administrativo não autorizado')
    return OrquestradorTudoLigado().status_completo()
