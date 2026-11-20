import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ashley_memoria.db"

@contextmanager
def conectar():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.execute("PRAGMA busy_timeout=10000")
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def inicializar():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS triad_sessoes (
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                historico TEXT NOT NULL DEFAULT '[]',
                atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, session_id)
            )
        """)

def salvar(user_id, session_id, historico):
    dados = json.dumps(historico, ensure_ascii=False)
    with conectar() as conn:
        conn.execute("""
            INSERT INTO triad_sessoes (user_id, session_id, historico)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, session_id)
            DO UPDATE SET
                historico=excluded.historico,
                atualizado_em=CURRENT_TIMESTAMP
        """, (str(user_id), str(session_id), dados))

def carregar(user_id, session_id):
    with conectar() as conn:
        row = conn.execute("""
            SELECT historico FROM triad_sessoes
            WHERE user_id=? AND session_id=?
        """, (str(user_id), str(session_id))).fetchone()
    return json.loads(row[0]) if row else None

def excluir(user_id, session_id):
    with conectar() as conn:
        cursor = conn.execute("""
            DELETE FROM triad_sessoes
            WHERE user_id=? AND session_id=?
        """, (str(user_id), str(session_id)))
        return cursor.rowcount > 0
