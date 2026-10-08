import os
import sqlite3
from typing import Dict, List, Any, Optional


DB_PATH = os.path.join("data", "ashley_memoria.db")


class MotorRessonanciaAntecipacao:
    """
    Motor de Ressonância e Antecipação da Ashley (MRAC).

    Responsabilidades:
    - registrar pontos cegos;
    - produzir contrapontos críticos;
    - registrar sinais operacionais mensuráveis;
    - gerar alertas proativos;
    - fornecer contexto de iniciativa ao orquestrador.

    O MRAC não executa ações críticas diretamente.
    A execução continua subordinada à governança
    e aos guardrails da Ashley.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

        diretorio = os.path.dirname(self.db_path)

        if diretorio:
            os.makedirs(diretorio, exist_ok=True)

        self._inicializar_banco()

    # =========================================================
    # BANCO DE DADOS
    # =========================================================

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_banco(self):
        with self._conectar() as conn:

            # -------------------------------------------------
            # PONTOS CEGOS
            # -------------------------------------------------

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_pontos_cegos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    projeto TEXT NOT NULL,
                    decisao TEXT NOT NULL,
                    risco_identificado TEXT NOT NULL,
                    contraponto TEXT NOT NULL,
                    nivel_risco INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pendente',
                    origem TEXT DEFAULT 'mrac',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # -------------------------------------------------
            # ALERTAS PROATIVOS
            # -------------------------------------------------

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_alertas_proativos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    tipo TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    prioridade INTEGER DEFAULT 3,
                    origem TEXT DEFAULT 'mrac',
                    status TEXT DEFAULT 'pendente',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolvido_em TIMESTAMP
                )
            """)

            # -------------------------------------------------
            # SINAIS OPERACIONAIS
            # -------------------------------------------------

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_sinais_operacionais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    contexto TEXT,
                    complexidade TEXT,
                    repeticoes_erro INTEGER DEFAULT 0,
                    falhas_ferramenta INTEGER DEFAULT 0,
                    bloqueios INTEGER DEFAULT 0,
                    estado_operacional TEXT,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    # =========================================================
    # PONTOS CEGOS
    # =========================================================

    def registrar_ponto_cego(
        self,
        projeto: str,
        decisao: str,
        risco_identificado: str,
        contraponto: str,
        nivel_risco: int = 1,
        user_id: Optional[int] = None
    ) -> int:

        nivel_risco = max(1, min(int(nivel_risco), 3))

        with self._conectar() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ashley_pontos_cegos (
                    user_id,
                    projeto,
                    decisao,
                    risco_identificado,
                    contraponto,
                    nivel_risco
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                projeto,
                decisao,
                risco_identificado,
                contraponto,
                nivel_risco
            ))

            conn.commit()

            return cursor.lastrowid

    def listar_pontos_cegos(
        self,
        user_id: Optional[int] = None,
        somente_pendentes: bool = True,
        limite: int = 20
    ) -> List[Dict[str, Any]]:

        query = """
            SELECT *
            FROM ashley_pontos_cegos
            WHERE 1 = 1
        """

        parametros = []

        if user_id is not None:
            query += " AND user_id = ?"
            parametros.append(user_id)

        if somente_pendentes:
            query += " AND status = 'pendente'"

        query += """
            ORDER BY nivel_risco DESC, criado_em DESC
            LIMIT ?
        """

        parametros.append(limite)

        with self._conectar() as conn:

            cursor = conn.execute(
                query,
                parametros
            )

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

    def atualizar_status_ponto_cego(
        self,
        ponto_id: int,
        novo_status: str
    ) -> bool:

        status_permitidos = {
            "pendente",
            "aceito",
            "ignorado",
            "resolvido"
        }

        novo_status = novo_status.lower().strip()

        if novo_status not in status_permitidos:
            raise ValueError(
                f"Status inválido: {novo_status}"
            )

        with self._conectar() as conn:

            cursor = conn.execute("""
                UPDATE ashley_pontos_cegos
                SET
                    status = ?,
                    atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                novo_status,
                ponto_id
            ))

            conn.commit()

            return cursor.rowcount > 0

    # =========================================================
    # ALERTAS PROATIVOS
    # =========================================================

    def criar_alerta(
        self,
        tipo: str,
        titulo: str,
        descricao: str,
        prioridade: int = 3,
        user_id: Optional[int] = None
    ) -> int:

        prioridade = max(
            1,
            min(int(prioridade), 5)
        )

        with self._conectar() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ashley_alertas_proativos (
                    user_id,
                    tipo,
                    titulo,
                    descricao,
                    prioridade
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                tipo,
                titulo,
                descricao,
                prioridade
            ))

            conn.commit()

            return cursor.lastrowid

    def listar_alertas(
        self,
        user_id: Optional[int] = None,
        somente_pendentes: bool = True,
        limite: int = 20
    ) -> List[Dict[str, Any]]:

        query = """
            SELECT *
            FROM ashley_alertas_proativos
            WHERE 1 = 1
        """

        parametros = []

        if user_id is not None:
            query += " AND user_id = ?"
            parametros.append(user_id)

        if somente_pendentes:
            query += " AND status = 'pendente'"

        query += """
            ORDER BY prioridade DESC, criado_em DESC
            LIMIT ?
        """

        parametros.append(limite)

        with self._conectar() as conn:

            cursor = conn.execute(
                query,
                parametros
            )

            return [
                dict(row)
                for row in cursor.fetchall()
            ]

    def resolver_alerta(
        self,
        alerta_id: int
    ) -> bool:

        with self._conectar() as conn:

            cursor = conn.execute("""
                UPDATE ashley_alertas_proativos
                SET
                    status = 'resolvido',
                    resolvido_em = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                alerta_id,
            ))

            conn.commit()

            return cursor.rowcount > 0

    # =========================================================
    # SINAIS OPERACIONAIS
    # =========================================================

    def registrar_sinal_operacional(
        self,
        contexto: str,
        complexidade: str = "baixa",
        repeticoes_erro: int = 0,
        falhas_ferramenta: int = 0,
        bloqueios: int = 0,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:

        complexidade = (
            complexidade
            or "baixa"
        ).lower().strip()

        complexidades_permitidas = {
            "baixa",
            "media",
            "alta",
            "critica"
        }

        if complexidade not in complexidades_permitidas:
            complexidade = "baixa"

        repeticoes_erro = max(
            0,
            int(repeticoes_erro)
        )

        falhas_ferramenta = max(
            0,
            int(falhas_ferramenta)
        )

        bloqueios = max(
            0,
            int(bloqueios)
        )

        # -------------------------------------------------
        # CÁLCULO OPERACIONAL
        # -------------------------------------------------

        pesos_complexidade = {
            "baixa": 0,
            "media": 1,
            "alta": 2,
            "critica": 3
        }

        pontuacao = pesos_complexidade[
            complexidade
        ]

        pontuacao += min(
            repeticoes_erro,
            3
        )

        pontuacao += min(
            falhas_ferramenta,
            3
        )

        pontuacao += min(
            bloqueios,
            3
        )

        if pontuacao >= 7:
            estado = "critico"

        elif pontuacao >= 4:
            estado = "atencao"

        else:
            estado = "normal"

        # -------------------------------------------------
        # REGISTRO
        # -------------------------------------------------

        with self._conectar() as conn:

            conn.execute("""
                INSERT INTO ashley_sinais_operacionais (
                    user_id,
                    contexto,
                    complexidade,
                    repeticoes_erro,
                    falhas_ferramenta,
                    bloqueios,
                    estado_operacional
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                contexto,
                complexidade,
                repeticoes_erro,
                falhas_ferramenta,
                bloqueios,
                estado
            ))

            conn.commit()

        return {
            "estado_operacional": estado,
            "pontuacao": pontuacao,
            "complexidade": complexidade,
            "repeticoes_erro": repeticoes_erro,
            "falhas_ferramenta": falhas_ferramenta,
            "bloqueios": bloqueios
        }

    # =========================================================
    # CONTEXTO PARA O ORQUESTRADOR
    # =========================================================

    def gerar_contexto_iniciativa(
        self,
        user_id: Optional[int] = None,
        limite: int = 5
    ) -> str:

        pontos_cegos = self.listar_pontos_cegos(
            user_id=user_id,
            somente_pendentes=True,
            limite=limite
        )

        alertas = self.listar_alertas(
            user_id=user_id,
            somente_pendentes=True,
            limite=limite
        )

        partes = []

        if pontos_cegos:

            partes.append(
                "PONTOS CEGOS ATIVOS:"
            )

            for ponto in pontos_cegos:

                partes.append(
                    f"- Projeto: {ponto['projeto']} | "
                    f"Risco: {ponto['risco_identificado']} | "
                    f"Contraponto: {ponto['contraponto']}"
                )

        if alertas:

            partes.append(
                "ALERTAS PROATIVOS:"
            )

            for alerta in alertas:

                partes.append(
                    f"- {alerta['titulo']}: "
                    f"{alerta['descricao']}"
                )

        if not partes:
            return (
                "Nenhum ponto cego ou alerta "
                "proativo pendente."
            )

        return "\n".join(partes)

    # =========================================================
    # ESTADO DO MOTOR
    # =========================================================

    def estado_mrac(
        self,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:

        pontos = self.listar_pontos_cegos(
            user_id=user_id,
            somente_pendentes=True,
            limite=100
        )

        alertas = self.listar_alertas(
            user_id=user_id,
            somente_pendentes=True,
            limite=100
        )

        return {
            "motor": "MRAC",
            "ativo": True,
            "pontos_cegos_pendentes": len(pontos),
            "alertas_pendentes": len(alertas),
            "db_path": self.db_path
        }