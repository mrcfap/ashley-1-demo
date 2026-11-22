"""Continuum: medição offline reproduzível, sem ações externas ou autoevolução."""
import hashlib
import json
import sqlite3
import time
from pathlib import Path


def executar(tarefa):
    tipo = tarefa["tipo"]
    if tipo == "normalizar":
        return " ".join(str(tarefa["entrada"]).split()).casefold()
    if tipo == "somar":
        valores = tarefa["entrada"]
        if not isinstance(valores, list) or len(valores) > 100 or any(type(v) not in (int, float) for v in valores):
            raise ValueError("Entrada inválida")
        return sum(valores)
    if tipo == "extrair_campos":
        return {campo: tarefa["entrada"].get(campo) for campo in tarefa["campos"]}
    raise ValueError("Tipo não autorizado")


def avaliar(tarefas, caminho_banco):
    if not tarefas:
        raise ValueError("Sem tarefas")
    caminho_banco = Path(caminho_banco)
    caminho_banco.parent.mkdir(parents=True, exist_ok=True)
    resultados = []
    with sqlite3.connect(caminho_banco) as banco:
        banco.execute("""CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY, tarefa TEXT, grupo TEXT, sucesso INTEGER,
            duracao_ms REAL, criado_em REAL)""")
        for tarefa in tarefas:
            grupo = tarefa.get("grupo")
            if grupo not in ("treino", "inedito"):
                raise ValueError("Grupo inválido")
            inicio = time.perf_counter()
            try:
                acerto = executar(tarefa) == tarefa["esperado"]
            except (ValueError, KeyError, TypeError):
                acerto = False
            duracao = round((time.perf_counter() - inicio) * 1000, 3)
            identificador = hashlib.sha256(json.dumps(tarefa, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
            banco.execute("INSERT INTO resultados(tarefa, grupo, sucesso, duracao_ms, criado_em) VALUES (?,?,?,?,?)",
                          (identificador, grupo, int(acerto), duracao, time.time()))
            resultados.append({"id": identificador, "grupo": grupo, "sucesso": acerto, "duracao_ms": duracao})
    resumo = {}
    for grupo in ("treino", "inedito"):
        itens = [r for r in resultados if r["grupo"] == grupo]
        resumo[grupo] = {"total": len(itens), "acertos": sum(r["sucesso"] for r in itens),
                         "taxa": sum(r["sucesso"] for r in itens) / len(itens) if itens else None}
    return {"resumo": resumo, "resultados": resultados,
            "limite": "Benchmark offline sintético; não comprova aprendizado autônomo."}
