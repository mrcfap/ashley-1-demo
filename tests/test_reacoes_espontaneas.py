from app.services.intencao_conversacional import classificar_intencao, orientacao_conversacional


def test_reacoes_espontaneas():
    for mensagem in ("Nossa me surpreendeu agora", "Uau!", "Caramba!", "Adorei", "Incrível!"):
        assert classificar_intencao(mensagem) == "reacao_espontanea"


def test_reacao_nao_gera_planejamento():
    instrucao = orientacao_conversacional("Nossa, me surpreendeu agora!")
    assert "não explique por que ele se surpreendeu" in instrucao
    assert "Não termine com pergunta automática" in instrucao


def test_pedidos_tecnicos_continuam_acao():
    assert classificar_intencao("Corrija o código") == "acao_solicitada"
    assert classificar_intencao("Faça sua autoevolução") == "autoevolucao_solicitada"
