"""Política explícita de esforço para tarefas, sem prometer raciocínio interno do provedor."""
from dataclasses import dataclass
from typing import Literal

Nivel = Literal["baixo", "medio", "alto", "maximo"]

@dataclass(frozen=True)
class OrcamentoTarefa:
    nivel: Nivel
    max_etapas: int
    max_revisoes: int
    exige_aprovacao_externa: bool = True

CONFIG = {
    "baixo": (2, 0),
    "medio": (5, 1),
    "alto": (10, 2),
    "maximo": (20, 3),
}

def planejar_esforco(nivel: Nivel = "medio") -> OrcamentoTarefa:
    """Limita etapas/revisões do orquestrador; não altera tokens de pensamento do LLM."""
    if nivel not in CONFIG:
        raise ValueError("Nível de esforço inválido")
    etapas, revisoes = CONFIG[nivel]
    return OrcamentoTarefa(nivel, etapas, revisoes)
