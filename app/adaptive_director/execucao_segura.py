"""Planejamento e execução segura, sem efeitos externos automáticos."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Mapping
from app.adaptive_director.politica_esforco import planejar_esforco

@dataclass(frozen=True)
class Tarefa:
    identificador: str
    descricao: str
    depende_de: tuple[str, ...] = ()
    efeito_externo: bool = False


def executar_plano(tarefas: list[Tarefa], ferramentas: Mapping[str, Callable[[], object]],
                   *, nivel: str = "medio", aprovadas: frozenset[str] = frozenset(),
                   trabalhadores: int = 3) -> dict:
    """Executa tarefas aprovadas; recusa dependências inválidas e ciclos.

    Ferramentas são injetadas pelo chamador; nenhuma ação externa ocorre sem aprovação.
    """
    limite = planejar_esforco(nivel)
    if len(tarefas) > limite.max_etapas or trabalhadores < 1 or trabalhadores > 8:
        raise ValueError("Orçamento de execução excedido")
    ids = [t.identificador for t in tarefas]
    if any(not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Identificadores inválidos ou duplicados")
    existentes = set(ids)
    if any(set(t.depende_de) - existentes or t.identificador in t.depende_de for t in tarefas):
        raise ValueError("Dependência inválida")
    pendentes = {t.identificador: t for t in tarefas}
    resultados = {}
    while pendentes:
        prontos = [t for t in pendentes.values() if set(t.depende_de) <= resultados.keys()]
        if not prontos:
            raise ValueError("Dependências cíclicas")
        with ThreadPoolExecutor(max_workers=trabalhadores) as pool:
            futures = {}
            for t in prontos:
                if t.efeito_externo and t.identificador not in aprovadas:
                    resultados[t.identificador] = {"status": "aguardando_aprovacao"}
                elif any(resultados[x]["status"] != "concluido" for x in t.depende_de):
                    resultados[t.identificador] = {"status": "bloqueado_por_dependencia"}
                elif t.identificador not in ferramentas:
                    resultados[t.identificador] = {"status": "ferramenta_indisponivel"}
                else:
                    futures[t.identificador] = pool.submit(ferramentas[t.identificador])
            for identificador, future in futures.items():
                try:
                    resultados[identificador] = {"status": "concluido", "resultado": future.result()}
                except Exception as exc:
                    resultados[identificador] = {"status": "falhou", "erro_tipo": type(exc).__name__}
        for t in prontos:
            pendentes.pop(t.identificador)
    return {"nivel": nivel, "resultados": resultados}
