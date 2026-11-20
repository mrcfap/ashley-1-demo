from app.services.intencao_conversacional import (
    classificar_intencao, orientacao_conversacional,
)


def test_comunicado_nao_e_pedido():
    for frase in (
        "Agora estou atualizando suas melhorias depois testamos",
        "Vou trabalhar na memoria hoje",
        "Acabei de atualizar o sistema",
    ):
        assert classificar_intencao(frase) == "compartilhamento"
        assert "não ofereça" in orientacao_conversacional(frase)


def test_pedido_explicito_continua_possivel():
    for frase in (
        "Conserte e estruture as melhorias",
        "Faça uma auditoria completa",
        "Implemente a memória semântica",
    ):
        assert classificar_intencao(frase) == "acao_solicitada"


def test_pergunta_simples_sem_roteiro():
    assert classificar_intencao("Qual é o nome do meu cachorro?") == "conversa"
    assert "perguntado" in orientacao_conversacional("Qual é o nome do meu cachorro?")
