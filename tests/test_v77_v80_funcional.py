import pytest
from fastapi import HTTPException
from app.finale_v77_v80 import api


@pytest.fixture
def banco_isolado(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB", tmp_path / "v77_v80_teste.db")
    return api


def test_v77_registra_evidencia(banco_isolado):
    m = banco_isolado
    resultado = m.add_evidence(
        m.Evidence(
            engine="V77",
            mission="Auditoria funcional",
            outcome="Teste concluído",
            cost=1.5,
            latency=0.8,
            approved=True
        ),
        uid="usuario_a"
    )
    assert resultado["recorded"] is True
    assert resultado["id"]
    assert resultado["source"] == "user_supplied_not_independently_verified"


def test_v77_metricas_por_usuario(banco_isolado):
    m = banco_isolado
    m.add_evidence(
        m.Evidence(
            engine="V77",
            mission="Teste",
            outcome="Aprovado",
            cost=2,
            latency=4,
            approved=True
        ),
        uid="usuario_a"
    )
    resultado = m.metrics(uid="usuario_a")
    assert len(resultado["metrics"]) == 1
    assert resultado["metrics"][0]["n"] == 1
    assert resultado["metrics"][0]["approved"] == 1
    assert resultado["metrics"][0]["cost"] == pytest.approx(2)


def test_v77_isolamento_de_metricas(banco_isolado):
    m = banco_isolado
    m.add_evidence(
        m.Evidence(
            engine="V77",
            mission="Privada",
            outcome="Somente A",
        ),
        uid="usuario_a"
    )
    assert m.metrics(uid="usuario_b")["metrics"] == []


def test_v78_cria_organizacao(banco_isolado):
    m = banco_isolado
    resultado = m.create_org(
        m.Organization(name="Organização Teste", budget=100),
        uid="usuario_a"
    )
    assert resultado["organization_id"]
    assert resultado["name"] == "Organização Teste"


def test_v78_consentimento_do_membro(banco_isolado):
    m = banco_isolado
    org = m.create_org(
        m.Organization(name="Organização Teste"),
        uid="usuario_a"
    )["organization_id"]

    resultado = m.set_consent(
        org,
        m.Consent(scope="analise", granted=True),
        uid="usuario_a"
    )
    assert resultado["granted"] is True


def test_v78_bloqueia_usuario_externo(banco_isolado):
    m = banco_isolado
    org = m.create_org(
        m.Organization(name="Organização Privada"),
        uid="usuario_a"
    )["organization_id"]

    with pytest.raises(HTTPException) as erro:
        m.set_consent(
            org,
            m.Consent(scope="analise", granted=True),
            uid="usuario_b"
        )
    assert erro.value.status_code == 404


def test_v79_declara_limitacao_de_traducao(banco_isolado):
    m = banco_isolado
    resultado = m.language_prepare(
        m.LanguageRequest(
            text="Bom dia",
            preferred_language="es"
        ),
        uid="usuario_a"
    )
    assert resultado["translation_performed"] is False
    assert resultado["detected_language"] is None


def test_v80_revisao_nao_autoriza_execucao(banco_isolado):
    m = banco_isolado
    resultado = m.mission_review(
        m.Mission(
            goal="Revisar projeto",
            evidence_ids=[],
            human_approval=True
        ),
        uid="usuario_a"
    )
    assert resultado["execution_authorized"] is False
    assert resultado["status"] == "review_only"
    assert "Nenhuma evidência associada" in resultado["warnings"]
