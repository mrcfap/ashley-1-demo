"""Fase 5: planejamento governado; nenhuma alteração em produção.

Usa a ponte V22 da Fase 4 para gerar propostas aprovadas. Não executa
código não confiável nem habilita sensores sem autorização.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence

@dataclass(frozen=True)
class Phase5Plan:
    goal: str
    files: tuple[str, ...]
    stages: tuple[str, ...]
    requires_human_approval: bool = True
    production_changes_allowed: bool = False
    automatic_tests_enabled: bool = False

class AutonomousCodingPhase5:
    def __init__(self, project_root, db_path=None, bridge=None):
        self.root = Path(project_root).resolve()
        if bridge is None:
            from app.agents.autonomous.phase4 import CodingV22Bridge
            bridge = CodingV22Bridge(self.root, db_path=db_path)
        self.bridge = bridge

    def plan(self, goal: str, files: Sequence[str]) -> dict:
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 2000:
            raise ValueError('Objetivo inválido')
        if not isinstance(files, (list, tuple)) or not 1 <= len(files) <= 4 or len(set(files)) != len(files):
            raise ValueError('Informe de 1 a 4 arquivos distintos')
        checked = []
        for filename in files:
            if not isinstance(filename, str):
                raise ValueError('Caminho inválido')
            candidate = self.root / filename
            if candidate.is_symlink():
                raise ValueError('Link simbólico não permitido')
            resolved = candidate.resolve()
            if not resolved.is_relative_to(self.root) or not resolved.is_file() or resolved.suffix != '.py' or resolved.stat().st_size > 18000:
                raise ValueError('Arquivo não permitido')
            checked.append(resolved.relative_to(self.root).as_posix())
        return asdict(Phase5Plan(goal.strip(), tuple(checked), (
            'planejar escopo', 'solicitar aprovação para geração',
            'gerar proposta em workspace isolado', 'revisar estaticamente',
            'registrar relatório e aguardar aprovação humana para promoção'
        )))

    def submit(self, user_id: int, goal: str, files: Sequence[str]) -> dict:
        plan = self.plan(goal, files)
        task = self.bridge.submit(user_id, plan['goal'], list(plan['files']))
        return {'plan': plan, 'task': task, 'note': 'A geração depende de aprovação explícita; nenhuma alteração de produção foi feita.'}

    def approve_generation(self, task_id: str, user_id: int):
        return self.bridge.approve_generation(task_id, user_id)

    async def run_approved(self, task_id: str, user_id: int):
        return await self.bridge.run_approved(task_id, user_id)
