from app.services.intencao_conversacional import classificar_intencao, orientacao_conversacional


def test_diferenciais_mercado():
    pergunta = "me fale dos seus diferenciais das IA que já tem aí no mercado"
    assert classificar_intencao(pergunta) == "diferenciais_axyntora"
    instrucao = orientacao_conversacional(pergunta)
    assert "memória persistente" in instrucao
    assert "sem encerrar oferecendo auditoria" in instrucao


def test_diferenciais_axyntora():
    assert classificar_intencao("Quais os diferenciais da Axyntora?") == "diferenciais_axyntora"


def test_acao_tecnica_continua():
    assert classificar_intencao("corrija o código do chat") == "acao_solicitada"
