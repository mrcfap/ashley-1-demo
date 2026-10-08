import os
import sqlite3
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join("data", "ashley_memoria.db")

STATUS_VALIDOS = {
    "pendente",
    "planejado",
    "em_andamento",
    "aguardando",
    "bloqueado",
    "validando",
    "concluido",
    "cancelado",
}

PRIORIDADES_VALIDAS = {"baixa", "normal", "alta", "critica"}

ORIGENS_VALIDAS = {
    "usuario",
    "memoria",
    "ferramenta",
    "web",
    "inferencia",
    "autoevolucao",
    "sistema",
}


class MotorContinuidadeCognitiva:
    """
    Motor de Continuidade Cognitiva (MCC) da Ashley.

    Mantém objetivos e subobjetivos persistentes, decisões e consequências,
    metacognição operacional, próxima ação e governança proporcional ao risco.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        diretorio = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(diretorio, exist_ok=True)
        self._inicializar_banco()

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _agora() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _colunas(self, conn: sqlite3.Connection, tabela: str) -> set:
        return {row["name"] for row in conn.execute(f"PRAGMA table_info({tabela})")}

    def _adicionar_coluna_se_necessario(
        self, conn: sqlite3.Connection, tabela: str, coluna: str, definicao: str
    ) -> None:
        if coluna not in self._colunas(conn, tabela):
            conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")

    def _inicializar_banco(self) -> None:
        """
        Cria as tabelas e faz migrações aditivas.
        Não apaga os dados da versão anterior do motor.
        """
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_objetivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    descricao TEXT,
                    contexto_origem TEXT,
                    status TEXT DEFAULT 'pendente',
                    progresso REAL DEFAULT 0.0,
                    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migração segura da tabela da versão inicial.
            novas_colunas_objetivos = {
                "objetivo_pai_id": "INTEGER",
                "prioridade": "TEXT DEFAULT 'normal'",
                "motivo": "TEXT",
                "proxima_acao": "TEXT",
                "dependencia": "TEXT",
                "bloqueio": "TEXT",
                "criterio_conclusao": "TEXT",
                "origem_informacao": "TEXT DEFAULT 'usuario'",
                "grau_confianca": "REAL DEFAULT 1.0",
                "concluido_em": "TEXT",
            }
            for coluna, definicao in novas_colunas_objetivos.items():
                self._adicionar_coluna_se_necessario(
                    conn, "ashley_objetivos", coluna, definicao
                )

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_decisoes_consequencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objetivo_id INTEGER,
                    decisao TEXT NOT NULL,
                    motivos TEXT,
                    consequencia_esperada TEXT,
                    consequencia_real TEXT,
                    resultado_sucesso INTEGER,
                    aprendizado TEXT,
                    origem_informacao TEXT DEFAULT 'sistema',
                    grau_confianca REAL DEFAULT 1.0,
                    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(objetivo_id) REFERENCES ashley_objetivos(id)
                )
            """)
            self._adicionar_coluna_se_necessario(
                conn, "ashley_decisoes_consequencias",
                "origem_informacao", "TEXT DEFAULT 'sistema'"
            )
            self._adicionar_coluna_se_necessario(
                conn, "ashley_decisoes_consequencias",
                "grau_confianca", "REAL DEFAULT 1.0"
            )

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_metacognicao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objetivo_id INTEGER,
                    tarefa TEXT NOT NULL,
                    tentativa TEXT,
                    resultado TEXT,
                    aprendizado TEXT,
                    grau_confianca REAL,
                    proxima_acao_sugerida TEXT,
                    origem_informacao TEXT DEFAULT 'inferencia',
                    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(objetivo_id) REFERENCES ashley_objetivos(id)
                )
            """)
            self._adicionar_coluna_se_necessario(
                conn, "ashley_metacognicao", "objetivo_id", "INTEGER"
            )
            self._adicionar_coluna_se_necessario(
                conn, "ashley_metacognicao",
                "origem_informacao", "TEXT DEFAULT 'inferencia'"
            )

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_acoes_continuidade (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objetivo_id INTEGER,
                    acao TEXT NOT NULL,
                    tipo_acao TEXT NOT NULL,
                    nivel_risco INTEGER NOT NULL,
                    autorizacao_necessaria INTEGER NOT NULL DEFAULT 0,
                    autorizado INTEGER,
                    executado INTEGER NOT NULL DEFAULT 0,
                    resultado TEXT,
                    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(objetivo_id) REFERENCES ashley_objetivos(id)
                )
            """)

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ashley_objetivos_status "
                "ON ashley_objetivos(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ashley_objetivos_pai "
                "ON ashley_objetivos(objetivo_pai_id)"
            )
            conn.commit()

    @staticmethod
    def _validar_confianca(valor: float) -> float:
        valor = float(valor)
        if not 0.0 <= valor <= 1.0:
            raise ValueError("grau_confianca deve estar entre 0.0 e 1.0")
        return valor

    @staticmethod
    def _validar_progresso(valor: float) -> float:
        valor = float(valor)
        if not 0.0 <= valor <= 100.0:
            raise ValueError("progresso deve estar entre 0 e 100")
        return valor

    def criar_objetivo(
        self,
        titulo: str,
        descricao: str = "",
        contexto_origem: str = "",
        motivo: str = "",
        prioridade: str = "normal",
        proxima_acao: str = "",
        criterio_conclusao: str = "",
        origem_informacao: str = "usuario",
        grau_confianca: float = 1.0,
        objetivo_pai_id: Optional[int] = None,
    ) -> int:
        if prioridade not in PRIORIDADES_VALIDAS:
            raise ValueError(f"prioridade inválida: {prioridade}")
        if origem_informacao not in ORIGENS_VALIDAS:
            raise ValueError(f"origem_informacao inválida: {origem_informacao}")
        confianca = self._validar_confianca(grau_confianca)
        agora = self._agora()

        with self._conectar() as conn:
            cursor = conn.execute("""
                INSERT INTO ashley_objetivos (
                    titulo, descricao, contexto_origem, status, progresso,
                    objetivo_pai_id, prioridade, motivo, proxima_acao,
                    criterio_conclusao, origem_informacao, grau_confianca,
                    criado_em, atualizado_em
                )
                VALUES (?, ?, ?, 'em_andamento', 0.0, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                titulo, descricao, contexto_origem, objetivo_pai_id, prioridade,
                motivo, proxima_acao, criterio_conclusao, origem_informacao,
                confianca, agora, agora
            ))
            conn.commit()
            return int(cursor.lastrowid)

    def criar_subobjetivo(
        self,
        objetivo_pai_id: int,
        titulo: str,
        descricao: str = "",
        **kwargs: Any,
    ) -> int:
        if not self.obter_objetivo(objetivo_pai_id):
            raise ValueError(f"objetivo-pai {objetivo_pai_id} não existe")
        return self.criar_objetivo(
            titulo=titulo,
            descricao=descricao,
            objetivo_pai_id=objetivo_pai_id,
            **kwargs,
        )

    def obter_objetivo(self, objetivo_id: int) -> Optional[Dict[str, Any]]:
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT * FROM ashley_objetivos WHERE id = ?", (objetivo_id,)
            ).fetchone()
            return dict(row) if row else None

    def listar_objetivos_ativos(self) -> List[Dict[str, Any]]:
        with self._conectar() as conn:
            rows = conn.execute("""
                SELECT * FROM ashley_objetivos
                WHERE status NOT IN ('concluido', 'cancelado')
                ORDER BY
                    CASE prioridade
                        WHEN 'critica' THEN 1
                        WHEN 'alta' THEN 2
                        WHEN 'normal' THEN 3
                        ELSE 4
                    END,
                    atualizado_em DESC
            """).fetchall()
            return [dict(row) for row in rows]

    def listar_subobjetivos(self, objetivo_pai_id: int) -> List[Dict[str, Any]]:
        with self._conectar() as conn:
            rows = conn.execute("""
                SELECT * FROM ashley_objetivos
                WHERE objetivo_pai_id = ?
                ORDER BY atualizado_em DESC
            """, (objetivo_pai_id,)).fetchall()
            return [dict(row) for row in rows]

    def atualizar_objetivo(
        self,
        objetivo_id: int,
        *,
        status: Optional[str] = None,
        progresso: Optional[float] = None,
        prioridade: Optional[str] = None,
        proxima_acao: Optional[str] = None,
        dependencia: Optional[str] = None,
        bloqueio: Optional[str] = None,
        criterio_conclusao: Optional[str] = None,
    ) -> Dict[str, Any]:
        atual = self.obter_objetivo(objetivo_id)
        if not atual:
            raise ValueError(f"objetivo {objetivo_id} não existe")

        alteracoes: Dict[str, Any] = {}
        if status is not None:
            if status not in STATUS_VALIDOS:
                raise ValueError(f"status inválido: {status}")
            alteracoes["status"] = status
        if progresso is not None:
            alteracoes["progresso"] = self._validar_progresso(progresso)
        if prioridade is not None:
            if prioridade not in PRIORIDADES_VALIDAS:
                raise ValueError(f"prioridade inválida: {prioridade}")
            alteracoes["prioridade"] = prioridade
        if proxima_acao is not None:
            alteracoes["proxima_acao"] = proxima_acao
        if dependencia is not None:
            alteracoes["dependencia"] = dependencia
        if bloqueio is not None:
            alteracoes["bloqueio"] = bloqueio
        if criterio_conclusao is not None:
            alteracoes["criterio_conclusao"] = criterio_conclusao

        if not alteracoes:
            return atual

        alteracoes["atualizado_em"] = self._agora()
        if alteracoes.get("status") == "concluido":
            alteracoes["progresso"] = 100.0
            alteracoes["concluido_em"] = self._agora()

        campos = ", ".join(f"{campo} = ?" for campo in alteracoes)
        valores = list(alteracoes.values()) + [objetivo_id]

        with self._conectar() as conn:
            conn.execute(
                f"UPDATE ashley_objetivos SET {campos} WHERE id = ?", valores
            )
            conn.commit()

        return self.obter_objetivo(objetivo_id) or {}

    def definir_proxima_acao(self, objetivo_id: int, proxima_acao: str) -> Dict[str, Any]:
        return self.atualizar_objetivo(
            objetivo_id, proxima_acao=proxima_acao
        )

    def bloquear_objetivo(
        self, objetivo_id: int, motivo_bloqueio: str, dependencia: str = ""
    ) -> Dict[str, Any]:
        return self.atualizar_objetivo(
            objetivo_id,
            status="bloqueado",
            bloqueio=motivo_bloqueio,
            dependencia=dependencia,
        )

    def concluir_objetivo(self, objetivo_id: int) -> Dict[str, Any]:
        return self.atualizar_objetivo(
            objetivo_id,
            status="concluido",
            progresso=100.0,
            proxima_acao="",
            bloqueio="",
        )

    def avaliar_risco_e_autonomia(
        self,
        acao_proposta: str,
        tipo_acao: str,
        objetivo_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Nível 1: baixo risco e reversível -> execução autônoma permitida.
        Nível 2: impacto moderado -> pode preparar/testar em sandbox,
                 mas promoção para ambiente principal exige autorização.
        Nível 3: alto risco, externo ou irreversível -> autorização humana obrigatória.
        """
        tipos_alto_risco = {
            "exclusao_dados",
            "alteracao_financeira",
            "envio_externo",
            "modificacao_estrutural_critica",
            "alteracao_permissoes",
            "alteracao_seguranca",
            "publicacao_producao",
            "execucao_sistema_externo",
        }
        tipos_medio_risco = {
            "modificacao_codigo_principal",
            "alteracao_config_ambiente",
            "instalacao_dependencia",
            "migracao_banco",
        }

        if tipo_acao in tipos_alto_risco:
            nivel = 3
            autorizacao_necessaria = True
            pode_executar = False
            escopo_permitido = "propor"
            mensagem = (
                "Alto risco: a Ashley pode analisar e propor, "
                "mas deve aguardar autorização humana antes de executar."
            )
        elif tipo_acao in tipos_medio_risco:
            nivel = 2
            autorizacao_necessaria = True
            pode_executar = False
            escopo_permitido = "sandbox"
            mensagem = (
                "Risco moderado: a Ashley pode preparar e testar em sandbox/workspace. "
                "Alteração no ambiente principal exige autorização humana."
            )
        else:
            nivel = 1
            autorizacao_necessaria = False
            pode_executar = True
            escopo_permitido = "execucao_reversivel"
            mensagem = "Baixo risco: execução autônoma e reversível permitida com registro."

        with self._conectar() as conn:
            cursor = conn.execute("""
                INSERT INTO ashley_acoes_continuidade (
                    objetivo_id, acao, tipo_acao, nivel_risco,
                    autorizacao_necessaria, executado
                )
                VALUES (?, ?, ?, ?, ?, 0)
            """, (
                objetivo_id, acao_proposta, tipo_acao, nivel,
                int(autorizacao_necessaria)
            ))
            conn.commit()
            acao_id = int(cursor.lastrowid)

        return {
            "acao_id": acao_id,
            "acao": acao_proposta,
            "tipo_acao": tipo_acao,
            "nivel_risco": nivel,
            "autorizacao_necessaria": autorizacao_necessaria,
            "pode_executar_agora": pode_executar,
            "escopo_permitido": escopo_permitido,
            "mensagem": mensagem,
        }

    def registrar_decisao_consequencia(
        self,
        objetivo_id: Optional[int],
        decisao: str,
        motivos: str = "",
        consequencia_esperada: str = "",
        consequencia_real: str = "",
        sucesso: Optional[bool] = None,
        aprendizado: str = "",
        origem_informacao: str = "sistema",
        grau_confianca: float = 1.0,
    ) -> int:
        if origem_informacao not in ORIGENS_VALIDAS:
            raise ValueError(f"origem_informacao inválida: {origem_informacao}")
        confianca = self._validar_confianca(grau_confianca)
        sucesso_db = None if sucesso is None else int(bool(sucesso))

        with self._conectar() as conn:
            cursor = conn.execute("""
                INSERT INTO ashley_decisoes_consequencias (
                    objetivo_id, decisao, motivos, consequencia_esperada,
                    consequencia_real, resultado_sucesso, aprendizado,
                    origem_informacao, grau_confianca
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                objetivo_id, decisao, motivos, consequencia_esperada,
                consequencia_real, sucesso_db, aprendizado,
                origem_informacao, confianca
            ))
            conn.commit()
            return int(cursor.lastrowid)

    # ==================================================
    # V17 - EXPERIÊNCIA, DECISÃO E CONSEQUÊNCIA (MEDC)
    # ==================================================

    @staticmethod
    def _normalizar_texto_experiencia(texto: str) -> str:
        """Normaliza texto para comparação lexical local, sem depender de LLM."""
        texto = unicodedata.normalize("NFKD", str(texto or ""))
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = texto.lower()
        return " ".join(re.findall(r"[a-z0-9]+", texto))

    @classmethod
    def _tokens_experiencia(cls, texto: str) -> set[str]:
        normalizado = cls._normalizar_texto_experiencia(texto)
        return {
            token for token in normalizado.split()
            if len(token) >= 3
        }

    @classmethod
    def _similaridade_experiencia(cls, atual: str, anterior: str) -> float:
        """
        Similaridade Jaccard simples e auditável.
        Serve como primeira camada local do V17; futuramente pode ser
        complementada por embeddings sem alterar o contrato deste método.
        """
        a = cls._tokens_experiencia(atual)
        b = cls._tokens_experiencia(anterior)
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def obter_decisao_consequencia(self, decisao_id: int) -> Optional[Dict[str, Any]]:
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT * FROM ashley_decisoes_consequencias WHERE id = ?",
                (decisao_id,)
            ).fetchone()
            return dict(row) if row else None

    def concluir_decisao_consequencia(
        self,
        decisao_id: int,
        consequencia_real: str,
        sucesso: bool,
        aprendizado: str,
        grau_confianca: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Fecha o ciclo de uma decisão já registrada:
        decisão -> consequência real -> avaliação -> aprendizado.
        """
        atual = self.obter_decisao_consequencia(decisao_id)
        if not atual:
            raise ValueError(f"decisão {decisao_id} não existe")

        campos = {
            "consequencia_real": consequencia_real,
            "resultado_sucesso": int(bool(sucesso)),
            "aprendizado": aprendizado,
        }
        if grau_confianca is not None:
            campos["grau_confianca"] = self._validar_confianca(grau_confianca)

        set_sql = ", ".join(f"{campo} = ?" for campo in campos)
        valores = list(campos.values()) + [decisao_id]

        with self._conectar() as conn:
            conn.execute(
                f"UPDATE ashley_decisoes_consequencias SET {set_sql} WHERE id = ?",
                valores
            )
            conn.commit()

        return self.obter_decisao_consequencia(decisao_id) or {}

    def buscar_experiencias_semelhantes(
        self,
        contexto_atual: str,
        objetivo_id: Optional[int] = None,
        limite: int = 5,
        similaridade_minima: float = 0.12,
        somente_concluidas: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Recupera experiências anteriores relevantes usando somente dados locais.

        O V17 não trata similaridade como certeza. Cada resultado mantém
        separadas a similaridade lexical, a confiança registrada e o desfecho.
        """
        limite = max(1, min(int(limite), 20))
        similaridade_minima = max(0.0, min(float(similaridade_minima), 1.0))

        filtros = []
        parametros: List[Any] = []

        if objetivo_id is not None:
            filtros.append("(objetivo_id = ? OR objetivo_id IS NULL)")
            parametros.append(objetivo_id)

        if somente_concluidas:
            filtros.append("resultado_sucesso IS NOT NULL")
            filtros.append("TRIM(COALESCE(consequencia_real, '')) <> ''")

        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        with self._conectar() as conn:
            rows = conn.execute(f"""
                SELECT * FROM ashley_decisoes_consequencias
                {where}
                ORDER BY criado_em DESC, id DESC
                LIMIT 250
            """, parametros).fetchall()

        experiencias: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            texto_anterior = " ".join([
                item.get("decisao") or "",
                item.get("motivos") or "",
                item.get("consequencia_esperada") or "",
                item.get("consequencia_real") or "",
                item.get("aprendizado") or "",
            ])
            similaridade = self._similaridade_experiencia(
                contexto_atual, texto_anterior
            )
            if similaridade < similaridade_minima:
                continue

            item["similaridade"] = round(similaridade, 4)
            item["sucesso"] = (
                None if item.get("resultado_sucesso") is None
                else bool(item.get("resultado_sucesso"))
            )
            experiencias.append(item)

        experiencias.sort(
            key=lambda x: (
                x.get("similaridade", 0.0),
                float(x.get("grau_confianca") or 0.0),
                int(x.get("id") or 0),
            ),
            reverse=True,
        )
        return experiencias[:limite]

    def orientar_por_experiencia(
        self,
        contexto_atual: str,
        objetivo_id: Optional[int] = None,
        limite: int = 5,
    ) -> Dict[str, Any]:
        """
        Converte experiências anteriores em contexto de apoio à decisão.

        Importante: o V17 aconselha o planejamento, mas não concede permissão
        de execução. A governança continua em avaliar_risco_e_autonomia().
        """
        experiencias = self.buscar_experiencias_semelhantes(
            contexto_atual=contexto_atual,
            objetivo_id=objetivo_id,
            limite=limite,
        )

        if not experiencias:
            return {
                "v17_ativo": True,
                "ha_experiencia_relevante": False,
                "quantidade": 0,
                "confianca_agregada": 0.0,
                "orientacao": (
                    "Não há experiência anterior suficientemente semelhante. "
                    "Planejar sem assumir que existe precedente confiável."
                ),
                "aprendizados": [],
                "experiencias": [],
                "governanca": (
                    "Experiência passada não autoriza ações de risco moderado "
                    "ou alto."
                ),
            }

        pesos = []
        sucessos_ponderados = 0.0
        aprendizados = []

        for exp in experiencias:
            peso = (
                float(exp.get("similaridade") or 0.0)
                * float(exp.get("grau_confianca") or 0.0)
            )
            pesos.append(peso)
            if exp.get("sucesso") is True:
                sucessos_ponderados += peso
            if exp.get("aprendizado"):
                aprendizados.append(exp["aprendizado"])

        peso_total = sum(pesos)
        taxa_sucesso = (
            sucessos_ponderados / peso_total
            if peso_total > 0
            else 0.0
        )
        confianca_agregada = (
            sum(pesos) / len(pesos)
            if pesos
            else 0.0
        )

        if taxa_sucesso >= 0.70:
            orientacao = (
                "Há precedentes positivos relevantes. Considere reutilizar "
                "os princípios que funcionaram, revalidando o contexto atual."
            )
        elif taxa_sucesso <= 0.30:
            orientacao = (
                "Há precedentes relevantes com resultados predominantemente "
                "negativos. Evite repetir a mesma estratégia sem revisão."
            )
        else:
            orientacao = (
                "Os precedentes são mistos. Use os aprendizados como contexto, "
                "mas reavalie alternativas antes de decidir."
            )

        return {
            "v17_ativo": True,
            "ha_experiencia_relevante": True,
            "quantidade": len(experiencias),
            "taxa_sucesso_ponderada": round(taxa_sucesso, 4),
            "confianca_agregada": round(confianca_agregada, 4),
            "orientacao": orientacao,
            "aprendizados": aprendizados[:5],
            "experiencias": experiencias,
            "governanca": (
                "Experiência passada influencia a decisão, mas não substitui "
                "avaliação de risco nem autorização humana quando exigida."
            ),
        }

    def registrar_metacognicao(
        self,
        tarefa: str,
        tentativa: str = "",
        resultado: str = "",
        aprendizado: str = "",
        grau_confianca: float = 0.5,
        proxima_acao: str = "",
        objetivo_id: Optional[int] = None,
        origem_informacao: str = "inferencia",
    ) -> int:
        if origem_informacao not in ORIGENS_VALIDAS:
            raise ValueError(f"origem_informacao inválida: {origem_informacao}")
        confianca = self._validar_confianca(grau_confianca)

        with self._conectar() as conn:
            cursor = conn.execute("""
                INSERT INTO ashley_metacognicao (
                    objetivo_id, tarefa, tentativa, resultado, aprendizado,
                    grau_confianca, proxima_acao_sugerida, origem_informacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                objetivo_id, tarefa, tentativa, resultado, aprendizado,
                confianca, proxima_acao, origem_informacao
            ))
            conn.commit()

        if objetivo_id is not None and proxima_acao:
            self.definir_proxima_acao(objetivo_id, proxima_acao)

        return int(cursor.lastrowid)

    def gerar_relatorio_continuidade(self) -> Dict[str, Any]:
        objetivos = self.listar_objetivos_ativos()

        with self._conectar() as conn:
            reflexoes = [
                dict(row) for row in conn.execute("""
                    SELECT * FROM ashley_metacognicao
                    ORDER BY criado_em DESC, id DESC
                    LIMIT 5
                """).fetchall()
            ]
            decisoes = [
                dict(row) for row in conn.execute("""
                    SELECT * FROM ashley_decisoes_consequencias
                    ORDER BY criado_em DESC, id DESC
                    LIMIT 5
                """).fetchall()
            ]

        proximo_objetivo = objetivos[0] if objetivos else None

        return {
            "total_objetivos_ativos": len(objetivos),
            "objetivos": objetivos,
            "objetivo_prioritario": proximo_objetivo,
            "proxima_acao": (
                proximo_objetivo.get("proxima_acao")
                if proximo_objetivo else None
            ),
            "ultimas_decisoes": decisoes,
            "ultimas_reflexoes_metacognitivas": reflexoes,
        }
