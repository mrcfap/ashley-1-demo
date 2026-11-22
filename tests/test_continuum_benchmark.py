import pytest
from app.continuum.benchmark import avaliar, executar


def test_registra_acertos(tmp_path):
    tarefas = [
        {"tipo": "somar", "entrada": [2, 3], "esperado": 5, "grupo": "treino"},
        {"tipo": "normalizar", "entrada": " OI  MUNDO ", "esperado": "oi mundo", "grupo": "inedito"},
    ]
    resultado = avaliar(tarefas, tmp_path / "teste.db")
    assert resultado["resumo"]["treino"]["taxa"] == 1
    assert resultado["resumo"]["inedito"]["taxa"] == 1


def test_bloqueia_codigo_arbitrario():
    with pytest.raises(ValueError):
        executar({"tipo": "python", "entrada": "print(1)"})


def test_contabiliza_falha(tmp_path):
    tarefa = {"tipo": "somar", "entrada": ["x"], "esperado": 1, "grupo": "inedito"}
    assert avaliar([tarefa], tmp_path / "teste.db")["resumo"]["inedito"]["taxa"] == 0
