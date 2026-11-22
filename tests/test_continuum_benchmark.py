import pytest
from app.continuum.benchmark import avaliar, executar, tarefas_exemplo


def test_baseline_reprodutivel(tmp_path):
    report=avaliar(tarefas_exemplo(),tmp_path/'out.db')
    assert report['resumo']['treino']['taxa']==1
    assert report['resumo']['inedito']['taxa']==1
    assert (tmp_path/'out.db').exists()


def test_rejeita_execucao_arbitraria():
    with pytest.raises(ValueError):
        executar({'tipo':'python','entrada':'print(1)'})


def test_erro_contabilizado(tmp_path):
    task={'tipo':'somar','entrada':['abc'],'esperado':1,'grupo':'inedito'}
    assert avaliar([task],tmp_path/'out.db')['resumo']['inedito']['taxa']==0
