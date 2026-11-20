"""Coordenação auditável de propostas de código da Ashley.

Esta camada não chama modelos externos e não aplica alterações em produção.
A geração de candidatos pode ser conectada ao AutonomousCodingLoop existente.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re
import uuid
from datetime import datetime, timezone
from app.evolution.self_coding_engine import SelfCodingEngine

@dataclass
class Mission:
    id: str
    goal: str
    status: str
    created_at: str
    files: list[str]
    workspace: str | None = None
    report: dict | None = None

class CodingCoordinator:
    ROLES = ('planejador', 'arquiteto', 'programador', 'revisor', 'testador', 'documentador')

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.engine = SelfCodingEngine(self.root)
        self.log_dir = self.root / '.ashley_agent_missions'
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _save(self, mission: Mission):
        path = self.log_dir / (mission.id + '.json')
        path.write_text(json.dumps(asdict(mission), ensure_ascii=False, indent=2), encoding='utf-8')

    def create_mission(self, goal: str, files: list[str] | None = None) -> dict:
        if not goal.strip():
            raise ValueError('Objetivo obrigatório')
        selected = [str(self.engine._safe_relative(f)) for f in (files or [])]
        mission = Mission(id=uuid.uuid4().hex, goal=goal.strip(), status='AGUARDANDO_CANDIDATO',
                          created_at=datetime.now(timezone.utc).isoformat(), files=selected)
        self._save(mission)
        return asdict(mission)

    def analyze(self, mission_id: str, changes: dict[str, str]) -> dict:
        """Aplica alterações somente em workspace e produz relatório; nunca promove."""
        if not re.fullmatch(r'[0-9a-f]{32}', mission_id):
            raise ValueError('ID inválido')
        record = self.log_dir / (mission_id + '.json')
        data = json.loads(record.read_text(encoding='utf-8'))
        if data['status'] != 'AGUARDANDO_CANDIDATO':
            raise ValueError('Missão já processada')
        if not changes or len(changes) > 12:
            raise ValueError('Envie entre 1 e 12 arquivos')
        allowed = set(data['files'])
        for rel, content in changes.items():
            rel = str(self.engine._safe_relative(rel))
            if allowed and rel not in allowed:
                raise ValueError('Arquivo fora do escopo autorizado')
            if not isinstance(content, str) or len(content) > 250_000:
                raise ValueError('Conteúdo inválido ou excessivo')
        workspace = self.engine.criar_workspace(mission_id)
        diffs = {}
        for rel, content in changes.items():
            self.engine.aplicar_conteudo_candidato(workspace, rel, content)
            diffs[rel] = self.engine.diff(workspace, rel)
        risk = self.engine.avaliar_risco(list(changes), data['goal'])
        # Somente validação sintática; testes de código não confiável exigem isolamento externo.
        syntax = self.engine.validar_python(workspace)
        report = {'risk': risk, 'syntax': syntax, 'diffs': diffs,
                  'agents': {r: 'papel disponível para integração' for r in self.ROLES},
                  'production_modified': False,
                  'next_step': 'Revisão humana e testes em sandbox isolado antes de promover'}
        data.update(status='AGUARDANDO_REVISAO', workspace=str(workspace), report=report)
        record.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        return data

    def status(self, mission_id: str) -> dict:
        if not re.fullmatch(r'[0-9a-f]{32}', mission_id):
            raise ValueError('ID inválido')
        return json.loads((self.log_dir / (mission_id + '.json')).read_text(encoding='utf-8'))
