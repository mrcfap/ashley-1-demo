from app.core.identidade_evolutiva import IdentidadeEvolutiva, PERGUNTAS

def test_cinco_perguntas(tmp_path):
    motor=IdentidadeEvolutiva(tmp_path / "identidade.db")
    diagnostico=motor.diagnostico({"chat": True})
    assert len(diagnostico["respostas"]) == 5
    assert set(diagnostico["respostas"]) == set(PERGUNTAS)
    assert "consciência" in diagnostico["respostas"][PERGUNTAS[0]]
    assert "chat" in motor.contexto({"chat": True})

def test_reflexao_nao_executa_mudancas(tmp_path):
    motor=IdentidadeEvolutiva(tmp_path / "identidade.db")
    proposta=motor.propor_reflexao({"chat":True}, ["teste de voz pendente"], ["testar voz"])
    assert proposta["status"] == "proposta_pendente_de_aprovacao"


def test_inventario_reflete_rota_e_resultado_atual():
    from app.core.capacidades import inventario

    estado = inventario(
        {"/chat", "/memoria/buscar/{user_id}"},
        {"conversa": {"resultado": "sucesso"}, "memoria_longa": {"resultado": "falha"}},
    )
    prioridades = {item["capacidade"]: item for item in IdentidadeEvolutiva.prioridades(estado)}
    assert "conversa" not in prioridades
    assert prioridades["memoria_longa"]["estado"] == "teste_real_sem_sucesso"
    assert prioridades["memoria_longa"]["acao_sugerida"] == "Investigar a falha e repetir o teste"
    assert estado["memoria_longa"]["rota_exposta"] is True
    assert estado["memoria_longa"]["requer_teste_real"] is True


def test_identidade_http_respeita_persona_e_permissoes(tmp_path, monkeypatch):
    import sqlite3
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from app.API import app as api

    def identity(token):
        if not token:
            raise HTTPException(401)
        return 1

    def require_admin(token):
        if token != "admin":
            raise HTTPException(403)

    banco = tmp_path / "identidade.db"
    monkeypatch.setattr(api, "identidade_evolutiva", IdentidadeEvolutiva(banco))
    monkeypatch.setattr(api, "testes_registrados", lambda: {})
    monkeypatch.setattr(api.ashley_auth, "identity", identity)
    monkeypatch.setattr(api.ashley_auth, "profile", lambda uid: {"age_group": "adult", "access_ready": True})
    monkeypatch.setattr(api.ashley_auth, "require_admin", require_admin)

    client = TestClient(api.app)
    assert client.get("/identidade").status_code == 401
    usuario = {"Authorization": "Bearer usuario"}
    diagnostico = client.get("/identidade", params={"persona": "Ashen"}, headers=usuario)
    assert diagnostico.status_code == 200
    assert diagnostico.json()["respostas"][PERGUNTAS[0]].startswith("Sou Ashen,")
    assert client.get("/identidade?persona=outra", headers=usuario).status_code == 422
    assert client.post("/identidade/reflexoes", headers=usuario).status_code == 403
    proposta = client.post("/identidade/reflexoes", headers={"Authorization": "Bearer admin"})
    assert proposta.status_code == 201
    assert proposta.json()["status"] == "proposta_pendente_de_aprovacao"
    with sqlite3.connect(banco) as con:
        registros = con.execute("SELECT aprovacao_humana FROM reflexoes_identidade").fetchall()
    assert registros == [(0,)]
