"""Alertas persistentes de prazo para a caixa de entrada da conta."""

from datetime import date
from pathlib import Path
import sqlite3
from contextlib import closing


def _criar_tabela(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alertas_turno (
            tarefa_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            prazo TEXT NOT NULL,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (tarefa_id, user_id, prazo)
        )
    """)


def registrar_vencimentos(db: Path, hoje: date) -> int:
    with closing(sqlite3.connect(db, timeout=10)) as conn, conn:
        _criar_tabela(conn)
        if not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='tarefas_v22'"
        ).fetchone():
            return 0
        return conn.execute("""
            INSERT OR IGNORE INTO alertas_turno (tarefa_id, user_id, prazo)
            SELECT id, user_id, json_extract(metadados, '$.prazo')
              FROM tarefas_v22
             WHERE status NOT IN ('CONCLUIDA', 'CANCELADA', 'FALHOU')
               AND CASE WHEN json_valid(metadados) THEN
                   json_extract(metadados, '$.tipo') = 'passagem_turno'
                   AND date(json_extract(metadados, '$.prazo')) < ?
               END
        """, (hoje.isoformat(),)).rowcount


def listar_alertas(db: Path, user_id: int) -> list[dict]:
    with closing(sqlite3.connect(db, timeout=10)) as conn, conn:
        conn.row_factory = sqlite3.Row
        _criar_tabela(conn)
        return [dict(row) for row in conn.execute("""
            SELECT tarefa_id, prazo, criado_em FROM alertas_turno
             WHERE user_id = ?
             ORDER BY criado_em DESC, tarefa_id
             LIMIT 100
        """, (user_id,))]
