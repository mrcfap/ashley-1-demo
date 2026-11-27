"""V22 — Motor de Execução Persistente e Agendada da Ashley 1.0.

Responsabilidade: persistir, agendar, reservar, concluir, falhar, cancelar e
retomar tarefas. O V22 NÃO substitui o Orquestrador: ele entrega a execução ao
cérebro central através de um executor fornecido pela API/serviço.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
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

    def __init__(self, db_path: str | Path, *, recuperar_ao_iniciar: bool = False):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()
        # Recuperação é explícita: construir uma instância por requisição não
        # pode reabrir tarefas que outro executor ainda está processando.
        if recuperar_ao_iniciar:
            self.recuperar_interrompidas()

    @contextmanager
    def _conectar(self):
        """Transação SQLite que sempre libera o arquivo, inclusive em erros."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            conn.row_factory = sqlite3.Row
            with conn:
                yield conn
        finally:
            conn.close()

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
        """Recupera execuções interrompidas sem exceder o limite de tentativas.

        Deve ser chamado uma vez no bootstrap controlado do worker, não a cada
        construção de uma instância do motor.
        """
        agora = _agora()
        with self._conectar() as conn:
            cur = conn.execute("""
                UPDATE tarefas_v22
                   SET status = CASE
                       WHEN tentativas >= max_tentativas THEN 'FALHOU'
                       ELSE 'PENDENTE'
                   END,
                   etapa_atual = CASE
                       WHEN tentativas >= max_tentativas
                           THEN 'Falha definitiva após reinício'
                       ELSE 'Retomada após reinício'
                   END,
                   erro = CASE
                       WHEN tentativas >= max_tentativas
                           THEN 'Limite de tentativas atingido durante interrupção.'
                       ELSE erro
                   END,
                   concluido_em = CASE
                       WHEN tentativas >= max_tentativas THEN ?
                       ELSE concluido_em
                   END,
                   atualizado_em = ?
                 WHERE status = 'EXECUTANDO'
            """, (agora, agora))
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

    def transferir_passagem(self, tarefa_id: str, titular: int, destinatario: int, *, aceitar: bool) -> bool:
        if titular == destinatario:
            return False
        with self._conectar() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT status, metadados FROM tarefas_v22 WHERE id=? AND user_id=?",
                (tarefa_id, titular),
            ).fetchone()
            if not row or row["status"] != "AGUARDANDO_APROVACAO":
                return False
            dados = json.loads(row["metadados"] or "{}")
            if dados.get("tipo") != "passagem_turno":
                return False
            if aceitar:
                if dados.get("transferencia_pendente") != destinatario:
                    return False
                dados.pop("transferencia_pendente")
                dados.setdefault("transferencias", []).append(
                    {"origem": titular, "destino": destinatario, "aceita_em": _agora()}
                )
                dados["responsavel"] = f"Conta {destinatario}"
            else:
                dados["transferencia_pendente"] = destinatario
            conn.execute(
                "UPDATE tarefas_v22 SET user_id=?, metadados=?, atualizado_em=? WHERE id=?",
                (destinatario if aceitar else titular, json.dumps(dados, ensure_ascii=False), _agora(), tarefa_id),
            )
            return True

    def aprovar(self, tarefa_id: str, user_id: int) -> Optional[dict]:
        """Aprova somente uma tarefa que aguarda aprovação explicitamente."""
        agora = _agora()
        with self._conectar() as conn:
            cur = conn.execute("""
                UPDATE tarefas_v22
                   SET aprovado = 1,
                       status = CASE
                           WHEN agendada_para IS NOT NULL THEN 'AGENDADA'
                           ELSE 'PENDENTE'
                       END,
                       atualizado_em = ?
                 WHERE id = ?
                   AND user_id = ?
                   AND status = 'AGUARDANDO_APROVACAO'
            """, (agora, tarefa_id, user_id))
            if cur.rowcount != 1:
                raise ValueError("Tarefa não está aguardando aprovação.")
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
        """Conclui apenas tarefas que ainda pertencem a uma execução ativa."""
        texto = resultado if isinstance(resultado, str) else json.dumps(
            resultado, ensure_ascii=False, indent=2, default=str
        )
        agora = _agora()
        with self._conectar() as conn:
            cur = conn.execute("""
                UPDATE tarefas_v22
                   SET status='CONCLUIDA', progresso=100,
                       etapa_atual='Concluída', resultado=?, erro=NULL,
                       atualizado_em=?, concluido_em=?
                 WHERE id=? AND status='EXECUTANDO'
            """, (texto, agora, agora, tarefa_id))
            if cur.rowcount != 1:
                raise ValueError(
                    "Conclusão recusada: tarefa inexistente ou não está em execução."
                )

    def falhar(self, tarefa_id: str, erro: str) -> bool:
        """Registra falha somente se a tarefa ainda estiver em execução."""
        agora = _agora()
        with self._conectar() as conn:
            cur = conn.execute("""
                UPDATE tarefas_v22
                   SET status = CASE
                       WHEN tentativas >= max_tentativas THEN 'FALHOU'
                       ELSE 'PENDENTE'
                   END,
                   etapa_atual = CASE
                       WHEN tentativas >= max_tentativas
                           THEN 'Falha definitiva'
                       ELSE 'Nova tentativa pendente'
                   END,
                   erro = ?,
                   atualizado_em = ?,
                   concluido_em = CASE
                       WHEN tentativas >= max_tentativas THEN ?
                       ELSE NULL
                   END
                 WHERE id = ? AND status = 'EXECUTANDO'
            """, (str(erro)[:8000], agora, agora, tarefa_id))
            return cur.rowcount == 1

    @staticmethod
    def _row(row: sqlite3.Row) -> dict:
        d = dict(row)
        try: d["metadados"] = json.loads(d.get("metadados") or "{}")
        except Exception: d["metadados"] = {}
        d["requer_aprovacao"] = bool(d.get("requer_aprovacao"))
        d["aprovado"] = bool(d.get("aprovado"))
        return d
