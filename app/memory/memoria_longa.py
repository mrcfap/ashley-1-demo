import sqlite3
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager


class MemoriaLongoPrazo:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        # A conexão remota não deve bloquear a importação da API.
        # PostgreSQL será inicializado sob demanda, com erro explícito em caso de falha.
        self._postgres_inicializado = False
        if not os.getenv("DATABASE_URL"):
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._init()

    def _conn(self):
        if os.getenv('DATABASE_URL'):
            from app.memory.postgres_memory import connect, init
            if not self._postgres_inicializado:
                init()
                self._postgres_inicializado = True
            return connect()
        return self._sqlite_conn()

    @contextmanager
    def _sqlite_conn(self):
        # sqlite3.Connection.__exit__ confirma/reverte a transação, mas NÃO fecha
        # o arquivo no Windows. O fechamento explícito evita WinError 32.
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init(self):
        if os.getenv('DATABASE_URL'):
            from app.memory.postgres_memory import init
            init()
            return
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

    @staticmethod
    def _normalizar(texto):
        texto = unicodedata.normalize("NFKD", str(texto or "").casefold())
        return "".join(c for c in texto if not unicodedata.combining(c))

    def buscar(self, user_id, consulta="", limite=20):
        """Busca determinística com relevância antes do corte; sem limite inicial 200.

        Nunca retorna dados de outro usuário. Consultas sem correspondência
        retornam [] em vez de memórias aleatórias.
        """
        limite = max(1, min(int(limite), 50))
        aliases = {
            "cachorro": ("cachorro", "cao", "pet", "animal de estimacao"),
            "cao": ("cachorro", "cao", "pet", "animal de estimacao"),
            "pet": ("cachorro", "cao", "pet", "animal de estimacao"),
            "animal": ("cachorro", "cao", "pet", "animal de estimacao"),
            "autor": ("autor", "escritor", "pseudonimo", "nome artistico"),
            "livro": ("livro", "obra", "bibliografia", "publicacao"),
            "livros": ("livro", "obra", "bibliografia", "publicacao"),
        }
        ignorar = {"qual", "quais", "quando", "onde", "como", "meu", "minha",
                   "seu", "sua", "nome", "voce", "sobre", "para", "isso",
                   "diga", "fale", "informacao", "primeira", "vez", "foi",
                   "que", "dos", "das", "com", "uma", "tem", "ele", "ela"}
        tokens = [t for t in re.findall(r"[a-z0-9]+", self._normalizar(consulta))
                  if len(t) >= 3 and t not in ignorar]
        termos = set(tokens)
        for t in tokens:
            termos.update(aliases.get(t, ()))
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM memoria_longo_prazo WHERE user_id=?",
                (user_id,)
            ).fetchall()
        itens = [dict(r) for r in rows]
        if not termos:
            itens.sort(key=lambda x: (float(x["importancia"]),
                                     float(x["permanencia"]),
                                     str(x["atualizado_em"])), reverse=True)
            return itens[:limite]
        pontuados = []
        for item in itens:
            chave = self._normalizar(item["chave"])
            categoria = self._normalizar(item["categoria"])
            conteudo = self._normalizar(item["conteudo"])
            pontos = sum(5 if t in chave else 3 if t in categoria
                         else 1 if t in conteudo else 0 for t in termos)
            if pontos:
                pontuados.append((pontos, item))
        pontuados.sort(key=lambda p: (p[0], float(p[1]["importancia"]),
                                      float(p[1]["permanencia"]),
                                      str(p[1]["atualizado_em"])), reverse=True)
        return [item for _, item in pontuados[:limite]]

    def contexto(self, user_id, consulta, limite=8):
        itens = self.buscar(user_id, consulta, limite)
        if not itens:
            return "Nenhuma memória persistente relevante encontrada."
        return "\n".join(
            f'- [{x["categoria"]}/{x["chave"]}] {x["conteudo"]}'
            for x in itens
        )

    def contexto_recente(self, user_id, limite=4):
        """Recupera as últimas interações do usuário, em ordem cronológica."""
        limite = max(1, min(int(limite), 20))
        with self._conn() as c:
            rows = c.execute("""
                SELECT entrada, resposta FROM interacoes_longo_prazo
                WHERE user_id=? ORDER BY id DESC LIMIT ?
            """, (user_id, limite)).fetchall()
        if not rows:
            return ""
        conversas = []
        for row in reversed(rows):
            if hasattr(row, "keys"):
                entrada = row["entrada"]
                resposta = row["resposta"]
            else:
                entrada, resposta = row[0], row[1]
            conversas.append(
                f"Usuário: {str(entrada or '')[:1500]}\n"
                f"Ashley: {str(resposta or '')[:2500]}"
            )
        return "\n\n".join(conversas)

    def estatisticas(self, user_id):
        with self._conn() as c:
            mem = c.execute("SELECT COUNT(*) FROM memoria_longo_prazo WHERE user_id=?", (user_id,)).fetchone()[0]
            hist = c.execute("SELECT COUNT(*) FROM interacoes_longo_prazo WHERE user_id=?", (user_id,)).fetchone()[0]
        return {"memorias": mem, "interacoes": hist}
