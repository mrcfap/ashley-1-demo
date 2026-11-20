"""Ashley V76 Humanity Core: consent-aware goals, evidence and decision plans.
No external model calls or autonomous actions. Standard library only.
"""
from __future__ import annotations
import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class HumanityCoreV76:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path, timeout=15)) as conn:
            conn.execute('PRAGMA busy_timeout=15000')
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS v76_consent (
                user_id TEXT PRIMARY KEY, enabled INTEGER NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS v76_goals (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS v76_events (
                id TEXT PRIMARY KEY, goal_id TEXT NOT NULL, user_id TEXT NOT NULL,
                note TEXT NOT NULL, evidence TEXT, confirmed INTEGER NOT NULL,
                created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_v76_goals_user ON v76_goals(user_id);
            CREATE INDEX IF NOT EXISTS idx_v76_events_user_goal ON v76_events(user_id,goal_id);
            ''')
            conn.commit()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA busy_timeout=15000')
        return conn

    @staticmethod
    def _check_user(user_id):
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError('user_id obrigatório')
        return user_id.strip()

    def consent(self, user_id: str, enabled: bool):
        user_id = self._check_user(user_id)
        if not isinstance(enabled, bool):
            raise ValueError('enabled deve ser booleano')
        with closing(self._connect()) as conn:
            with conn:
                conn.execute('INSERT INTO v76_consent VALUES (?,?,?) ON CONFLICT(user_id) DO UPDATE SET enabled=excluded.enabled,updated_at=excluded.updated_at',
                             (user_id, int(enabled), utcnow()))
        return {'user_id': user_id, 'enabled': enabled}

    def _require_consent(self, conn, user_id):
        row = conn.execute('SELECT enabled FROM v76_consent WHERE user_id=?', (user_id,)).fetchone()
        if row is None or not row['enabled']:
            raise PermissionError('Consentimento explícito necessário para o V76')

    def create_goal(self, user_id: str, title: str):
        user_id = self._check_user(user_id)
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 300:
            raise ValueError('Título deve ter de 1 a 300 caracteres')
        goal = {'id': str(uuid.uuid4()), 'user_id': user_id, 'title': title.strip(), 'status': 'active', 'created_at': utcnow()}
        with closing(self._connect()) as conn:
            with conn:
                self._require_consent(conn, user_id)
                conn.execute('INSERT INTO v76_goals VALUES (:id,:user_id,:title,:status,:created_at)', goal)
        return goal

    def list_goals(self, user_id: str):
        user_id = self._check_user(user_id)
        with closing(self._connect()) as conn:
            self._require_consent(conn, user_id)
            return [dict(r) for r in conn.execute('SELECT * FROM v76_goals WHERE user_id=? ORDER BY created_at,id', (user_id,))]

    def record_progress(self, user_id: str, goal_id: str, note: str, *, evidence: str | None = None, confirmed: bool = False):
        user_id = self._check_user(user_id)
        if not isinstance(note, str) or not 1 <= len(note.strip()) <= 2000:
            raise ValueError('Nota deve ter de 1 a 2000 caracteres')
        if evidence is not None and (not isinstance(evidence, str) or len(evidence) > 2000):
            raise ValueError('Evidência inválida')
        if not isinstance(confirmed, bool):
            raise ValueError('confirmed deve ser booleano')
        event = {'id': str(uuid.uuid4()), 'goal_id': goal_id, 'user_id': user_id,
                 'note': note.strip(), 'evidence': evidence, 'confirmed': int(confirmed), 'created_at': utcnow()}
        with closing(self._connect()) as conn:
            with conn:
                self._require_consent(conn, user_id)
                if not conn.execute('SELECT 1 FROM v76_goals WHERE id=? AND user_id=?', (goal_id, user_id)).fetchone():
                    raise LookupError('Objetivo não encontrado para este usuário')
                conn.execute('INSERT INTO v76_events VALUES (:id,:goal_id,:user_id,:note,:evidence,:confirmed,:created_at)', event)
        event['confirmed'] = confirmed
        return event

    def progress(self, user_id: str, goal_id: str):
        user_id = self._check_user(user_id)
        with closing(self._connect()) as conn:
            self._require_consent(conn, user_id)
            goal = conn.execute('SELECT * FROM v76_goals WHERE id=? AND user_id=?', (goal_id, user_id)).fetchone()
            if goal is None:
                raise LookupError('Objetivo não encontrado para este usuário')
            events = [dict(row) for row in conn.execute('SELECT * FROM v76_events WHERE goal_id=? AND user_id=? ORDER BY created_at,id', (goal_id, user_id))]
            for event in events:
                event['confirmed'] = bool(event['confirmed'])
            return {'goal': dict(goal), 'events': events, 'verified_outcomes': sum(bool(e['confirmed'] and e['evidence']) for e in events),
                    'disclaimer': 'Registros confirmados pelo usuário não equivalem a auditoria independente.'}

    def propose(self, user_id: str, message: str, *, requested_action: str = 'reflect'):
        """Non-executing deterministic decision plan; no inference of mental state."""
        user_id = self._check_user(user_id)
        if not isinstance(message, str) or not message.strip():
            raise ValueError('Mensagem obrigatória')
        with closing(self._connect()) as conn:
            self._require_consent(conn, user_id)
        allowed = {'reflect', 'plan', 'review'}
        if requested_action not in allowed:
            return {'decision': 'deny', 'executed': False, 'reason': 'Ação não autorizada pelo V76', 'requires_confirmation': True}
        return {'decision': 'suggest', 'executed': False, 'mode': requested_action,
                'suggestion': {'reflect': 'Perguntar qual objetivo é prioritário.',
                               'plan': 'Propor etapas verificáveis e solicitar aprovação.',
                               'review': 'Revisar registros e distinguir evidências de hipóteses.'}[requested_action],
                'reason': 'Proposta limitada ao pedido explícito; nenhuma ação externa foi executada.',
                'requires_confirmation': True, 'model_provider': 'none'}

    def delete_my_data(self, user_id: str):
        user_id = self._check_user(user_id)
        with closing(self._connect()) as conn:
            with conn:
                conn.execute('DELETE FROM v76_events WHERE user_id=?', (user_id,))
                conn.execute('DELETE FROM v76_goals WHERE user_id=?', (user_id,))
                conn.execute('DELETE FROM v76_consent WHERE user_id=?', (user_id,))
        return {'deleted': True, 'user_id': user_id}
