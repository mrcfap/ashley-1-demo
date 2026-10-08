import os
import sqlite3
from typing import Dict, List, Any, Optional

DB_PATH = os.path.join("data", "ashley_memoria.db")


class MotorPersonalidadeAdaptativa:
    """
    FPA V14 - Framework de Personalidade Adaptativa da Ashley.

    Responsabilidades:
    - analisar sinais objetivos da interação;
    - manter um estado comportamental adaptativo;
    - ajustar a forma de comunicação;
    - registrar mudanças relevantes;
    - fornecer contexto comportamental ao Orquestrador.

    O FPA não representa emoções reais.
    Ele modela estratégias de interação e comunicação.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

        diretorio = os.path.dirname(self.db_path)
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)

        self._inicializar_banco()

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_banco(self):
        with self._conectar() as conn:

            # Estado adaptativo atual.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_estado_adaptativo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    modo_comunicacao TEXT DEFAULT 'equilibrado',
                    nivel_empatia REAL DEFAULT 0.75,
                    nivel_cautela REAL DEFAULT 0.60,
                    nivel_diretividade REAL DEFAULT 0.65,
                    profundidade_tecnica REAL DEFAULT 0.65,
                    nivel_iniciativa REAL DEFAULT 0.60,
                    confianca_contextual REAL DEFAULT 0.50,
                    motivo_adaptacao TEXT,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Histórico das adaptações realizadas.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_historico_adaptativo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    contexto TEXT,
                    sinal_detectado TEXT,
                    modo_anterior TEXT,
                    modo_novo TEXT,
                    motivo TEXT,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Diário metacognitivo.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_diario_metacognitivo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    contexto TEXT,
                    observacao TEXT,
                    estrategia_adotada TEXT,
                    resultado TEXT,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    @staticmethod
    def _limitar(valor: float) -> float:
        """Mantém valores adaptativos entre 0.0 e 1.0."""
        return round(max(0.0, min(float(valor), 1.0)), 2)

    def obter_estado(
        self,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:

        with self._conectar() as conn:

            if user_id is None:
                estado = conn.execute("""
                    SELECT *
                    FROM ashley_estado_adaptativo
                    WHERE user_id IS NULL
                    ORDER BY id DESC
                    LIMIT 1
                """).fetchone()
            else:
                estado = conn.execute("""
                    SELECT *
                    FROM ashley_estado_adaptativo
                    WHERE user_id = ?
                    ORDER BY id DESC
                    LIMIT 1
                """, (user_id,)).fetchone()

            if estado:
                return dict(estado)

        # Estado-base da personalidade.
        return {
            "user_id": user_id,
            "modo_comunicacao": "equilibrado",
            "nivel_empatia": 0.75,
            "nivel_cautela": 0.60,
            "nivel_diretividade": 0.65,
            "profundidade_tecnica": 0.65,
            "nivel_iniciativa": 0.60,
            "confianca_contextual": 0.50,
            "motivo_adaptacao": "estado_base"
        }

    def analisar_interacao(
        self,
        mensagem: str,
        complexidade: str = "baixa",
        repeticoes_erro: int = 0,
        bloqueios: int = 0,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:

        texto = (mensagem or "").lower().strip()
        complexidade = (complexidade or "baixa").lower().strip()

        estado_anterior = self.obter_estado(user_id)

        modo = "equilibrado"
        empatia = 0.75
        cautela = 0.60
        diretividade = 0.65
        profundidade = 0.65
        iniciativa = 0.60
        confianca = 0.60

        sinais: List[str] = []

        # --------------------------------------------------
        # ERROS E PROBLEMAS
        # --------------------------------------------------

        palavras_erro = (
            "erro",
            "problema",
            "falhou",
            "não funciona",
            "nao funciona",
            "quebrou",
            "exception",
            "traceback"
        )

        if any(palavra in texto for palavra in palavras_erro):
            sinais.append("problema_tecnico")
            modo = "tecnico_cauteloso"
            cautela += 0.20
            diretividade += 0.15
            profundidade += 0.15
            iniciativa += 0.10

        # --------------------------------------------------
        # REPETIÇÃO DE ERROS
        # --------------------------------------------------

        if repeticoes_erro >= 2:
            sinais.append("erro_recorrente")
            modo = "diagnostico_estruturado"
            cautela += 0.20
            diretividade += 0.20
            profundidade += 0.15

        # --------------------------------------------------
        # BLOQUEIOS
        # --------------------------------------------------

        if bloqueios > 0:
            sinais.append("bloqueio_operacional")
            modo = "resolutivo"
            diretividade += 0.20
            iniciativa += 0.15

        # --------------------------------------------------
        # COMPLEXIDADE
        # --------------------------------------------------

        if complexidade in ("alta", "critica"):
            sinais.append("alta_complexidade")
            cautela += 0.15
            profundidade += 0.20
            diretividade += 0.10
            confianca -= 0.10

        # --------------------------------------------------
        # SINAIS DE FRUSTRAÇÃO EXPRESSA
        # --------------------------------------------------

        palavras_frustracao = (
            "cansado",
            "cansada",
            "frustrado",
            "frustrada",
            "difícil",
            "dificil",
            "complicado",
            "não aguento",
            "nao aguento"
        )

        if any(palavra in texto for palavra in palavras_frustracao):
            sinais.append("frustracao_expressa")
            empatia += 0.15
            diretividade -= 0.10

            if modo == "equilibrado":
                modo = "acolhedor_objetivo"

        # --------------------------------------------------
        # FEEDBACK POSITIVO
        # --------------------------------------------------

        palavras_positivas = (
            "excelente",
            "ótimo",
            "otimo",
            "perfeito",
            "parabéns",
            "parabens",
            "muito bom"
        )

        if any(palavra in texto for palavra in palavras_positivas):
            sinais.append("feedback_positivo")

            if modo == "equilibrado":
                modo = "colaborativo_positivo"

            iniciativa += 0.05
            confianca += 0.10

        # --------------------------------------------------
        # PEDIDO TÉCNICO
        # --------------------------------------------------

        palavras_tecnicas = (
            "código",
            "codigo",
            "python",
            "fastapi",
            "sqlite",
            "api",
            "classe",
            "função",
            "funcao",
            "banco",
            "powershell"
        )

        if any(palavra in texto for palavra in palavras_tecnicas):
            sinais.append("contexto_tecnico")
            profundidade += 0.15

            if modo == "equilibrado":
                modo = "tecnico_colaborativo"

        # --------------------------------------------------
        # NORMALIZAÇÃO
        # --------------------------------------------------

        empatia = self._limitar(empatia)
        cautela = self._limitar(cautela)
        diretividade = self._limitar(diretividade)
        profundidade = self._limitar(profundidade)
        iniciativa = self._limitar(iniciativa)
        confianca = self._limitar(confianca)

        if not sinais:
            sinais.append("interacao_neutra")

        motivo = ", ".join(sinais)

        novo_estado = {
            "user_id": user_id,
            "modo_comunicacao": modo,
            "nivel_empatia": empatia,
            "nivel_cautela": cautela,
            "nivel_diretividade": diretividade,
            "profundidade_tecnica": profundidade,
            "nivel_iniciativa": iniciativa,
            "confianca_contextual": confianca,
            "motivo_adaptacao": motivo
        }

        self._salvar_estado(
            novo_estado,
            estado_anterior,
            texto,
            sinais
        )

        return novo_estado

    def _salvar_estado(
        self,
        estado: Dict[str, Any],
        estado_anterior: Dict[str, Any],
        contexto: str,
        sinais: List[str]
    ):
        with self._conectar() as conn:

            conn.execute("""
                INSERT INTO ashley_estado_adaptativo (
                    user_id,
                    modo_comunicacao,
                    nivel_empatia,
                    nivel_cautela,
                    nivel_diretividade,
                    profundidade_tecnica,
                    nivel_iniciativa,
                    confianca_contextual,
                    motivo_adaptacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                estado["user_id"],
                estado["modo_comunicacao"],
                estado["nivel_empatia"],
                estado["nivel_cautela"],
                estado["nivel_diretividade"],
                estado["profundidade_tecnica"],
                estado["nivel_iniciativa"],
                estado["confianca_contextual"],
                estado["motivo_adaptacao"]
            ))

            conn.execute("""
                INSERT INTO ashley_historico_adaptativo (
                    user_id,
                    contexto,
                    sinal_detectado,
                    modo_anterior,
                    modo_novo,
                    motivo
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                estado["user_id"],
                contexto[:1000],
                ", ".join(sinais),
                estado_anterior.get(
                    "modo_comunicacao",
                    "equilibrado"
                ),
                estado["modo_comunicacao"],
                estado["motivo_adaptacao"]
            ))

            conn.commit()

    def registrar_reflexao(
        self,
        contexto: str,
        observacao: str,
        estrategia_adotada: str,
        resultado: str = "pendente",
        user_id: Optional[int] = None
    ) -> int:

        with self._conectar() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ashley_diario_metacognitivo (
                    user_id,
                    contexto,
                    observacao,
                    estrategia_adotada,
                    resultado
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                contexto,
                observacao,
                estrategia_adotada,
                resultado
            ))

            conn.commit()

            return cursor.lastrowid

    def gerar_contexto_adaptativo(
        self,
        user_id: Optional[int] = None
    ) -> str:

        estado = self.obter_estado(user_id)

        return (
            "ESTADO COMPORTAMENTAL ADAPTATIVO:\n"
            f"- Modo de comunicação: "
            f"{estado['modo_comunicacao']}\n"
            f"- Empatia: {estado['nivel_empatia']}\n"
            f"- Cautela: {estado['nivel_cautela']}\n"
            f"- Diretividade: "
            f"{estado['nivel_diretividade']}\n"
            f"- Profundidade técnica: "
            f"{estado['profundidade_tecnica']}\n"
            f"- Iniciativa: "
            f"{estado['nivel_iniciativa']}\n"
            f"- Confiança contextual: "
            f"{estado['confianca_contextual']}\n"
            f"- Motivo da adaptação: "
            f"{estado['motivo_adaptacao']}\n"
            "\n"
            "Use este estado apenas para modular a forma da resposta. "
            "Não descreva esses valores ao usuário, salvo se ele pedir."
        )

    def estado_fpa(
        self,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:

        estado = self.obter_estado(user_id)

        return {
            "motor": "FPA",
            "versao": "V14",
            "ativo": True,
            "modo_comunicacao":
                estado["modo_comunicacao"],
            "nivel_empatia":
                estado["nivel_empatia"],
            "nivel_cautela":
                estado["nivel_cautela"],
            "nivel_diretividade":
                estado["nivel_diretividade"],
            "profundidade_tecnica":
                estado["profundidade_tecnica"],
            "nivel_iniciativa":
                estado["nivel_iniciativa"],
            "confianca_contextual":
                estado["confianca_contextual"],
            "db_path": self.db_path
        }