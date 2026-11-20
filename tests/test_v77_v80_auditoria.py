from fastapi.testclient import TestClient
from app.API.app import app

client = TestClient(app)

def test_rotas_v77_v80_registradas():
    rotas = {
        r.path
        for item in app.routes
        for r in (
            getattr(item, "original_router", item).routes
            if hasattr(item, "original_router")
            else [item]
        )
        if hasattr(r, "path")
    }

    esperadas = {
        "/api/v1/engines/v77/evidence",
        "/api/v1/engines/v77/metrics",
        "/api/v1/engines/v78/organizations",
        "/api/v1/engines/v78/my-data",
        "/api/v1/engines/v79/language/prepare",
        "/api/v1/engines/v80/mission/review",
        "/api/v1/engines/v77-v80/status",
    }

    assert esperadas <= rotas


def test_status_exige_autenticacao():
    resposta = client.get("/api/v1/engines/v77-v80/status")
    assert resposta.status_code == 401


def test_metricas_v77_exigem_autenticacao():
    resposta = client.get("/api/v1/engines/v77/metrics")
    assert resposta.status_code == 401


def test_dados_v78_exigem_autenticacao():
    resposta = client.get("/api/v1/engines/v78/my-data")
    assert resposta.status_code == 401
