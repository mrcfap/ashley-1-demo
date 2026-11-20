from app.services.intencao_conversacional import classificar_intencao, orientacao_conversacional


def test_pedido_autoevolucao():
    for texto in (
        "você tem autonomia para estar evoluindo tem agentes para sua autoprogramação faça sua autoevolução",
        "Quero que você faça sua autoevolução",
        "Evolua seus agentes com segurança",
    ):
        assert classificar_intencao(texto) == "autoevolucao_solicitada"
        resposta = orientacao_conversacional(texto)
        assert "não pode" in resposta
        assert "sandbox" in resposta


def test_comunicado_nao_e_autoevolucao():
    assert classificar_intencao("Estou atualizando as melhorias depois testamos") == "compartilhamento"
