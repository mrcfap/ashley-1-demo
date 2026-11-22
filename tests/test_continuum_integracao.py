import pytest
from app.continuum.integracao import rodar_ciclo, exemplos


def test_planner_critic_memoria_e_heldout(tmp_path):
    treino, inedito = exemplos()
    m, b = str(tmp_path/'mem.db'), str(tmp_path/'benchmark.db')
    antes = rodar_ciclo(treino, inedito, m, b)
    assert antes['treino_antes']['taxa'] == 0.5
    assert antes['treino_proposto']['taxa'] == 1
    assert antes['inedito']['taxa'] == 0.5
    assert not antes['promovida']
    depois = rodar_ciclo(treino, inedito, m, b, promover=True)
    assert depois['promovida']
    assert depois['inedito']['taxa'] == 1
    # Continuidade após reinicialização: instancia a memória novamente
    repeticao = rodar_ciclo(treino, inedito, m, b)
    assert repeticao['estrategia_ativa']
    assert repeticao['inedito']['taxa'] == 1


def test_impede_vazamento_entre_grupos(tmp_path):
    treino, _ = exemplos()
    duplicada = dict(treino[0], grupo='inedito')
    # O identificador completo inclui grupo; a verificação também deve detectar mesmo conteúdo.
    with pytest.raises(ValueError):
        rodar_ciclo(treino, [duplicada], str(tmp_path/'m.db'), str(tmp_path/'b.db'))
