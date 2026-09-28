import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class MemoriaLongoPrazo:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS memoria_longo_prazo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    categoria TEXT NOT NULL,
                    chave TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    importancia REAL NOT NULL DEFAULT 0.7,
                    permanencia REAL NOT NULL DEFAULT 0.8,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    UNIQUE(user_id, categoria, chave)
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS interacoes_longo_prazo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    entrada TEXT NOT NULL,
                    resposta TEXT NOT NULL,
                    criado_em TEXT NOT NULL
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_mem_lp_user ON memoria_longo_prazo(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_inter_lp_user ON interacoes_longo_prazo(user_id)")
            c.commit()

    def guardar(self, user_id, categoria, chave, conteudo, importancia=0.7, permanencia=0.8):
        agora = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            c.execute("""
                INSERT INTO memoria_longo_prazo
                (user_id,categoria,chave,conteudo,importancia,permanencia,criado_em,atualizado_em)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(user_id,categoria,chave) DO UPDATE SET
                    conteudo=excluded.conteudo,
                    importancia=excluded.importancia,
                    permanencia=excluded.permanencia,
                    atualizado_em=excluded.atualizado_em
            """, (user_id,categoria,chave,conteudo,importancia,permanencia,agora,agora))
            c.commit()
        return {"sucesso": True, "user_id": user_id, "categoria": categoria, "chave": chave}

    def registrar_evento(self, user_id, categoria, chave, conteudo):
        return self.guardar(user_id, categoria, chave, conteudo, 0.55, 0.45)

    def registrar_interacao(self, user_id, entrada, resposta):
        agora = datetime.now(timezone.utc).isoformat()
        with self._conn() as c:
            c.execute("""
                INSERT INTO interacoes_longo_prazo(user_id,entrada,resposta,criado_em)
                VALUES(?,?,?,?)
            """, (user_id, entrada[:12000], resposta[:24000], agora))
            # retenção operacional: mantém as 5000 interações mais recentes por usuário
            c.execute("""
                DELETE FROM interacoes_longo_prazo
                WHERE user_id=? AND id NOT IN (
                    SELECT id FROM interacoes_longo_prazo
                    WHERE user_id=? ORDER BY id DESC LIMIT 5000
                )
            """, (user_id, user_id))
            c.commit()

    def buscar(self, user_id, consulta="", limite=20):
        termos = [t.lower() for t in consulta.split() if len(t) >= 3][:8]
        with self._conn() as c:
            rows = c.execute("""
                SELECT * FROM memoria_longo_prazo
                WHERE user_id=?
                ORDER BY importancia DESC, permanencia DESC, atualizado_em DESC
                LIMIT 200
            """, (user_id,)).fetchall()
        itens = [dict(r) for r in rows]
        if termos:
            itens.sort(
                key=lambda x: (
                    sum(t in (x["chave"]+" "+x["conteudo"]).lower() for t in termos),
                    x["importancia"],
                    x["permanencia"]
                ),
                reverse=True
            )
        return itens[:limite]

    def contexto(self, user_id, consulta, limite=8):
        itens = self.buscar(user_id, consulta, limite)
        if not itens:
            return "Nenhuma memória persistente relevante encontrada."
        return "\n".join(
            f'- [{x["categoria"]}/{x["chave"]}] {x["conteudo"]}'
            for x in itens
        )

    def estatisticas(self, user_id):
        with self._conn() as c:
            mem = c.execute("SELECT COUNT(*) FROM memoria_longo_prazo WHERE user_id=?", (user_id,)).fetchone()[0]
            hist = c.execute("SELECT COUNT(*) FROM interacoes_longo_prazo WHERE user_id=?", (user_id,)).fetchone()[0]
        return {"memorias": mem, "interacoes": hist}
