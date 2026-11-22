import pytest
from app.continuum.integracao import ciclo, exemplos

def test_ciclo_memoria_critico_planner(tmp_path):
    a,b=exemplos()
    m=str(tmp_path/"mem.db"); d=str(tmp_path/"metricas.db")
    inicial=ciclo(a,b,m,d)
    assert inicial["treino_antes"]["taxa"]==0.5
    assert inicial["inedito"]["taxa"]==0.5
    assert not inicial["promovida"]
    melhorado=ciclo(a,b,m,d,aprovar=True)
    assert melhorado["promovida"]
    assert melhorado["inedito"]["taxa"]==1
    assert ciclo(a,b,m,d)["estrategia_ativa"]

def test_sem_vazamento(tmp_path):
    a,_=exemplos()
    with pytest.raises(ValueError):
        ciclo(a,[dict(a[0],grupo="inedito")],str(tmp_path/"m.db"),str(tmp_path/"d.db"))
