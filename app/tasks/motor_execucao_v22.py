"""V22 — Motor de Execução Persistente e Agendada da Ashley 1.0.

Responsabilidade: persistir, agendar, reservar, concluir, falhar, cancelar e
retomar tarefas. O V22 NÃO substitui o Orquestrador: ele entrega a execução ao
cérebro central através de um executor fornecido pela API/serviço.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


ESTADOS_FINAIS = {"CONCLUIDA", "FALHOU", "CANCELADA"}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalizar_data(valor: Optional[str]) -> Optional[str]:
    if not valor:
        return None
    dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


class MotorExecucaoV22:
    """Fila SQLite durável para trabalho autônomo governado pelo Orquestrador."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()
        self.recuperar_interrompidas()

    def _conectar(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar(self):
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tarefas_v22 (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    titulo TEXT NOT NULL,
                    objetivo TEXT NOT NULL,
                    contexto TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDENTE',
                    prioridade INTEGER NOT NULL DEFAULT 3,
                    agendada_para TEXT,
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    iniciado_em TEXT,
                    concluido_em TEXT,
                    tentativas INTEGER NOT NULL DEFAULT 0,
                    max_tentativas INTEGER NOT NULL DEFAULT 3,
                    progresso INTEGER NOT NULL DEFAULT 0,
                    etapa_atual TEXT,
                    resultado TEXT,
                    erro TEXT,
                    requer_aprovacao INTEGER NOT NULL DEFAULT 0,
                    aprovado INTEGER NOT NULL DEFAULT 0,
                    metadados TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_v22_fila ON tarefas_v22(status, agendada_para, prioridade, criado_em)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_v22_usuario ON tarefas_v22(user_id, criado_em)")

    def recuperar_interrompidas(self) -> int:
        """Após reinício, devolve execuções interrompidas para a fila."""
        with self._conectar() as conn:
            cur = conn.execute("""
                UPDATE tarefas_v22
                   SET status='PENDENTE', etapa_atual='Retomada após reinício', atualizado_em=?
                 WHERE status='EXECUTANDO'
            """, (_agora(),))
            return cur.rowcount

    def criar(self, *, user_id: int, titulo: str, objetivo: str, contexto: str = "",
              prioridade: int = 3, agendada_para: Optional[str] = None,
              max_tentativas: int = 3, requer_aprovacao: bool = False,
              metadados: Optional[dict[str, Any]] = None) -> dict:
        tid = str(uuid.uuid4())
        agora = _agora()
        agendada = _normalizar_data(agendada_para)
        status = "AGUARDANDO_APROVACAO" if requer_aprovacao else ("AGENDADA" if agendada else "PENDENTE")
        with self._conectar() as conn:
            conn.execute("""
                INSERT INTO tarefas_v22
                (id,user_id,titulo,objetivo,contexto,status,prioridade,agendada_para,criado_em,atualizado_em,max_tentativas,requer_aprovacao,metadados)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (tid, user_id, titulo.strip(), objetivo.strip(), contexto.strip(), status,
                  max(1, min(5, int(prioridade))), agendada, agora, agora,
                  max(1, min(10, int(max_tentativas))), int(requer_aprovacao), json.dumps(metadados or {}, ensure_ascii=False)))
        return self.obter(tid, user_id)

    def obter(self, tarefa_id: str, user_id: Optional[int] = None) -> Optional[dict]:
        sql, args = "SELECT * FROM tarefas_v22 WHERE id=?", [tarefa_id]
        if user_id is not None:
            sql += " AND user_id=?"; args.append(user_id)
        with self._conectar() as conn:
            row = conn.execute(sql, args).fetchone()
        return self._row(row) if row else None

    def listar(self, user_id: int, limite: int = 50) -> list[dict]:
        with self._conectar() as conn:
            rows = conn.execute("SELECT * FROM tarefas_v22 WHERE user_id=? ORDER BY criado_em DESC LIMIT ?", (user_id, limite)).fetchall()
        return [self._row(r) for r in rows]

    def aprovar(self, tarefa_id: str, user_id: int) -> Optional[dict]:
        t = self.obter(tarefa_id, user_id)
        if not t or t["status"] in ESTADOS_FINAIS:
            return t
        novo = "AGENDADA" if t.get("agendada_para") else "PENDENTE"
        with self._conectar() as conn:
            conn.execute("UPDATE tarefas_v22 SET aprovado=1,status=?,atualizado_em=? WHERE id=? AND user_id=?", (novo, _agora(), tarefa_id, user_id))
        return self.obter(tarefa_id, user_id)

    def cancelar(self, tarefa_id: str, user_id: int) -> Optional[dict]:
        with self._conectar() as conn:
            conn.execute("UPDATE tarefas_v22 SET status='CANCELADA',atualizado_em=?,concluido_em=? WHERE id=? AND user_id=? AND status NOT IN ('CONCLUIDA','FALHOU','CANCELADA')", (_agora(), _agora(), tarefa_id, user_id))
        return self.obter(tarefa_id, user_id)

    def proxima(self) -> Optional[dict]:
        agora = _agora()
        with self._conectar() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("""
                SELECT * FROM tarefas_v22
                 WHERE status IN ('PENDENTE','AGENDADA')
                   AND (agendada_para IS NULL OR agendada_para<=?)
                   AND (requer_aprovacao=0 OR aprovado=1)
                   AND tentativas < max_tentativas
                 ORDER BY prioridade DESC, COALESCE(agendada_para, criado_em), criado_em
                 LIMIT 1
            """, (agora,)).fetchone()
            if not row:
                conn.commit(); return None
            conn.execute("""
                UPDATE tarefas_v22 SET status='EXECUTANDO', iniciado_em=COALESCE(iniciado_em,?),
                    atualizado_em=?, tentativas=tentativas+1, progresso=5, etapa_atual='Entregue ao Orquestrador'
                 WHERE id=?
            """, (agora, agora, row["id"]))
            conn.commit()
        return self.obter(row["id"])

    def progresso(self, tarefa_id: str, percentual: int, etapa: str):
        with self._conectar() as conn:
            conn.execute("UPDATE tarefas_v22 SET progresso=?,etapa_atual=?,atualizado_em=? WHERE id=? AND status='EXECUTANDO'", (max(0,min(99,int(percentual))), etapa, _agora(), tarefa_id))

    def concluir(self, tarefa_id: str, resultado: Any):
        texto = resultado if isinstance(resultado, str) else json.dumps(resultado, ensure_ascii=False, indent=2, default=str)
        with self._conectar() as conn:
            conn.execute("UPDATE tarefas_v22 SET status='CONCLUIDA',progresso=100,etapa_atual='Concluída',resultado=?,erro=NULL,atualizado_em=?,concluido_em=? WHERE id=?", (texto, _agora(), _agora(), tarefa_id))

    def falhar(self, tarefa_id: str, erro: str):
        t = self.obter(tarefa_id)
        if not t: return
        final = int(t["tentativas"]) >= int(t["max_tentativas"])
        status = "FALHOU" if final else "PENDENTE"
        etapa = "Falha definitiva" if final else "Nova tentativa pendente"
        with self._conectar() as conn:
            conn.execute("UPDATE tarefas_v22 SET status=?,etapa_atual=?,erro=?,atualizado_em=?,concluido_em=? WHERE id=?", (status, etapa, str(erro)[:8000], _agora(), _agora() if final else None, tarefa_id))

    @staticmethod
    def _row(row: sqlite3.Row) -> dict:
        d = dict(row)
        try: d["metadados"] = json.loads(d.get("metadados") or "{}")
        except Exception: d["metadados"] = {}
        d["requer_aprovacao"] = bool(d.get("requer_aprovacao"))
        d["aprovado"] = bool(d.get("aprovado"))
        return d
