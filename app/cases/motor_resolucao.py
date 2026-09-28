import json
import sqlite3
from datetime import datetime, timezone


class MotorResolucao:
    """
    Camada V4 para estruturar a resolução de um caso:
    diagnóstico -> hipóteses -> plano -> ações -> resultados -> reavaliação.
    """

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
                CREATE TABLE IF NOT EXISTS caso_diagnosticos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    resumo TEXT NOT NULL,
                    fatos_json TEXT NOT NULL DEFAULT '[]',
                    informacoes_faltantes_json TEXT NOT NULL DEFAULT '[]',
                    criado_em TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS caso_hipoteses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    hipotese TEXT NOT NULL,
                    evidencia TEXT NOT NULL DEFAULT '',
                    confianca REAL NOT NULL DEFAULT 0.5,
                    status TEXT NOT NULL DEFAULT 'ABERTA',
                    criado_em TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS caso_planos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    objetivo TEXT NOT NULL,
                    estrategia TEXT NOT NULL,
                    criterio_sucesso TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'ATIVO',
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS caso_proximas_acoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    descricao TEXT NOT NULL,
                    responsavel TEXT NOT NULL DEFAULT 'usuario',
                    prazo TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDENTE',
                    resultado TEXT NOT NULL DEFAULT '',
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_diag_caso ON caso_diagnosticos(caso_id, user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hip_caso ON caso_hipoteses(caso_id, user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_plano_caso ON caso_planos(caso_id, user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prox_caso ON caso_proximas_acoes(caso_id, user_id)"
            )
            conn.commit()

    def registrar_diagnostico(self, caso_id, user_id, resumo, fatos=None, informacoes_faltantes=None):
        agora = self._agora()
        with self._conectar() as conn:
            cur = conn.execute("""
                INSERT INTO caso_diagnosticos
                (caso_id, user_id, resumo, fatos_json, informacoes_faltantes_json, criado_em)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                int(caso_id), int(user_id), resumo,
                json.dumps(fatos or [], ensure_ascii=False),
                json.dumps(informacoes_faltantes or [], ensure_ascii=False),
                agora
            ))
            conn.commit()
            return cur.lastrowid

    def adicionar_hipotese(self, caso_id, user_id, hipotese, evidencia="", confianca=0.5):
        confianca = max(0.0, min(1.0, float(confianca)))
        with self._conectar() as conn:
            cur = conn.execute("""
                INSERT INTO caso_hipoteses
                (caso_id, user_id, hipotese, evidencia, confianca, status, criado_em)
                VALUES (?, ?, ?, ?, ?, 'ABERTA', ?)
            """, (int(caso_id), int(user_id), hipotese, evidencia, confianca, self._agora()))
            conn.commit()
            return cur.lastrowid

    def criar_plano(self, caso_id, user_id, objetivo, estrategia, criterio_sucesso=""):
        agora = self._agora()
        with self._conectar() as conn:
            conn.execute("""
                UPDATE caso_planos
                SET status='SUBSTITUIDO', atualizado_em=?
                WHERE caso_id=? AND user_id=? AND status='ATIVO'
            """, (agora, int(caso_id), int(user_id)))
            cur = conn.execute("""
                INSERT INTO caso_planos
                (caso_id, user_id, objetivo, estrategia, criterio_sucesso, status, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, 'ATIVO', ?, ?)
            """, (
                int(caso_id), int(user_id), objetivo, estrategia,
                criterio_sucesso, agora, agora
            ))
            conn.commit()
            return cur.lastrowid

    def definir_proxima_acao(self, caso_id, user_id, descricao, responsavel="usuario", prazo=None):
        agora = self._agora()
        with self._conectar() as conn:
            # Apenas uma "próxima ação" principal pendente por caso.
            conn.execute("""
                UPDATE caso_proximas_acoes
                SET status='SUBSTITUIDA', atualizado_em=?
                WHERE caso_id=? AND user_id=? AND status='PENDENTE'
            """, (agora, int(caso_id), int(user_id)))
            cur = conn.execute("""
                INSERT INTO caso_proximas_acoes
                (caso_id, user_id, descricao, responsavel, prazo, status, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, 'PENDENTE', ?, ?)
            """, (
                int(caso_id), int(user_id), descricao, responsavel,
                prazo, agora, agora
            ))
            conn.commit()
            return cur.lastrowid

    def concluir_proxima_acao(self, acao_id, user_id, resultado=""):
        agora = self._agora()
        with self._conectar() as conn:
            cur = conn.execute("""
                UPDATE caso_proximas_acoes
                SET status='CONCLUIDA', resultado=?, atualizado_em=?
                WHERE id=? AND user_id=? AND status='PENDENTE'
            """, (resultado, agora, int(acao_id), int(user_id)))
            conn.commit()
            return cur.rowcount > 0

    def contexto_caso(self, caso_id, user_id):
        with self._conectar() as conn:
            diag = conn.execute("""
                SELECT * FROM caso_diagnosticos
                WHERE caso_id=? AND user_id=?
                ORDER BY id DESC LIMIT 1
            """, (int(caso_id), int(user_id))).fetchone()

            hip = conn.execute("""
                SELECT id, hipotese, evidencia, confianca, status, criado_em
                FROM caso_hipoteses
                WHERE caso_id=? AND user_id=?
                ORDER BY id DESC LIMIT 5
            """, (int(caso_id), int(user_id))).fetchall()

            plano = conn.execute("""
                SELECT id, objetivo, estrategia, criterio_sucesso, status, criado_em, atualizado_em
                FROM caso_planos
                WHERE caso_id=? AND user_id=? AND status='ATIVO'
                ORDER BY id DESC LIMIT 1
            """, (int(caso_id), int(user_id))).fetchone()

            prox = conn.execute("""
                SELECT id, descricao, responsavel, prazo, status, resultado, criado_em, atualizado_em
                FROM caso_proximas_acoes
                WHERE caso_id=? AND user_id=? AND status='PENDENTE'
                ORDER BY id DESC LIMIT 1
            """, (int(caso_id), int(user_id))).fetchone()

        diagnostico = None
        if diag:
            diagnostico = dict(diag)
            diagnostico["fatos"] = json.loads(diagnostico.pop("fatos_json") or "[]")
            diagnostico["informacoes_faltantes"] = json.loads(
                diagnostico.pop("informacoes_faltantes_json") or "[]"
            )

        return {
            "caso_id": int(caso_id),
            "diagnostico": diagnostico,
            "hipoteses": [dict(x) for x in hip],
            "plano_ativo": dict(plano) if plano else None,
            "proxima_acao": dict(prox) if prox else None
        }
