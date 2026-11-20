from app.nextgen.engines import SymphonyV84


def test_v84_exige_consentimento():
    resultado = SymphonyV84().route(
        consent=False,
        safety_allowed=True,
        requested_action="read",
        approved=True
    )
    assert resultado["state"] == "DENIED"


def test_v84_bloqueia_acao_insegura():
    resultado = SymphonyV84().route(
        consent=True,
        safety_allowed=False,
        requested_action="write",
        approved=True
    )
    assert resultado["state"] == "DENIED"


def test_v84_exige_aprovacao_para_escrita():
    resultado = SymphonyV84().route(
        consent=True,
        safety_allowed=True,
        requested_action="write",
        approved=False
    )
    assert resultado["state"] == "AWAITING_APPROVAL"


def test_v84_leitura_permitida():
    resultado = SymphonyV84().route(
        consent=True,
        safety_allowed=True,
        requested_action="read"
    )
    assert resultado["state"] == "READY_FOR_EXISTING_ORCHESTRATOR"


def test_v84_nao_executa_acao():
    resultado = SymphonyV84().route(
        consent=True,
        safety_allowed=True,
        requested_action="write",
        approved=True
    )
    assert resultado["state"] == "READY_FOR_EXISTING_ORCHESTRATOR"
    assert "execution_result" not in resultado
