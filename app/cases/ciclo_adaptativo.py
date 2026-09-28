import sqlite3
from datetime import datetime, timezone


class CicloAdaptativoResolucao:
    """
    V5: fecha o ciclo ação -> resultado -> avaliação -> adaptação.

    A avaliação é explícita e auditável. O motor não inventa sucesso:
    recebe sinais/medidas observadas e decide a transição do caso.
    """

    RESULTADOS = {"SUCESSO", "PARCIAL", "FALHA", "INCONCLUSIVO"}

    def __init__(self, db_path="data/ashley_memoria.db"):
        self.db_path = str(db_path)
        self._inicializar()

    def _agora(self):
        return datetime.now(timezone.utc).isoformat()

    def _conectar(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar(self):
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS caso_avaliacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    acao_id INTEGER,
                    classificacao TEXT NOT NULL,
                    resultado_observado TEXT NOT NULL,
                    criterio_atendido INTEGER NOT NULL DEFAULT 0,
                    justificativa TEXT NOT NULL DEFAULT '',
                    criado_em TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS caso_adaptacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    criado_em TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_avaliacao_caso "
                "ON caso_avaliacoes(caso_id, user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_adaptacao_caso "
                "ON caso_adaptacoes(caso_id, user_id)"
            )
            conn.commit()

    def registrar_avaliacao(
        self,
        caso_id,
        user_id,
        classificacao,
        resultado_observado,
        criterio_atendido=False,
        justificativa="",
        acao_id=None
    ):
        classificacao = str(classificacao).upper().strip()
        if classificacao not in self.RESULTADOS:
            raise ValueError(
                "classificacao deve ser SUCESSO, PARCIAL, FALHA ou INCONCLUSIVO."
            )

        with self._conectar() as conn:
            cur = conn.execute("""
                INSERT INTO caso_avaliacoes
                (caso_id, user_id, acao_id, classificacao,
                 resultado_observado, criterio_atendido, justificativa, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(caso_id), int(user_id),
                int(acao_id) if acao_id is not None else None,
                classificacao, resultado_observado,
                1 if criterio_atendido else 0,
                justificativa, self._agora()
            ))
            conn.commit()
            return cur.lastrowid

    def ajustar_confianca_hipoteses(self, caso_id, user_id, delta):
        delta = float(delta)
        alteradas = []
        with self._conectar() as conn:
            linhas = conn.execute("""
                SELECT id, confianca
                FROM caso_hipoteses
                WHERE caso_id=? AND user_id=? AND status='ABERTA'
            """, (int(caso_id), int(user_id))).fetchall()

            for linha in linhas:
                nova = max(0.0, min(1.0, float(linha["confianca"]) + delta))
                conn.execute(
                    "UPDATE caso_hipoteses SET confianca=? WHERE id=? AND user_id=?",
                    (nova, int(linha["id"]), int(user_id))
                )
                alteradas.append({
                    "hipotese_id": int(linha["id"]),
                    "confianca_anterior": float(linha["confianca"]),
                    "confianca_nova": nova
                })
            conn.commit()
        return alteradas

    def registrar_adaptacao(self, caso_id, user_id, tipo, descricao):
        with self._conectar() as conn:
            cur = conn.execute("""
                INSERT INTO caso_adaptacoes
                (caso_id, user_id, tipo, descricao, criado_em)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int(caso_id), int(user_id), tipo, descricao, self._agora()
            ))
            conn.commit()
            return cur.lastrowid

    def historico(self, caso_id, user_id, limite=10):
        with self._conectar() as conn:
            avaliacoes = conn.execute("""
                SELECT id, acao_id, classificacao, resultado_observado,
                       criterio_atendido, justificativa, criado_em
                FROM caso_avaliacoes
                WHERE caso_id=? AND user_id=?
                ORDER BY id DESC LIMIT ?
            """, (int(caso_id), int(user_id), int(limite))).fetchall()

            adaptacoes = conn.execute("""
                SELECT id, tipo, descricao, criado_em
                FROM caso_adaptacoes
                WHERE caso_id=? AND user_id=?
                ORDER BY id DESC LIMIT ?
            """, (int(caso_id), int(user_id), int(limite))).fetchall()

        return {
            "avaliacoes": [dict(x) for x in avaliacoes],
            "adaptacoes": [dict(x) for x in adaptacoes]
        }
