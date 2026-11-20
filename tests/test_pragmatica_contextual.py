from app.pragmatics import PragmaticaHumana


def test_escuta_sem_conselho():
    p = PragmaticaHumana.analisar('Só quero desabafar, não quero conselho')
    assert 'pedido_de_escuta' in p['pistas']
    assert 'não dê conselhos' in PragmaticaHumana.instrucoes(p)


def test_reparo_sem_defensividade():
    p = PragmaticaHumana.analisar('Você levou ao pé da letra, era uma metáfora')
    assert 'reparo_de_entendimento' in p['pistas']
    assert 'linguagem_nao_literal' in p['pistas']


def test_modo_analitico_e_conciso():
    assert 'pedido_de_analise' in PragmaticaHumana.analisar('Quero uma análise dos dados')['pistas']
    assert 'pedido_de_objetividade' in PragmaticaHumana.analisar('Vai direto ao ponto')['pistas']


def test_consentimento_e_ausencia_de_persistencia():
    p = PragmaticaHumana.analisar('Pergunte antes de agir')
    assert 'pedido_de_confirmacao' in p['pistas']
    assert not hasattr(PragmaticaHumana(), 'db_path')
