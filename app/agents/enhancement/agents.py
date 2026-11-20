"""Oito agentes de aprimoramento, protótipos determinísticos e sem efeitos externos.

Não executam comandos, não acessam rede, não modificam motores e não fazem
aprendizado automático. Integração com API/orquestrador exige homologação.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import hashlib
import json
import math
import uuid


def _now():
    return datetime.now(timezone.utc).isoformat()


def _required(value: str, name: str):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} obrigatório")
    if len(value) > 4096:
        raise ValueError(f"{name} excede o limite")


@dataclass
class Evidence:
    reference: str
    assertion: str
    kind: str = 'observation'
    verified: bool = False
    created_at: str = field(default_factory=_now)


class MNEMOSYNE:
    """Memória revisável em RAM; somente registros consentidos e referenciados."""
    def __init__(self):
        self._items: dict[str, dict] = {}

    def remember(self, namespace: str, assertion: str, evidence_ref: str, *, consent: bool):
        for name, value in [('namespace', namespace), ('assertion', assertion), ('evidence_ref', evidence_ref)]:
            _required(value, name)
        if not consent:
            raise PermissionError('Consentimento explícito necessário')
        ident = uuid.uuid4().hex
        self._items[ident] = {'id': ident, 'namespace': namespace, 'assertion': assertion,
                              'evidence_ref': evidence_ref, 'status': 'unverified', 'created_at': _now()}
        return ident

    def review(self, ident: str, *, verified: bool, approved: bool):
        if not approved:
            raise PermissionError('Revisão exige aprovação')
        self._items[ident]['status'] = 'verified' if verified else 'disputed'
        return dict(self._items[ident])

    def recall(self, namespace: str):
        return [dict(v) for v in self._items.values() if v['namespace'] == namespace]

    def forget(self, ident: str):
        return self._items.pop(ident, None) is not None


class ATLAS:
    """Máquina de estados de missões; não executa a tarefa."""
    transitions = {'draft': {'approved', 'cancelled'}, 'approved': {'running', 'cancelled'},
                   'running': {'paused', 'completed', 'failed'}, 'paused': {'running', 'cancelled'},
                   'failed': {'approved'}, 'completed': set(), 'cancelled': set()}
    def __init__(self):
        self._missions = {}

    def create(self, goal: str):
        _required(goal, 'goal')
        ident = uuid.uuid4().hex
        self._missions[ident] = {'id': ident, 'goal': goal, 'status': 'draft', 'history': [('draft', _now())]}
        return ident

    def transition(self, ident: str, status: str, *, approved: bool = False):
        mission = self._missions[ident]
        if status not in self.transitions[mission['status']]:
            raise ValueError('Transição de estado inválida')
        if status in ('approved', 'running') and not approved:
            raise PermissionError('Autorização necessária')
        mission['status'] = status
        mission['history'].append((status, _now()))
        return dict(mission)


class SPECTRA:
    """Organiza referências de eventos multimodais; não interpreta imagens/áudio."""
    channels = frozenset({'text', 'audio', 'image', 'video', 'document'})
    def __init__(self):
        self._events = []

    def ingest_reference(self, channel: str, ref: str, timestamp_ms: int, *, consent: bool):
        if not consent:
            raise PermissionError('Permissão de processamento necessária')
        if channel not in self.channels or not isinstance(timestamp_ms, int) or timestamp_ms < 0:
            raise ValueError('Canal ou tempo inválido')
        _required(ref, 'ref')
        event = {'channel': channel, 'ref': ref, 'timestamp_ms': timestamp_ms}
        self._events.append(event)
        return dict(event)

    def timeline(self):
        return sorted((dict(e) for e in self._events), key=lambda x: x['timestamp_ms'])


class DARWIN:
    """Gates de evolução; sem escrita em arquivos ou deploy."""
    def assess(self, change_id: str, checks: dict[str, bool], *, human_approved: bool):
        _required(change_id, 'change_id')
        required = {'syntax', 'tests', 'security', 'rollback'}
        if not required.issubset(checks) or any(type(checks[k]) is not bool for k in required):
            raise ValueError('Checks obrigatórios ausentes/inválidos')
        passed = all(checks[k] for k in required)
        return {'change_id': change_id, 'checks_passed': passed,
                'human_approved': human_approved, 'eligible_for_manual_review': passed and human_approved,
                'deployed': False}


class IMPACT:
    """Métricas de resultado com referência de evidência, sem alegar causalidade."""
    def compare(self, metric: str, baseline: float, observed: float, evidence_ref: str):
        _required(metric, 'metric'); _required(evidence_ref, 'evidence_ref')
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (baseline, observed)):
            raise ValueError('Valores precisam ser números finitos')
        delta = observed - baseline
        return {'metric': metric, 'baseline': baseline, 'observed': observed, 'delta': delta,
                'relative_change': delta / abs(baseline) if baseline else None,
                'evidence_ref': evidence_ref, 'causal_claim': False}


class ORACLE:
    """Cenários aritméticos explícitos, sem capacidade preditiva autônoma."""
    def scenarios(self, base: float, changes: dict[str, float]):
        if not isinstance(base, (int, float)) or not math.isfinite(base):
            raise ValueError('Base inválida')
        if not changes or len(changes) > 30:
            raise ValueError('Informe de 1 a 30 cenários')
        results = {}
        for name, rate in changes.items():
            _required(name, 'scenario')
            if not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate < -1:
                raise ValueError('Taxa inválida')
            results[name] = base * (1 + rate)
        return {'base': base, 'scenarios': results, 'forecast': False, 'assumptions_supplied_by_user': True}


class IMMUNIS:
    """Política local fail-closed de ações; não substitui autenticação do servidor."""
    sensitive = frozenset({'delete', 'deploy', 'payment', 'send', 'camera', 'microphone', 'write_code'})
    def authorize(self, action: str, permissions: set[str], *, human_approved: bool = False):
        _required(action, 'action')
        if action not in permissions:
            return {'allowed': False, 'reason': 'permission_denied'}
        if action in self.sensitive and not human_approved:
            return {'allowed': False, 'reason': 'human_approval_required'}
        return {'allowed': True, 'reason': 'policy_passed_not_executed'}


class METACORE:
    """Avalia indicadores fornecidos; não altera pesos/modelos automaticamente."""
    def evaluate(self, indicators: dict[str, float], thresholds: dict[str, float]):
        if not indicators or set(indicators) != set(thresholds):
            raise ValueError('Indicadores e limiares devem corresponder')
        findings = []
        for name, value in indicators.items():
            _required(name, 'indicator')
            target = thresholds[name]
            if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in (value, target)):
                raise ValueError('Indicador não finito')
            if value < target:
                findings.append({'indicator': name, 'observed': value, 'minimum': target, 'gap': target - value})
        findings.sort(key=lambda item: item['gap'], reverse=True)
        return {'passed': not findings, 'findings': findings, 'automatic_changes': False}


AGENTS = {cls.__name__: cls for cls in (MNEMOSYNE, ATLAS, SPECTRA, DARWIN, IMPACT, ORACLE, IMMUNIS, METACORE)}
