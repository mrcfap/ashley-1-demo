import pytest

from app.finale_v77_v80.bridge import FinaleBridge


def test_status_dos_quatro_motores():
    status = FinaleBridge(user_id=1).status()
    assert all(f"v{n}" in status for n in range(77, 81))


def test_nao_declara_prontidao_para_producao():
    status = FinaleBridge().status()
    assert status["production_ready"] is False


def test_ponte_permanece_somente_leitura():
    status = FinaleBridge().status()
    assert status["orchestrator_bridge"] == "read_only"


def test_preparacao_contexto():
    resultado = FinaleBridge().preparar_contexto(
        "Analisar um projeto e apresentar alternativas."
    )
    assert resultado["text_length"] == len(
        "Analisar um projeto e apresentar alternativas."
    )
    assert resultado["requested_language"] == "auto"


def test_acoes_externas_exigem_revisao():
    resultado = FinaleBridge().preparar_contexto(
        "Executar uma tarefa externa"
    )
    assert resultado["review_required_for_external_actions"] is True
    assert resultado["automatic_consent"] is False


def test_contexto_rejeita_entrada_nao_textual():
    with pytest.raises(TypeError):
        FinaleBridge().preparar_contexto(123)
