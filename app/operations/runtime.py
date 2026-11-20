"""Ashley Runtime: diagnósticos locais, somente leitura, sem segredos."""
from __future__ import annotations
import importlib.util
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

COMPONENTS = {
    'api': 'app.API.app',
    'orchestrator': 'app.core.orquestrador',
    'humanity_v76': 'app.humanity_v76',
    'tasks_v22': 'app.tasks.motor_execucao_v22',
    'agents_phase5': 'app.agents.autonomous.phase5',
    'auth': 'app.security.auth',
}


def runtime_report(root: str | Path) -> dict:
    """Checagem passiva: não importa app, não abre rede, não modifica bancos."""
    root = Path(root).resolve()
    checks = {}
    for name, module in COMPONENTS.items():
        target = root.joinpath(*module.split('.'))
        exists = target.with_suffix('.py').is_file() or (target / '__init__.py').is_file()
        checks[name] = {'present': exists}
    for name, relative in {'auth_db':'data/auth_users.sqlite3', 'main_db':'data/ashley.db',
                           'coding_queue':'ashley_coding_v22.db'}.items():
        p = root / relative
        checks[name] = {'present': p.is_file(), 'size_bytes': p.stat().st_size if p.is_file() else None}
    return {'generated_at': datetime.now(timezone.utc).isoformat(),
            'root': str(root), 'checks': checks,
            'mode': 'read_only', 'production_ready': False,
            'note': 'Presença de arquivos não comprova saúde dos serviços ou integração.'}


def mission_report(db_path: str | Path, user_id: int, limit: int = 30) -> dict:
    """Consulta somente tarefas do usuário indicado. Uso CLI local, nunca expor sem auth."""
    if type(user_id) is not int or user_id < 1:
        raise ValueError('user_id positivo obrigatório')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit deve estar entre 1 e 100')
    db = Path(db_path).resolve()
    if not db.is_file():
        return {'available': False, 'tasks': [], 'count': 0}
    # URI read-only: não cria nem altera o arquivo
    conn = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=3)
    try:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute('''SELECT id, titulo, status, progresso, etapa_atual,
                       criado_em, atualizado_em, requer_aprovacao, aprovado
                       FROM tarefas_v22 WHERE user_id=? ORDER BY criado_em DESC LIMIT ?''',
                       (user_id, limit)).fetchall()
        except sqlite3.OperationalError as exc:
            if 'no such table' in str(exc).lower():
                return {'available': False, 'tasks': [], 'count': 0}
            raise
        tasks = [dict(r) for r in rows]
        return {'available': True, 'tasks': tasks, 'count': len(tasks), 'mode': 'read_only'}
    finally:
        conn.close()
