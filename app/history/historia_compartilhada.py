import sqlite3
from datetime import datetime


class MotorHistoriaCompartilhada:
    """
    V14 - Motor de HistÃ³ria Compartilhada da Ashley.

    Registra experiÃªncias relevantes da trajetÃ³ria usuÃ¡rio-Ashley
    e permite recuperar experiÃªncias anteriores semelhantes.
    """

    def __init__(self, db_path="data/ashley_memoria.db"):
        self.db_path = db_path
        self._inicializar_banco()

    def _conectar(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_banco(self):
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historia_compartilhada (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_id INTEGER,

                    projeto TEXT,
                    situacao TEXT NOT NULL,

                    decisao TEXT,
                    motivo TEXT,

                    expectativa TEXT,
                    resultado TEXT,
                    consequencia TEXT,

                    aprendizado TEXT,
                    aplicacao_futura TEXT,

                    importancia INTEGER DEFAULT 3,
                    confianca REAL DEFAULT 1.0,

                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_historia_usuario
                ON historia_compartilhada(user_id)
            """)

            conn.commit()

    def registrar_episodio(
        self,
        situacao,
        user_id=None,
        projeto="",
        decisao="",
        motivo="",
        expectativa="",
        resultado="",
        consequencia="",
        aprendizado="",
        aplicacao_futura="",
        importancia=3,
        confianca=1.0
    ):
        agora = datetime.utcnow().isoformat()

        importancia = max(1, min(5, int(importancia)))
        confianca = max(0.0, min(1.0, float(confianca)))

        with self._conectar() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO historia_compartilhada (
                    user_id,
                    projeto,
                    situacao,
                    decisao,
                    motivo,
                    expectativa,
                    resultado,
                    consequencia,
                    aprendizado,
                    aplicacao_futura,
                    importancia,
                    confianca,
                    criado_em,
                    atualizado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                projeto,
                situacao,
                decisao,
                motivo,
                expectativa,
                resultado,
                consequencia,
                aprendizado,
                aplicacao_futura,
                importancia,
                confianca,
                agora,
                agora
            ))

            conn.commit()

            return cursor.lastrowid

    def listar_historia(self, user_id=None, limite=20):
        with self._conectar() as conn:

            if user_id is None:
                rows = conn.execute("""
                    SELECT *
                    FROM historia_compartilhada
                    ORDER BY importancia DESC, criado_em DESC
                    LIMIT ?
                """, (limite,)).fetchall()

            else:
                rows = conn.execute("""
                    SELECT *
                    FROM historia_compartilhada
                    WHERE user_id = ?
                    ORDER BY importancia DESC, criado_em DESC
                    LIMIT ?
                """, (user_id, limite)).fetchall()

        return [dict(row) for row in rows]

    def buscar_experiencias_semelhantes(
        self,
        consulta,
        user_id=None,
        limite=5
    ):
        """
        Primeira versÃ£o conservadora da recuperaÃ§Ã£o por analogia.
        Posteriormente poderÃ¡ usar embeddings/busca semÃ¢ntica.
        """

        termos = [
            termo.lower()
            for termo in consulta.split()
            if len(termo) >= 4
        ]

        episodios = self.listar_historia(
            user_id=user_id,
            limite=100
        )

        resultados = []

        for episodio in episodios:

            texto = " ".join([
                episodio.get("projeto") or "",
                episodio.get("situacao") or "",
                episodio.get("decisao") or "",
                episodio.get("motivo") or "",
                episodio.get("resultado") or "",
                episodio.get("consequencia") or "",
                episodio.get("aprendizado") or "",
                episodio.get("aplicacao_futura") or ""
            ]).lower()

            pontuacao = sum(
                1 for termo in termos
                if termo in texto
            )

            if pontuacao > 0:
                episodio["similaridade"] = pontuacao
                resultados.append(episodio)

        resultados.sort(
            key=lambda x: (
                x["similaridade"],
                x["importancia"]
            ),
            reverse=True
        )

        return resultados[:limite]

    def gerar_contexto_historico(
        self,
        consulta,
        user_id=None,
        limite=3
    ):
        experiencias = self.buscar_experiencias_semelhantes(
            consulta=consulta,
            user_id=user_id,
            limite=limite
        )

        if not experiencias:
            return (
                "=== HISTÃ“RIA COMPARTILHADA V14 ===\n"
                "Nenhuma experiÃªncia anterior suficientemente "
                "relacionada foi encontrada.\n"
                "NÃ£o invente acontecimentos anteriores."
            )

        partes = [
            "=== HISTÃ“RIA COMPARTILHADA V14 ===",
            "ExperiÃªncias anteriores potencialmente relevantes:"
        ]

        for exp in experiencias:
            partes.append(
                f"""
EPISÃ“DIO #{exp['id']}
Projeto: {exp.get('projeto') or 'nÃ£o informado'}
SituaÃ§Ã£o: {exp.get('situacao') or ''}
DecisÃ£o: {exp.get('decisao') or ''}
Motivo: {exp.get('motivo') or ''}
Resultado: {exp.get('resultado') or ''}
ConsequÃªncia: {exp.get('consequencia') or ''}
Aprendizado: {exp.get('aprendizado') or ''}
AplicaÃ§Ã£o futura: {exp.get('aplicacao_futura') or ''}
"""
            )

        partes.append(
            "\nUse essas experiÃªncias apenas como contexto. "
            "NÃ£o presuma que uma situaÃ§Ã£o atual Ã© idÃªntica Ã  anterior."
        )

        return "\n".join(partes)
