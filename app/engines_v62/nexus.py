"""V62 PRAXIS-NEXUS: planejamento e acompanhamento social supervisionado.

Núcleo de domínio independente de FastAPI. Nenhuma ação externa é executada.
O chamador deve obter user_id da autenticação da Ashley, não de parâmetros livres.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import uuid


def now():
    return datetime.now(timezone.utc).isoformat()


class NexusEngine:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS nexus_projects (
                    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL,
                    title TEXT NOT NULL, purpose TEXT NOT NULL,
                    community TEXT NOT NULL, status TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS nexus_steps (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
                    description TEXT NOT NULL, status TEXT NOT NULL,
                    evidence TEXT, confirmed_by TEXT, confirmed_at TEXT,
                    FOREIGN KEY(project_id) REFERENCES nexus_projects(id)
                );
                CREATE INDEX IF NOT EXISTS idx_nexus_owner ON nexus_projects(owner_id);
                CREATE INDEX IF NOT EXISTS idx_nexus_steps ON nexus_steps(project_id);
            """)

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def create_project(self, *, owner_id: str, title: str, purpose: str,
                       community: str, steps: list[str]) -> dict:
        if not all(isinstance(v, str) and v.strip() for v in (owner_id, title, purpose, community)):
            raise ValueError('Campos obrigatórios não podem estar vazios')
        if not isinstance(steps, list) or not 1 <= len(steps) <= 100 or any(not isinstance(s, str) or not s.strip() for s in steps):
            raise ValueError('Informe de 1 a 100 etapas válidas')
        pid, timestamp = str(uuid.uuid4()), now()
        with self._db() as conn:
            conn.execute('INSERT INTO nexus_projects VALUES (?,?,?,?,?,?,?,?)',
                         (pid, owner_id, title.strip(), purpose.strip(), community.strip(), 'PLANEJADO', timestamp, timestamp))
            for step in steps:
                conn.execute('INSERT INTO nexus_steps(id,project_id,description,status) VALUES (?,?,?,?)',
                             (str(uuid.uuid4()), pid, step.strip(), 'PENDENTE'))
        return self.get_project(owner_id=owner_id, project_id=pid)

    def get_project(self, *, owner_id: str, project_id: str) -> dict | None:
        with self._db() as conn:
            p = conn.execute('SELECT * FROM nexus_projects WHERE id=? AND owner_id=?', (project_id, owner_id)).fetchone()
            if p is None:
                return None
            steps = conn.execute('SELECT * FROM nexus_steps WHERE project_id=? ORDER BY rowid', (project_id,)).fetchall()
            return {'project': dict(p), 'steps': [dict(s) for s in steps]}

    def list_projects(self, *, owner_id: str) -> list[dict]:
        with self._db() as conn:
            return [dict(r) for r in conn.execute('SELECT * FROM nexus_projects WHERE owner_id=? ORDER BY created_at DESC', (owner_id,))]

    def report_step(self, *, owner_id: str, project_id: str, step_id: str, evidence: str) -> bool:
        """Registra alegação de conclusão, SEM declará-la confirmada."""
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError('Evidência descritiva obrigatória')
        with self._db() as conn:
            cur = conn.execute('''UPDATE nexus_steps SET status='AGUARDANDO_CONFIRMACAO', evidence=?,
                confirmed_by=NULL, confirmed_at=NULL WHERE id=? AND project_id=?
                AND EXISTS (SELECT 1 FROM nexus_projects WHERE id=? AND owner_id=?)''',
                (evidence.strip(), step_id, project_id, project_id, owner_id))
            return cur.rowcount == 1

    def confirm_step(self, *, owner_id: str, project_id: str, step_id: str, approver_id: str) -> bool:
        """A API deve autenticar e autorizar approver_id antes de chamar este método."""
        if not approver_id or approver_id != owner_id:
            raise PermissionError('Confirmação requer proprietário autenticado')
        with self._db() as conn:
            cur = conn.execute('''UPDATE nexus_steps SET status='CONFIRMADA', confirmed_by=?, confirmed_at=?
                WHERE id=? AND project_id=? AND status='AGUARDANDO_CONFIRMACAO'
                AND EXISTS (SELECT 1 FROM nexus_projects WHERE id=? AND owner_id=?)''',
                (approver_id, now(), step_id, project_id, project_id, owner_id))
            return cur.rowcount == 1
