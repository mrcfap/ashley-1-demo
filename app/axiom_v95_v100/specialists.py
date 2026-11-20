"""Axyntora specialist registry and bounded, non-executing governance checks.

These checks are advisory; they are not a replacement for authorization,
cryptography, sandbox isolation, clinical assessment or adversarial testing.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Specialist:
    id: str
    name: str
    responsibility: str
    implementation: str
    limitations: str

SPECIALISTS = (
    Specialist('sentinela', 'AXYNTORA SENTINELA', 'Segurança, permissões e memória', 'policy_scaffold', 'Não implementa criptografia, RAG ou defesa completa contra prompt injection.'),
    Specialist('sintonia', 'AXYNTORA SINTONIA', 'Comunicação e adaptação de tom', 'policy_scaffold', 'Não diagnostica emoções nem infere estados mentais com certeza.'),
    Specialist('praxis', 'AXYNTORA PRAXIS', 'Execução supervisionada', 'execution_disabled', 'Não executa shell, scripts, ferramentas ou APIs externas.'),
    Specialist('vigia', 'AXYNTORA VIGIA', 'Workers, filas e monitoramento', 'design_only', 'Sem workers em segundo plano ou agendamentos nesta entrega.'),
    Specialist('crivo', 'AXYNTORA CRIVO', 'Revisão adversarial', 'policy_scaffold', 'Não equivale a red teaming automatizado nem garante ausência de falhas.'),
)

BY_ID = {s.id: s for s in SPECIALISTS}


def catalog():
    return {'orchestrator': 'V100 AION SYMPHONY',
            'specialists': [asdict(s) for s in SPECIALISTS],
            'new_engine_numbers': [], 'all_specialists_operational': False}


def assess_request(data: dict):
    """Advisory planning only. Never executes a user-provided action."""
    if not isinstance(data, dict):
        raise ValueError('data deve ser um objeto')
    objective = data.get('objective', '')
    if not isinstance(objective, str) or not objective.strip() or len(objective) > 4000:
        raise ValueError('objective: texto obrigatório de até 4000 caracteres')
    requested = data.get('specialists', ['sentinela', 'sintonia', 'praxis', 'vigia', 'crivo'])
    if not isinstance(requested, list) or not requested or len(requested) > 5 or any(not isinstance(s, str) or s not in BY_ID for s in requested) or len(set(requested)) != len(requested):
        raise ValueError('specialists: lista única de identificadores válidos')
    sensitive = bool(data.get('sensitive_action', False))
    if not isinstance(data.get('sensitive_action', False), bool):
        raise ValueError('sensitive_action deve ser booleano')
    return {
        'objective': objective.strip(), 'orchestrator': 'V100 AION SYMPHONY',
        'selected_specialists': [asdict(BY_ID[s]) for s in requested],
        'status': 'planning_only', 'requires_human_approval': sensitive or 'praxis' in requested,
        'execution_authorized': False, 'tools_executed': False,
        'production_modified': False,
        'warnings': ['Análise consultiva: não substitui controles técnicos de segurança.',
                     'Nenhum agente especializado foi executado por um modelo nesta chamada.']
    }
