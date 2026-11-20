from app.pragmatics import PragmaticaHumana


def test_humor_e_metafora():
    a = PragmaticaHumana.analisar("kkkk, estamos chegando lá, foi uma metáfora!")
    assert "humor_ou_brincadeira" in a["pistas"]
    assert "linguagem_nao_literal" in a["pistas"]
    assert "sem corrigir uma brincadeira" in PragmaticaHumana.instrucoes(a)


def test_reparo():
    a = PragmaticaHumana.analisar("Você entendeu errado, eu quis dizer outra coisa")
    assert "reparo_de_entendimento" in a["pistas"]


def test_neutro_e_privacidade():
    assert PragmaticaHumana.instrucoes(PragmaticaHumana.analisar("Qual é a capital do Brasil?")) == ""
    assert not hasattr(PragmaticaHumana(), "db_path")


def test_comentario_sem_aula():
    a = PragmaticaHumana.analisar("Eu sei disso, foi um comentário")
    assert "comentario_sem_pedido_de_aula" in a["pistas"]
