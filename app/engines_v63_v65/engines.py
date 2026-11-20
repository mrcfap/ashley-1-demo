"""Ashley V63-V65: núcleo independente e supervisionado.

Sem inferência clínica, sem chamadas externas e sem ações automáticas.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Literal
import uuid


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Suggestion:
    level: Literal['baixo', 'moderado', 'elevado']
    explanation: str
    options: tuple[str, ...]
    clinical_diagnosis: bool = False


class PsycheSynapseV63:
    """Sugestões de organização baseadas SOMENTE em carga autodeclarada.

    Não avalia saúde mental, voz, rosto ou empregados; não executa ações.
    """
    def suggest(self, workload: float, *, consent: bool, context: str = 'pessoal') -> Suggestion:
        if not consent:
            raise PermissionError('Consentimento necessário para esta avaliação voluntária')
        if not isinstance(workload, (float, int)) or isinstance(workload, bool) or not 0 <= workload <= 10:
            raise ValueError('Carga autodeclarada deve estar entre 0 e 10')
        if context not in ('pessoal', 'corporativo'):
            raise ValueError('Contexto inválido')
        if workload >= 8:
            return Suggestion('elevado', 'Carga autodeclarada alta; isto não é avaliação clínica.',
                              ('Revisar prioridades com a pessoa', 'Propor redistribuição somente com aprovação', 'Considerar uma pausa'))
        if workload >= 5:
            return Suggestion('moderado', 'Carga autodeclarada moderada; sem inferência emocional.',
                              ('Revisar prazos', 'Escolher uma tarefa prioritária'))
        return Suggestion('baixo', 'Carga autodeclarada baixa; sem conclusão sobre saúde.',
                          ('Manter a organização escolhida pela pessoa',))


@dataclass
class Outcome:
    id: str
    owner_id: str
    objective: str
    status: str
    evidence: str | None
    updated_at: str


class RealityBridgeV64:
    """Prova de resultado: planejar não equivale a concluir.

    Armazenamento em memória somente para testes/integração posterior.
    """
    def __init__(self):
        self._items: dict[str, Outcome] = {}

    def plan(self, owner_id: str, objective: str) -> dict:
        if not owner_id.strip() or not objective.strip():
            raise ValueError('Responsável e objetivo são obrigatórios')
        item = Outcome(str(uuid.uuid4()), owner_id, objective, 'PLANEJADO', None, now())
        self._items[item.id] = item
        return asdict(item)

    def submit_evidence(self, owner_id: str, item_id: str, evidence: str) -> dict:
        item = self._owned(owner_id, item_id)
        if item.status != 'PLANEJADO' or not evidence.strip():
            raise ValueError('Estado ou evidência inválidos')
        item.status, item.evidence, item.updated_at = 'AGUARDANDO_VERIFICACAO', evidence, now()
        return asdict(item)

    def verify(self, owner_id: str, item_id: str, *, approved_by_human: bool) -> dict:
        item = self._owned(owner_id, item_id)
        if item.status != 'AGUARDANDO_VERIFICACAO':
            raise ValueError('Não há evidência pendente')
        if not approved_by_human:
            return asdict(item)
        item.status, item.updated_at = 'CONFIRMADO_POR_PESSOA', now()
        return asdict(item)

    def _owned(self, owner_id: str, item_id: str) -> Outcome:
        item = self._items.get(item_id)
        if item is None or item.owner_id != owner_id:
            raise KeyError('Registro não encontrado')
        return item


class EpistemicCoreV65:
    """Rotula origem de afirmações sem inventar prova ou grau de certeza."""
    SOURCES = {'observacao', 'documento', 'memoria', 'inferencia', 'desconhecido'}

    def assess(self, claim: str, source: str, *, evidence: str | None = None,
               independently_verified: bool = False) -> dict:
        if not claim.strip() or source not in self.SOURCES:
            raise ValueError('Afirmação ou origem inválida')
        if independently_verified and (source not in ('observacao', 'documento') or not evidence or not evidence.strip()):
            raise ValueError('Verificação requer evidência observável/documental')
        label = 'VERIFICADO_COM_EVIDENCIA_DECLARADA' if independently_verified else 'NAO_VERIFICADO'
        return {'claim': claim, 'source': source, 'evidence': evidence,
                'status': label, 'requires_review': not independently_verified,
                'note': 'O rótulo de verificação depende da validação externa da evidência; não é prova automática.'}
