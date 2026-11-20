import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.finale_v77_v80 import api


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB", tmp_path / "auditoria_seguranca.db")
    return api


def registrar(m, usuario, aprovado=True):
    return m.add_evidence(
        m.Evidence(
            engine="V77",
            mission="Auditoria de segurança",
            outcome="Resultado de teste",
            cost=1.0,
            latency=0.5,
            approved=aprovado
        ),
        uid=usuario
    )["id"]


def test_v80_aceita_evidencia_do_proprietario(ambiente):
    m = ambiente
    eid = registrar(m, "usuario_a")

    resposta = m.mission_review(
        m.Mission(goal="Revisar evidência", evidence_ids=[eid]),
        uid="usuario_a"
    )

    assert resposta["evidence_count"] == 1
    assert resposta["evidence"][0]["id"] == eid
    assert resposta["execution_authorized"] is False


def test_v80_bloqueia_evidencia_de_outro_usuario(ambiente):
    m = ambiente
    eid = registrar(m, "usuario_a")

    with pytest.raises(HTTPException) as erro:
        m.mission_review(
            m.Mission(goal="Acessar evidência alheia", evidence_ids=[eid]),
            uid="usuario_b"
        )

    assert erro.value.status_code == 404


def test_v80_alerta_evidencia_nao_aprovada(ambiente):
    m = ambiente
    eid = registrar(m, "usuario_a", aprovado=False)

    resposta = m.mission_review(
        m.Mission(goal="Revisar evidência", evidence_ids=[eid]),
        uid="usuario_a"
    )

    assert "Evidência não aprovada" in resposta["warnings"]


def test_v78_revogacao_de_consentimento(ambiente):
    m = ambiente
    org = m.create_org(
        m.Organization(name="Organização de Teste"),
        uid="usuario_a"
    )["organization_id"]

    m.set_consent(
        org,
        m.Consent(scope="analise", granted=True),
        uid="usuario_a"
    )

    resposta = m.set_consent(
        org,
        m.Consent(scope="analise", granted=False),
        uid="usuario_a"
    )

    assert resposta["granted"] is False

    with m.connect() as conexao:
        registro = conexao.execute(
            "SELECT granted FROM consent WHERE org=? AND uid=? AND scope=?",
            (org, "usuario_a", "analise")
        ).fetchone()

    assert registro["granted"] == 0


def test_v77_metricas_isoladas_entre_usuarios(ambiente):
    m = ambiente
    registrar(m, "usuario_a")
    registrar(m, "usuario_a")
    registrar(m, "usuario_b")

    a = m.metrics(uid="usuario_a")["metrics"]
    b = m.metrics(uid="usuario_b")["metrics"]

    assert a[0]["n"] == 2
    assert b[0]["n"] == 1


def test_modelos_rejeitam_valores_invalidos(ambiente):
    m = ambiente

    with pytest.raises(ValidationError):
        m.Evidence(
            engine="V77",
            mission="Teste",
            outcome="Resultado",
            cost=-10
        )

    with pytest.raises(ValidationError):
        m.Organization(name="Teste", budget=-100)

    with pytest.raises(ValidationError):
        m.LanguageRequest(text="")

    with pytest.raises(ValidationError):
        m.Mission(goal="")
