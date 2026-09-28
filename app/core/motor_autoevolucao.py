import json
import sqlite3
import uuid
from datetime import datetime, timezone


class MotorAutoEvolucao:
    """
    V8: metacognição operacional e evolução governada.

    O motor NÃO altera produção sozinho. Ele:
    1. observa falhas/sinais;
    2. cria uma proposta;
    3. classifica risco;
    4. define experimento e critérios;
    5. registra teste;
    6. recomenda promover, revisar ou rejeitar;
    7. exige aprovação para mudanças estruturais/relevantes.

    Isso permite autonomia útil com trilha de auditoria e rollback.
    """

    RISCOS = {"BAIXO", "MEDIO", "ALTO", "CRITICO"}
    ESTADOS = {
        "PROPOSTA", "EM_TESTE", "VALIDADA", "REJEITADA",
        "AGUARDANDO_APROVACAO", "APROVADA", "APLICADA", "REVERTIDA"
    }

    def __init__(self, db_path):
        self.db_path = str(db_path)
        self._inicializar()

    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def _agora(self):
        return datetime.now(timezone.utc).isoformat()

    def _inicializar(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS evolucao_observacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                categoria TEXT NOT NULL,
                descricao TEXT NOT NULL,
                severidade INTEGER NOT NULL DEFAULT 1,
                dados_json TEXT NOT NULL DEFAULT '{}',
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evolucao_propostas (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                titulo TEXT NOT NULL,
                problema TEXT NOT NULL,
                hipotese_melhoria TEXT NOT NULL,
                componente TEXT NOT NULL,
                risco TEXT NOT NULL,
                estado TEXT NOT NULL,
                reversivel INTEGER NOT NULL DEFAULT 1,
                requer_aprovacao INTEGER NOT NULL DEFAULT 1,
                plano_teste TEXT NOT NULL,
                criterio_sucesso TEXT NOT NULL,
                rollback TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evolucao_experimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposta_id TEXT NOT NULL,
                ambiente TEXT NOT NULL,
                resultado TEXT NOT NULL,
                metricas_json TEXT NOT NULL DEFAULT '{}',
                passou INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evolucao_aprendizados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposta_id TEXT,
                licao TEXT NOT NULL,
                criado_em TEXT NOT NULL
            );
            """)
            c.commit()

    def observar(self, user_id, categoria, descricao, severidade=1, dados=None):
        with self._conn() as c:
            cur = c.execute("""
                INSERT INTO evolucao_observacoes
                (user_id,categoria,descricao,severidade,dados_json,criado_em)
                VALUES (?,?,?,?,?,?)
            """, (
                user_id, categoria, descricao, int(severidade),
                json.dumps(dados or {}, ensure_ascii=False), self._agora()
            ))
            c.commit()
            return cur.lastrowid

    def propor(self, user_id, titulo, problema, hipotese_melhoria, componente,
               risco="MEDIO", plano_teste="", criterio_sucesso="", rollback=""):
        risco = str(risco).upper()
        if risco not in self.RISCOS:
            raise ValueError("Risco inválido")

        pid = "EV-" + uuid.uuid4().hex[:12].upper()
        requer = risco in {"MEDIO", "ALTO", "CRITICO"} or componente.lower() in {
            "seguranca", "permissoes", "memoria", "orquestrador", "api",
            "autenticacao", "banco", "ferramentas_externas"
        }
        estado = "AGUARDANDO_APROVACAO" if requer else "PROPOSTA"
        agora = self._agora()

        with self._conn() as c:
            c.execute("""
                INSERT INTO evolucao_propostas
                (id,user_id,titulo,problema,hipotese_melhoria,componente,risco,
                 estado,reversivel,requer_aprovacao,plano_teste,
                 criterio_sucesso,rollback,criado_em,atualizado_em)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                pid, user_id, titulo, problema, hipotese_melhoria, componente,
                risco, estado, 1, int(requer), plano_teste, criterio_sucesso,
                rollback, agora, agora
            ))
            c.commit()
        return self.obter_proposta(pid)

    def obter_proposta(self, proposta_id):
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM evolucao_propostas WHERE id=?",
                (proposta_id,)
            ).fetchone()
        return dict(row) if row else None

    def aprovar(self, proposta_id):
        p = self.obter_proposta(proposta_id)
        if not p:
            raise ValueError("Proposta inexistente")
        with self._conn() as c:
            c.execute("""
                UPDATE evolucao_propostas
                SET estado='APROVADA', atualizado_em=?
                WHERE id=?
            """, (self._agora(), proposta_id))
            c.commit()
        return self.obter_proposta(proposta_id)

    def registrar_experimento(self, proposta_id, resultado, metricas=None,
                              passou=False, ambiente="sandbox"):
        p = self.obter_proposta(proposta_id)
        if not p:
            raise ValueError("Proposta inexistente")
        if ambiente != "sandbox":
            raise ValueError("V8 permite experimento automático apenas em sandbox")

        with self._conn() as c:
            c.execute("""
                INSERT INTO evolucao_experimentos
                (proposta_id,ambiente,resultado,metricas_json,passou,criado_em)
                VALUES (?,?,?,?,?,?)
            """, (
                proposta_id, ambiente, resultado,
                json.dumps(metricas or {}, ensure_ascii=False),
                int(bool(passou)), self._agora()
            ))
            novo = "VALIDADA" if passou else "REJEITADA"
            # Uma validação técnica não equivale a autorização para produção.
            if passou and p["requer_aprovacao"]:
                novo = "AGUARDANDO_APROVACAO"
            c.execute("""
                UPDATE evolucao_propostas SET estado=?, atualizado_em=?
                WHERE id=?
            """, (novo, self._agora(), proposta_id))
            c.commit()
        return self.obter_proposta(proposta_id)

    def aprender(self, proposta_id, licao):
        with self._conn() as c:
            c.execute("""
                INSERT INTO evolucao_aprendizados(proposta_id,licao,criado_em)
                VALUES (?,?,?)
            """, (proposta_id, licao, self._agora()))
            c.commit()

    def painel(self, user_id=None, limite=20):
        where = ""
        args = []
        if user_id is not None:
            where = "WHERE user_id=?"
            args.append(user_id)
        args.append(int(limite))
        with self._conn() as c:
            props = [
                dict(r) for r in c.execute(
                    f"""SELECT * FROM evolucao_propostas {where}
                        ORDER BY criado_em DESC LIMIT ?""", args
                ).fetchall()
            ]
            obs = [
                dict(r) for r in c.execute(
                    f"""SELECT * FROM evolucao_observacoes {where}
                        ORDER BY criado_em DESC LIMIT ?""", args
                ).fetchall()
            ]
        return {"propostas": props, "observacoes": obs}

    def ciclo_reflexao(self, user_id, sinais):
        """
        Converte sinais operacionais em observações e, quando há recorrência
        suficiente, pode criar uma proposta de melhoria.

        'sinais' é uma lista de dicts:
        {categoria, descricao, severidade, componente, sugestao}
        """
        criadas = []
        for s in sinais or []:
            self.observar(
                user_id=user_id,
                categoria=s.get("categoria", "geral"),
                descricao=s.get("descricao", ""),
                severidade=s.get("severidade", 1),
                dados=s
            )
            if int(s.get("severidade", 1)) >= 3 and s.get("sugestao"):
                p = self.propor(
                    user_id=user_id,
                    titulo=s.get("titulo", "Melhoria proposta pela Ashley"),
                    problema=s.get("descricao", ""),
                    hipotese_melhoria=s["sugestao"],
                    componente=s.get("componente", "orquestrador"),
                    risco=s.get("risco", "MEDIO"),
                    plano_teste=s.get("plano_teste") or (
                        "Executar testes automatizados e comparar métricas em sandbox."
                    ),
                    criterio_sucesso=s.get("criterio_sucesso") or (
                        "Não introduzir regressões e melhorar a métrica-alvo."
                    ),
                    rollback=s.get("rollback") or (
                        "Restaurar a versão anterior do componente."
                    )
                )
                criadas.append(p)
        return criadas
