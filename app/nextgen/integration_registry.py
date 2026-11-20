"""Inventário verificável da integração, sem importar ou executar motores.

Referências em arquivos não comprovam funcionamento. A varredura é somente leitura.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'
ENGINE_PATTERN = re.compile(r'(?<![a-zA-Z0-9])v0*([1-9]|[1-7][0-9]|8[0-4])(?![0-9])', re.I)


def inventory() -> dict:
    discovered: dict[int, set[str]] = {i: set() for i in range(1, 85)}
    parse_errors: list[str] = []
    files = 0
    for path in sorted(APP.rglob('*.py')):
        if any(part in {'__pycache__', 'backups', '.ashley_evolution_workspaces'} for part in path.parts):
            continue
        files += 1
        relative = path.relative_to(ROOT).as_posix()
        try:
            source = path.read_text(encoding='utf-8-sig')
            tree = ast.parse(source, filename=relative)
        except (OSError, UnicodeError, SyntaxError) as exc:
            parse_errors.append(f'{relative}: {type(exc).__name__}')
            continue
        # Apenas identificadores de símbolos e caminhos, não texto de comentários.
        identifiers = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
        identifiers += [node.name for node in ast.walk(tree) if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
        identifiers += [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
        identifiers.append(path.stem)
        for token in identifiers:
            for match in ENGINE_PATTERN.finditer(token.replace('_', ' ')):
                discovered[int(match.group(1))].add(relative)
    engines = [
        {'motor': f'V{i}', 'symbol_references': sorted(discovered[i]),
         'status': 'referenciado_nao_homologado' if discovered[i] else 'nao_identificado_por_simbolo'}
        for i in range(1, 85)
    ]
    return {'range': 'V1-V84', 'files_parsed_attempted': files,
            'engines': engines, 'parse_errors': parse_errors,
            'all_engines_operational': False,
            'method': 'static_ast_symbol_inventory_no_import_no_execution'}


def agent_catalog() -> dict:
    return {'roles': ['planejador', 'arquiteto', 'programador', 'revisor', 'testador', 'documentador'],
            'coordinator': 'app.agents.autonomous.coordinator.CodingCoordinator',
            'mode': 'workspace_only_human_review',
            'roles_executed': False, 'production_write_authorized': False}
