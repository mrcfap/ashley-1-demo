from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.nextgen.symphony_http import router, identity


def test_v84_http_sem_autenticacao():
    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/engines/v84/plan",
            json={
                "objective": "Analisar projeto",
                "complexity": "alta",
            },
        )

    assert response.status_code == 401


def test_v84_http_rejeita_objetivo_vazio():
    app = FastAPI()
    app.dependency_overrides[identity] = lambda: "usuario_teste"
    app.include_router(router)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/engines/v84/plan",
            json={
                "objective": "",
                "complexity": "alta",
            },
        )

    assert response.status_code == 422


def test_v84_http_planejamento_sem_execucao():
    app = FastAPI()
    app.dependency_overrides[identity] = lambda: "usuario_teste"
    app.include_router(router)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/engines/v84/plan",
            json={
                "objective": "Analisar a causa de uma falha no projeto",
                "complexity": "alta",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["motor"] == "V84 SYMPHONY"
    assert data["execution_authorized"] is False
    assert data["external_actions_enabled"] is False
    assert data["status"] == "planning_only"
    assert data["selected_engines"]["motores"]["continuidade"] is True
