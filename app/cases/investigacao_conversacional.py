import re
import sqlite3
from datetime import datetime, timezone


class InvestigacaoConversacional:
    """
    V7: acompanha respostas naturais do usuário dentro de um caso aberto.

    A camada é deliberadamente conservadora:
    - não inventa fatos;
    - registra a resposta como evidência relatada;
    - identifica alguns campos investigativos por sinais linguísticos;
    - mantém uma fila de perguntas ainda não respondidas;
    - não declara causa comprovada automaticamente.
    """

    CAMPOS = (
        "resultado_desejado",
        "inicio_problema",
        "mudanca_anterior",
        "tentativas_anteriores",
        "dados_objetivos",
    )

    PERGUNTAS = {
        "resultado_desejado": (
            "Qual resultado concreto mostraria para você que esse problema foi resolvido?"
        ),
        "inicio_problema": (
            "Quando esse problema começou, aproximadamente?"
        ),
        "mudanca_anterior": (
            "O que mudou pouco antes de o problema começar?"
        ),
        "tentativas_anteriores": (
            "O que vocês já tentaram fazer para resolver isso e o que aconteceu?"
        ),
        "dados_objetivos": (
            "Que dados objetivos temos para medir o problema e comparar antes e depois?"
        ),
    }

    def __init__(self, db_path):
        self.db_path = str(db_path)
        self._inicializar()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _agora(self):
        return datetime.now(timezone.utc).isoformat()

    def _inicializar(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS caso_investigacao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    campo TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    confianca REAL NOT NULL DEFAULT 0.70,
                    origem TEXT NOT NULL DEFAULT 'conversa',
                    criado_em TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL,
                    UNIQUE(caso_id, user_id, campo)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_investigacao_caso
                ON caso_investigacao(caso_id, user_id)
            """)
            conn.commit()

    def registrar(self, caso_id, user_id, campo, valor, confianca=0.70):
        if campo not in self.CAMPOS:
            raise ValueError(f"Campo investigativo inválido: {campo}")
        valor = re.sub(r"\s+", " ", str(valor or "")).strip()
        if not valor:
            return False

        agora = self._agora()
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO caso_investigacao
                (caso_id, user_id, campo, valor, confianca, origem, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, 'conversa', ?, ?)
                ON CONFLICT(caso_id, user_id, campo)
                DO UPDATE SET
                    valor=excluded.valor,
                    confianca=excluded.confianca,
                    atualizado_em=excluded.atualizado_em
            """, (
                int(caso_id), int(user_id), campo, valor,
                float(confianca), agora, agora
            ))
            conn.commit()
        return True

    def contexto(self, caso_id, user_id):
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT campo, valor, confianca, atualizado_em
                FROM caso_investigacao
                WHERE caso_id=? AND user_id=?
                ORDER BY id
            """, (int(caso_id), int(user_id))).fetchall()

        respondidos = {r["campo"]: dict(r) for r in rows}
        faltantes = [c for c in self.CAMPOS if c not in respondidos]
        proximo = faltantes[0] if faltantes else None

        return {
            "respondidos": respondidos,
            "faltantes": faltantes,
            "proximo_campo": proximo,
            "proxima_pergunta": self.PERGUNTAS.get(proximo) if proximo else None
        }

    def extrair_sinais(self, mensagem):
        """
        Extração determinística inicial. Não pretende compreender tudo.
        O modelo recebe o contexto para complementar a conversa, mas somente
        sinais suficientemente claros são persistidos automaticamente aqui.
        """
        original = re.sub(r"\s+", " ", (mensagem or "")).strip()
        texto = original.lower()
        achados = {}

        sinais_inicio = (
            "começou", "comecou", "há ", "ha ", "desde ", "faz ",
            "meses", "semanas", "dias", "anos"
        )
        sinais_mudanca = (
            "depois que", "depois de", "mudou", "mudamos", "aumentamos",
            "reduzimos", "trocamos", "implantamos", "implementamos",
            "contratamos", "demitimos", "lançamos", "lancamos"
        )
        sinais_tentativa = (
            "tentamos", "tentei", "já fiz", "ja fiz", "fizemos",
            "testamos", "mudamos para", "tentativa"
        )
        sinais_objetivo = (
            "quero que", "preciso que", "objetivo é", "objetivo e",
            "considero resolvido", "estará resolvido", "estara resolvido"
        )
        sinais_dados = (
            "%", "por cento", "clientes", "vendas", "faturamento",
            "taxa", "número", "numero", "métrica", "metrica"
        )

        if any(s in texto for s in sinais_inicio):
            achados["inicio_problema"] = original
        if any(s in texto for s in sinais_mudanca):
            achados["mudanca_anterior"] = original
        if any(s in texto for s in sinais_tentativa):
            achados["tentativas_anteriores"] = original
        if any(s in texto for s in sinais_objetivo):
            achados["resultado_desejado"] = original
        if any(s in texto for s in sinais_dados) and any(ch.isdigit() for ch in texto):
            achados["dados_objetivos"] = original

        return achados
