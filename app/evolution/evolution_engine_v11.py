from __future__ import annotations
import hashlib, json, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path

class EvolutionEngineV11:
    """
    Motor contínuo de evolução da Ashley.

    Autonomia:
      observar -> agregar -> propor -> preparar autoprogramação -> sandbox/testes
      -> avaliar -> aprender -> colocar candidata na fila de promoção.

    A promoção da instalação ativa continua separada do ciclo autônomo.
    """

    DEFAULT_POLICY = {
        "auto_observar": True,
        "auto_propor": True,
        "auto_programar_sandbox": True,
        "auto_testar": True,
        "auto_revisar": True,
        "auto_promover_producao": False,
        "min_ocorrencias": 3,
        "janela_observacoes": 50,
        "max_tentativas_correcao": 2,
    }

    def __init__(self, db_path, self_coder, autonomous_coder):
        self.db_path = str(db_path)
        self.self_coder = self_coder
        self.autonomous_coder = autonomous_coder
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def _init_db(self):
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS evolucao_v11_politica(
                user_id INTEGER PRIMARY KEY,
                politica_json TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS evolucao_v11_sinais(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                descricao TEXT NOT NULL,
                componente TEXT,
                severidade INTEGER NOT NULL DEFAULT 1,
                dados_json TEXT,
                criado_em TEXT NOT NULL
            )""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_v11_sinais
                ON evolucao_v11_sinais(user_id,fingerprint)""")
            c.execute("""CREATE TABLE IF NOT EXISTS evolucao_v11_ciclos(
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                fingerprint TEXT NOT NULL,
                proposta_id TEXT,
                estado TEXT NOT NULL,
                ocorrencias INTEGER NOT NULL,
                resumo TEXT,
                resultado_json TEXT,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS evolucao_v11_aprendizados(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ciclo_id TEXT NOT NULL,
                licao TEXT NOT NULL,
                dados_json TEXT,
                criado_em TEXT NOT NULL
            )""")

    def politica(self, user_id):
        with self._conn() as c:
            r=c.execute("SELECT politica_json FROM evolucao_v11_politica WHERE user_id=?",
                        (user_id,)).fetchone()
        p=dict(self.DEFAULT_POLICY)
        if r:
            p.update(json.loads(r[0]))
        return p

    def definir_politica(self, user_id, **mudancas):
        permitidas=set(self.DEFAULT_POLICY)
        desconhecidas=set(mudancas)-permitidas
        if desconhecidas:
            raise ValueError(f"Políticas desconhecidas: {sorted(desconhecidas)}")
        # Produção nunca é ligada implicitamente.
        if mudancas.get("auto_promover_producao") is True:
            raise PermissionError("Promoção autônoma em produção não pode ser habilitada pela V11.")
        p=self.politica(user_id); p.update(mudancas)
        with self._conn() as c:
            c.execute("""INSERT INTO evolucao_v11_politica(user_id,politica_json,atualizado_em)
                         VALUES(?,?,?)
                         ON CONFLICT(user_id) DO UPDATE SET
                         politica_json=excluded.politica_json,
                         atualizado_em=excluded.atualizado_em""",
                      (user_id,json.dumps(p,ensure_ascii=False),self._now()))
        return p

    def _fingerprint(self, categoria, componente, descricao):
        txt=f"{categoria}|{componente or ''}|{descricao}".lower()
        txt=re.sub(r"\d+","N",txt)
        txt=re.sub(r"\s+"," ",txt).strip()
        return hashlib.sha256(txt.encode("utf-8")).hexdigest()[:20]

    def observar(self, user_id, categoria, descricao, componente=None,
                 severidade=1, dados=None):
        fp=self._fingerprint(categoria,componente,descricao)
        with self._conn() as c:
            c.execute("""INSERT INTO evolucao_v11_sinais
                (user_id,categoria,fingerprint,descricao,componente,severidade,dados_json,criado_em)
                VALUES(?,?,?,?,?,?,?,?)""",
                (user_id,categoria,fp,descricao,componente,int(severidade),
                 json.dumps(dados or {},ensure_ascii=False),self._now()))
        return {"fingerprint":fp,"categoria":categoria,"descricao":descricao}

    def observar_interacao(self, user_id, mensagem, resposta=None, erro=None,
                           preparacao=None):
        sinais=[]
        m=(mensagem or "").lower()
        r=(resposta or "").lower()
        if erro:
            sinais.append(self.observar(user_id,"erro_execucao",
                f"Falha operacional recorrente: {str(erro)[:240]}",
                "runtime",4,{"erro":str(erro)[:1000]}))
        negativos=("não funcionou","nao funcionou","deu errado","continua errado",
                   "não resolveu","nao resolveu","você repetiu","voce repetiu")
        if any(x in m for x in negativos):
            sinais.append(self.observar(user_id,"feedback_negativo",
                "Usuário relatou que a solução/resposta anterior não resolveu adequadamente.",
                "orquestrador",3,{"mensagem":mensagem[:1000]}))
        if resposta and len(r)>80 and mensagem and mensagem.lower().strip() in r:
            sinais.append(self.observar(user_id,"qualidade_resposta",
                "Resposta reproduziu excessivamente a mensagem do usuário.",
                "orquestrador",2))
        prep=preparacao or {}
        if prep.get("replanejamentos",0):
            sinais.append(self.observar(user_id,"replanejamento",
                "Interação exigiu replanejamento do fluxo de resolução.",
                "planner",2,{"quantidade":prep.get("replanejamentos")}))
        return sinais

    def candidatos(self, user_id):
        p=self.politica(user_id)
        limite=int(p["janela_observacoes"])
        with self._conn() as c:
            rows=c.execute("""SELECT fingerprint,categoria,componente,descricao,
                       COUNT(*) n,MAX(severidade) sev
                       FROM (SELECT * FROM evolucao_v11_sinais
                             WHERE user_id=? ORDER BY id DESC LIMIT ?)
                       GROUP BY fingerprint,categoria,componente,descricao
                       HAVING COUNT(*)>=?
                       ORDER BY sev DESC,n DESC""",
                    (user_id,limite,int(p["min_ocorrencias"]))).fetchall()
        return [{"fingerprint":x[0],"categoria":x[1],"componente":x[2],
                 "descricao":x[3],"ocorrencias":x[4],"severidade":x[5]} for x in rows]

    def ja_tem_ciclo(self, user_id, fingerprint):
        with self._conn() as c:
            r=c.execute("""SELECT id,estado,proposta_id FROM evolucao_v11_ciclos
                           WHERE user_id=? AND fingerprint=?
                           ORDER BY criado_em DESC LIMIT 1""",
                        (user_id,fingerprint)).fetchone()
        return {"id":r[0],"estado":r[1],"proposta_id":r[2]} if r else None

    def abrir_ciclo(self, user_id, candidato, proposta_id=None):
        cid="C11-"+hashlib.sha256(
            f"{user_id}|{candidato['fingerprint']}|{self._now()}".encode()
        ).hexdigest()[:12].upper()
        now=self._now()
        with self._conn() as c:
            c.execute("""INSERT INTO evolucao_v11_ciclos
                (id,user_id,fingerprint,proposta_id,estado,ocorrencias,resumo,
                 resultado_json,criado_em,atualizado_em)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (cid,user_id,candidato["fingerprint"],proposta_id,"DETECTADO",
                 candidato["ocorrencias"],candidato["descricao"],"{}",now,now))
        return cid

    def atualizar_ciclo(self, ciclo_id, estado, proposta_id=None, resultado=None):
        with self._conn() as c:
            c.execute("""UPDATE evolucao_v11_ciclos SET estado=?,
                         proposta_id=COALESCE(?,proposta_id),resultado_json=?,
                         atualizado_em=? WHERE id=?""",
                      (estado,proposta_id,json.dumps(resultado or {},ensure_ascii=False),
                       self._now(),ciclo_id))

    def aprender(self,user_id,ciclo_id,licao,dados=None):
        with self._conn() as c:
            c.execute("""INSERT INTO evolucao_v11_aprendizados
                         (user_id,ciclo_id,licao,dados_json,criado_em)
                         VALUES(?,?,?,?,?)""",
                      (user_id,ciclo_id,licao,json.dumps(dados or {},ensure_ascii=False),
                       self._now()))

    def painel(self,user_id,limite=30):
        with self._conn() as c:
            ciclos=c.execute("""SELECT id,fingerprint,proposta_id,estado,ocorrencias,
                         resumo,resultado_json,criado_em,atualizado_em
                         FROM evolucao_v11_ciclos WHERE user_id=?
                         ORDER BY atualizado_em DESC LIMIT ?""",(user_id,limite)).fetchall()
            aprend=c.execute("""SELECT ciclo_id,licao,dados_json,criado_em
                         FROM evolucao_v11_aprendizados WHERE user_id=?
                         ORDER BY id DESC LIMIT ?""",(user_id,limite)).fetchall()
        return {
            "politica":self.politica(user_id),
            "candidatos":self.candidatos(user_id),
            "ciclos":[{"id":r[0],"fingerprint":r[1],"proposta_id":r[2],
                       "estado":r[3],"ocorrencias":r[4],"resumo":r[5],
                       "resultado":json.loads(r[6] or "{}"),"criado_em":r[7],
                       "atualizado_em":r[8]} for r in ciclos],
            "aprendizados":[{"ciclo_id":r[0],"licao":r[1],
                             "dados":json.loads(r[2] or "{}"),"criado_em":r[3]}
                            for r in aprend]
        }
