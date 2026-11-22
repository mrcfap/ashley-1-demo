import pytest
from app.adaptive_director.execucao_segura import Tarefa, executar_plano
from app.adaptive_director.recuperacao_contextual import recuperar_contexto
from app.adaptive_director.auditoria_codigo import auditar_codigo

def test_paralelo_e_dependencias():
    r = executar_plano([Tarefa("a", "analisar"), Tarefa("b", "revisar", ("a",))],
                       {"a": lambda: 1, "b": lambda: 2})
    assert r["resultados"]["b"]["status"] == "concluido"

def test_efeito_externo_exige_aprovacao():
    r = executar_plano([Tarefa("deploy", "publicar", efeito_externo=True)],
                       {"deploy": lambda: "publicado"})
    assert r["resultados"]["deploy"]["status"] == "aguardando_aprovacao"

def test_ciclo_rejeitado():
    with pytest.raises(ValueError):
        executar_plano([Tarefa("a", "a", ("b",)), Tarefa("b", "b", ("a",))], {})

def test_isolamento_memoria():
    docs = [{"id": "1", "usuario_id": 1, "texto": "projeto Axyntora", "consentimento": True},
            {"id": "2", "usuario_id": 2, "texto": "projeto Axyntora", "consentimento": True}]
    assert [x["id"] for x in recuperar_contexto("Axyntora", docs, usuario_id=1)] == ["1"]

def test_sem_consentimento():
    assert recuperar_contexto("teste", [{"id": "1", "usuario_id": 1, "texto": "teste"}], usuario_id=1) == []

def test_auditoria_estatica(tmp_path):
    (tmp_path / "exemplo.py").write_text("eval('1+1')")
    assert auditar_codigo(str(tmp_path))[0]["regra"] == "eval"
