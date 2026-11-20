import importlib
import json
import re
import sqlite3
from contextlib import closing

from fastapi.testclient import TestClient

from app.cases.ciclo_adaptativo import CicloAdaptativoResolucao


def test_chat_outcome_survives_new_session_and_requires_confirmation(tmp_path, monkeypatch):
    api = importlib.import_module("app.API.app")
    db = tmp_path / "cases.sqlite"
    monkeypatch.setattr(api, "DB", db)
    monkeypatch.setattr(api.ashley_auth, "identity", lambda token: {"first": 1, "second": 1, "other": 3}[token])
    monkeypatch.setattr(api.ashley_auth, "profile", lambda uid: {"age_group": "adult", "access_ready": True})
    client = TestClient(api.app)

    def send(message, token="first", uid=1, json_header=True):
        body = {"message": message, "persona": "Ashley", "language": "pt-BR", "user_id": uid, "history": []}
        headers = {"Authorization": f"Bearer {token}"}
        if json_header:
            return client.post("/chat", headers=headers, json=body)
        return client.post("/chat", headers=headers, content=json.dumps(body))

    def query(statement):
        with closing(sqlite3.connect(db)) as conn:
            return conn.execute(statement).fetchall()

    assert send("/acompanhar Explicar em francês simples | Cliente conclui em francês").status_code == 200
    assert send("/retomar-caso 1", token="other", json_header=False).status_code == 403
    assert "Não encontrei" in send("/retomar-caso 1", token="other", uid=3).json()["answer"]

    response = send("Fiz o que você sugeriu e o cliente ainda pediu inglês.", token="second")
    assert response.status_code == 200, response.text
    reply = response.json()["answer"]
    assert "Explicar em francês simples" in reply
    token = re.search(r"/confirmar-resultado (\w+)", reply)[1]
    assert query("SELECT count(*) FROM caso_avaliacoes") == [(0,)]
    assert "não está disponível" in send(f"/confirmar-resultado {token} FALHA", token="other", uid=3).json()["answer"]

    def fail(*args, **kwargs):
        raise RuntimeError("falha simulada após iniciar a avaliação")

    with monkeypatch.context() as scoped:
        scoped.setattr(CicloAdaptativoResolucao, "registrar_adaptacao", fail)
        failing_client = TestClient(api.app, raise_server_exceptions=False)
        response = failing_client.post("/chat", headers={"Authorization": "Bearer second"}, json={
            "message": f"/confirmar-resultado {token} FALHA", "user_id": 1, "language": "pt-BR",
        })
        assert response.status_code == 500
    assert query("SELECT count(*) FROM caso_avaliacoes") == [(0,)]
    assert query("SELECT status FROM caso_proximas_acoes") == [("PENDENTE",)]

    confirmed = send(f"/confirmar-resultado {token} FALHA", token="second").json()["answer"]
    assert "Ajuste proposto" in confirmed
    assert "já foi processado" in send(f"/confirmar-resultado {token} FALHA").json()["answer"]
    assert query("SELECT classificacao, acao_id FROM caso_avaliacoes") == [("FALHA", 1)]
    assert query("SELECT status FROM caso_proximas_acoes") == [("CONCLUIDA",)]
    assert "Ajuste aprovado" in send(f"/aprovar-ajuste {token}").json()["answer"]
    assert "Ajuste desfeito" in send(f"/desfazer-ajuste {token}").json()["answer"]
    assert "Resultado confirmado" in send("/retomar-caso 1", token="second").json()["answer"]
    assert query("SELECT status FROM caso_proximas_acoes ORDER BY id") == [("CONCLUIDA",), ("SUBSTITUIDA",)]
