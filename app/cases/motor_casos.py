import json
import sqlite3
from datetime import datetime, timezone


class MotorCasos:
    """
    Gerencia casos persistentes da Ashley 1.0.

    Um caso representa um problema/objetivo que precisa de continuidade:
    diagnóstico -> plano -> execução -> acompanhamento -> reavaliação -> resolução.
    """

    STATUS_VALIDOS = {
        "ABERTO",
        "DIAGNOSTICO",
        "PLANO",
        "EM_EXECUCAO",
        "AGUARDANDO_RESULTADO",
        "REAVALIACAO",
        "RESOLVIDO",
        "ARQUIVADO",
    }

    def __init__(self, db_path="data/ashley_memoria.db"):
        self.db_path = str(db_path)
        self._inicializar()

    @staticmethod
    def _agora():
        return datetime.now(timezone.utc).isoformat()

    def _conectar(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar(self):
        with self._conectar() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS casos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    objetivo TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'ABERTO',
                    prioridade INTEGER NOT NULL DEFAULT 3,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    encerrado_em TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_casos_usuario_status
                ON casos(user_id, status, atualizado_em);

                CREATE TABLE IF NOT EXISTS caso_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    dados_json TEXT DEFAULT '{}',
                    criado_em TEXT NOT NULL,
                    FOREIGN KEY(caso_id) REFERENCES casos(id)
                );

                CREATE INDEX IF NOT EXISTS idx_eventos_caso
                ON caso_eventos(caso_id, criado_em);

                CREATE TABLE IF NOT EXISTS caso_acoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    descricao TEXT NOT NULL,
                    responsavel TEXT DEFAULT 'usuario',
                    status TEXT NOT NULL DEFAULT 'PENDENTE',
                    prazo TEXT,
                    resultado TEXT DEFAULT '',
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    FOREIGN KEY(caso_id) REFERENCES casos(id)
                );

                CREATE INDEX IF NOT EXISTS idx_acoes_caso_status
                ON caso_acoes(caso_id, status);
            """)
            conn.commit()

    def criar_caso(self, user_id, titulo, descricao, objetivo="", prioridade=3):
        user_id = int(user_id)
        if user_id <= 0:
            raise ValueError("user_id deve ser maior que zero.")

        agora = self._agora()
        prioridade = max(1, min(5, int(prioridade)))

        with self._conectar() as conn:
            cur = conn.execute(
                """
                INSERT INTO casos
                (user_id, titulo, descricao, objetivo, status, prioridade, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, 'ABERTO', ?, ?, ?)
                """,
                (user_id, titulo.strip(), descricao.strip(), objetivo.strip(), prioridade, agora, agora),
            )
            caso_id = cur.lastrowid
            conn.execute(
                """
                INSERT INTO caso_eventos
                (caso_id, user_id, tipo, conteudo, dados_json, criado_em)
                VALUES (?, ?, 'CASO_CRIADO', ?, '{}', ?)
                """,
                (caso_id, user_id, descricao.strip(), agora),
            )
            conn.commit()

        return self.obter_caso(caso_id, user_id)

    def obter_caso(self, caso_id, user_id):
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT * FROM casos WHERE id=? AND user_id=?",
                (int(caso_id), int(user_id)),
            ).fetchone()
        return dict(row) if row else None

    def listar_casos(self, user_id, incluir_resolvidos=False, limite=10):
        sql = "SELECT * FROM casos WHERE user_id=?"
        params = [int(user_id)]

        if not incluir_resolvidos:
            sql += " AND status NOT IN ('RESOLVIDO','ARQUIVADO')"

        sql += " ORDER BY atualizado_em DESC LIMIT ?"
        params.append(int(limite))

        with self._conectar() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(x) for x in rows]

    def caso_ativo(self, user_id):
        casos = self.listar_casos(user_id, incluir_resolvidos=False, limite=1)
        return casos[0] if casos else None

    def atualizar_status(self, caso_id, user_id, status, observacao=""):
        status = str(status).upper().strip()
        if status not in self.STATUS_VALIDOS:
            raise ValueError(f"Status inválido: {status}")

        agora = self._agora()
        encerrado = agora if status in {"RESOLVIDO", "ARQUIVADO"} else None

        with self._conectar() as conn:
            conn.execute(
                """
                UPDATE casos
                SET status=?, atualizado_em=?, encerrado_em=?
                WHERE id=? AND user_id=?
                """,
                (status, agora, encerrado, int(caso_id), int(user_id)),
            )
            conn.execute(
                """
                INSERT INTO caso_eventos
                (caso_id, user_id, tipo, conteudo, dados_json, criado_em)
                VALUES (?, ?, 'STATUS', ?, ?, ?)
                """,
                (
                    int(caso_id),
                    int(user_id),
                    observacao or f"Status alterado para {status}.",
                    json.dumps({"status": status}, ensure_ascii=False),
                    agora,
                ),
            )
            conn.commit()

        return self.obter_caso(caso_id, user_id)

    def registrar_evento(self, caso_id, user_id, tipo, conteudo, dados=None):
        agora = self._agora()
        with self._conectar() as conn:
            conn.execute(
                """
                INSERT INTO caso_eventos
                (caso_id, user_id, tipo, conteudo, dados_json, criado_em)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(caso_id),
                    int(user_id),
                    str(tipo).upper().strip(),
                    str(conteudo).strip(),
                    json.dumps(dados or {}, ensure_ascii=False),
                    agora,
                ),
            )
            conn.execute(
                "UPDATE casos SET atualizado_em=? WHERE id=? AND user_id=?",
                (agora, int(caso_id), int(user_id)),
            )
            conn.commit()

    def adicionar_acao(self, caso_id, user_id, descricao, responsavel="usuario", prazo=None):
        agora = self._agora()
        with self._conectar() as conn:
            cur = conn.execute(
                """
                INSERT INTO caso_acoes
                (caso_id, user_id, descricao, responsavel, status, prazo, resultado, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, 'PENDENTE', ?, '', ?, ?)
                """,
                (
                    int(caso_id),
                    int(user_id),
                    descricao.strip(),
                    responsavel.strip(),
                    prazo,
                    agora,
                    agora,
                ),
            )
            conn.execute(
                "UPDATE casos SET atualizado_em=? WHERE id=? AND user_id=?",
                (agora, int(caso_id), int(user_id)),
            )
            conn.commit()
            return cur.lastrowid

    def concluir_acao(self, acao_id, user_id, resultado=""):
        agora = self._agora()
        with self._conectar() as conn:
            conn.execute(
                """
                UPDATE caso_acoes
                SET status='CONCLUIDA', resultado=?, atualizado_em=?
                WHERE id=? AND user_id=?
                """,
                (resultado, agora, int(acao_id), int(user_id)),
            )
            conn.commit()

    def contexto_usuario(self, user_id, limite_casos=5):
        if user_id is None:
            return "Nenhum usuário identificado; casos não foram consultados."

        casos = self.listar_casos(user_id, incluir_resolvidos=False, limite=limite_casos)
        if not casos:
            return "Nenhum caso ativo registrado para este usuário."

        blocos = []
        with self._conectar() as conn:
            for caso in casos:
                eventos = conn.execute(
                    """
                    SELECT tipo, conteudo, criado_em
                    FROM caso_eventos
                    WHERE caso_id=? AND user_id=?
                    ORDER BY id DESC LIMIT 5
                    """,
                    (caso["id"], int(user_id)),
                ).fetchall()

                acoes = conn.execute(
                    """
                    SELECT id, descricao, responsavel, status, prazo, resultado
                    FROM caso_acoes
                    WHERE caso_id=? AND user_id=?
                    ORDER BY id DESC LIMIT 8
                    """,
                    (caso["id"], int(user_id)),
                ).fetchall()

                bloco = {
                    "id": caso["id"],
                    "titulo": caso["titulo"],
                    "descricao": caso["descricao"],
                    "objetivo": caso["objetivo"],
                    "status": caso["status"],
                    "prioridade": caso["prioridade"],
                    "acoes": [dict(x) for x in acoes],
                    "eventos_recentes": [dict(x) for x in eventos],
                }
                blocos.append(bloco)

        return json.dumps(blocos, ensure_ascii=False, indent=2)
