from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class AnamnesisV71:
    """Explicit opt-in personal milestones. No emotional inference or unsolicited reminders."""
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS milestones (
                id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, label TEXT NOT NULL,
                event_date TEXT, sensitivity TEXT NOT NULL, created_at TEXT NOT NULL)''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_milestone_owner ON milestones(owner_id)')

    @contextmanager
    def _connect(self):
        """Commit/rollback and always close SQLite handle (required on Windows)."""
        db = sqlite3.connect(str(self.db_path), timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def add(self, owner_id, label, *, consent=False, event_date=None, sensitivity='personal'):
        if consent is not True:
            raise PermissionError('Consentimento explicito necessario')
        label = label.strip()
        if not label or len(label) > 300:
            raise ValueError('Marco biografico invalido')
        if sensitivity not in ('personal', 'sensitive'):
            raise ValueError('Classificacao invalida')
        if event_date:
            from datetime import date
            date.fromisoformat(event_date)
        record_id = str(uuid4())
        with self._connect() as db:
            db.execute('INSERT INTO milestones VALUES (?,?,?,?,?,?)',
                       (record_id, str(owner_id), label, event_date, sensitivity, utc_now()))
        return {'id': record_id, 'label': label, 'event_date': event_date, 'sensitivity': sensitivity}

    def list(self, owner_id):
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute('SELECT id,label,event_date,sensitivity FROM milestones WHERE owner_id=? ORDER BY created_at DESC', (str(owner_id),)).fetchall()
            return [dict(row) for row in rows]

    def delete(self, owner_id, record_id):
        with self._connect() as db:
            cur = db.execute('DELETE FROM milestones WHERE owner_id=? AND id=?', (str(owner_id), record_id))
            return cur.rowcount == 1


class ResonanceSilenceV72:
    """Explicit user pacing, not diagnosis or inferred emotion."""
    def plan(self, *, preference='normal', message='', urgent=False):
        if preference not in ('normal', 'brief', 'quiet'):
            raise ValueError('Preferencia invalida')
        # User safety takes priority over silence; downstream safety handler must evaluate content.
        if urgent:
            return {'mode': 'safety_priority', 'max_words': 120, 'allow_followup': True,
                    'instruction': 'Nao suprima informacoes de seguranca urgentes. Encaminhe ao fluxo de seguranca.'}
        if preference == 'quiet':
            return {'mode': 'quiet', 'max_words': 20, 'allow_followup': False,
                    'instruction': 'Responda brevemente, sem perguntas desnecessarias, sem alegar sentimentos ou presenca fisica.'}
        if preference == 'brief':
            return {'mode': 'brief', 'max_words': 50, 'allow_followup': False,
                    'instruction': 'Priorize uma resposta breve e objetiva; respeite pedidos de silencio.'}
        return {'mode': 'normal', 'max_words': 180, 'allow_followup': True,
                'instruction': 'Responda conforme o pedido, sem afirmar conhecer estados emocionais nao informados.'}
