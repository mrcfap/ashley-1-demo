"""Fase 3: revisão multiagente de propostas, sem execução ou promoção de código."""
from __future__ import annotations
import ast
import json
from pathlib import Path
from app.agents.autonomous.phase2 import AutonomousCodingPhase2

class AutonomousCodingPhase3(AutonomousCodingPhase2):
    """Fluxo: planejador -> programador (Fase 2) -> revisor -> documentador.

    A revisão estática é local; os papéis ainda não são modelos independentes.
    """
    def review_static(self, changes: dict[str, str]) -> dict:
        findings = []
        for name, source in changes.items():
            if not name.endswith('.py'):
                findings.append({'file': name, 'severity': 'block', 'reason': 'Apenas Python'})
                continue
            try:
                tree = ast.parse(source, filename=name)
            except SyntaxError as exc:
                findings.append({'file': name, 'severity': 'block', 'reason': f'Sintaxe: {exc.msg}'})
                continue
            risky_calls = {'eval', 'exec', 'compile', '__import__'}
            risky_imports = {'subprocess', 'ctypes', 'pickle'}
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in risky_calls:
                    findings.append({'file': name, 'severity': 'review', 'reason': f'Chamada sensível: {node.func.id}'})
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] in risky_imports:
                            findings.append({'file': name, 'severity': 'review', 'reason': f'Importação sensível: {alias.name}'})
                if isinstance(node, ast.ImportFrom) and (node.module or '').split('.')[0] in risky_imports:
                    findings.append({'file': name, 'severity': 'review', 'reason': f'Importação sensível: {node.module}'})
        return {'approved_for_production': False, 'requires_human_review': True,
                'static_findings': findings, 'syntax_ok': not any(f['severity']=='block' for f in findings),
                'sandbox_tests_executed': False}

    async def propose_and_review(self, goal: str, files: list[str]) -> dict:
        result = await self.propose(goal, files)
        workspace = Path(result['workspace']).resolve()
        if not workspace.is_relative_to(self.root):
            raise ValueError('Workspace fora da raiz do projeto')
        changes = {}
        for name in files:
            path = (workspace / name).resolve()
            if not path.is_relative_to(workspace) or not path.is_file() or path.is_symlink():
                raise ValueError('Arquivo candidato inválido')
            changes[name] = path.read_text(encoding='utf-8')
        review = self.review_static(changes)
        result['phase3_review'] = review
        result['phase3_roles'] = {'planejador':'escopo definido pelo usuário',
            'programador':'proposta gerada pela Fase 2', 'revisor':'revisão estática local',
            'testador':'não executado; requer sandbox externo',
            'documentador':'relatório de diferenças da Fase 2'}
        result['integration_v22'] = 'pendente; nenhuma tarefa V22 disparada'
        record = self.coordinator.log_dir / (result['id'] + '.json')
        state = json.loads(record.read_text(encoding='utf-8'))
        state['phase3_review'] = review
        state['phase3_roles'] = result['phase3_roles']
        record.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        return result
