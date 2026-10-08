from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


class MotorRaciocinioCausal:
    """
    V18 — Motor de Raciocínio Causal (MRC).

    Objetivo:
    - separar fatos, hipóteses e inferências;
    - registrar evidências a favor e contra;
    - considerar causas alternativas e variáveis de confusão;
    - produzir conclusão provisória sem transformar correlação em causalidade;
    - indicar o próximo teste/verificação útil.

    Este motor NÃO autoriza ações externas e NÃO substitui governança,
    Critic, V17 ou supervisão humana.
    """

    def __init__(self, db_path: str = "data/ashley_memoria.db"):
        self.db_path = db_path
        self._inicializar_banco()

    def _conectar(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_banco(self):
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_analises_causais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    problema TEXT NOT NULL,
                    hipotese_principal TEXT,
                    conclusao_provisoria TEXT,
                    confianca REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'EM_ANALISE',
                    proxima_verificacao TEXT,
                    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ashley_evidencias_causais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analise_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    peso REAL DEFAULT 0.5,
                    origem TEXT DEFAULT 'conversa',
                    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(analise_id) REFERENCES ashley_analises_causais(id)
                )
            """)
            conn.commit()

    @staticmethod
    def _limitar_confianca(valor: float) -> float:
        return max(0.0, min(1.0, float(valor)))

    def criar_analise(
        self,
        problema: str,
        hipotese_principal: str = "",
        user_id: Optional[int] = None,
    ) -> int:
        problema = (problema or "").strip()
        if not problema:
            raise ValueError("O problema causal não pode ser vazio.")

        with self._conectar() as conn:
            cur = conn.execute(
                """
                INSERT INTO ashley_analises_causais
                (user_id, problema, hipotese_principal)
                VALUES (?, ?, ?)
                """,
                (user_id, problema, (hipotese_principal or "").strip()),
            )
            conn.commit()
            return int(cur.lastrowid)

    def registrar_evidencia(
        self,
        analise_id: int,
        tipo: str,
        descricao: str,
        peso: float = 0.5,
        origem: str = "conversa",
    ) -> int:
        tipos_validos = {
            "FATO",
            "FAVORAVEL",
            "CONTRARIA",
            "ALTERNATIVA",
            "CONFUNDIDORA",
            "LACUNA",
        }
        tipo = (tipo or "").upper().strip()
        if tipo not in tipos_validos:
            raise ValueError(
                "tipo deve ser FATO, FAVORAVEL, CONTRARIA, ALTERNATIVA, "
                "CONFUNDIDORA ou LACUNA."
            )

        descricao = (descricao or "").strip()
        if not descricao:
            raise ValueError("A evidência não pode ser vazia.")

        peso = self._limitar_confianca(peso)

        with self._conectar() as conn:
            cur = conn.execute(
                """
                INSERT INTO ashley_evidencias_causais
                (analise_id, tipo, descricao, peso, origem)
                VALUES (?, ?, ?, ?, ?)
                """,
                (analise_id, tipo, descricao, peso, origem),
            )
            conn.commit()
            return int(cur.lastrowid)

    def obter_analise(self, analise_id: int) -> Optional[Dict[str, Any]]:
        with self._conectar() as conn:
            analise = conn.execute(
                "SELECT * FROM ashley_analises_causais WHERE id = ?",
                (analise_id,),
            ).fetchone()
            if not analise:
                return None

            evidencias = conn.execute(
                """
                SELECT * FROM ashley_evidencias_causais
                WHERE analise_id = ?
                ORDER BY id ASC
                """,
                (analise_id,),
            ).fetchall()

        resultado = dict(analise)
        resultado["evidencias"] = [dict(x) for x in evidencias]
        return resultado

    def avaliar_analise(self, analise_id: int) -> Dict[str, Any]:
        analise = self.obter_analise(analise_id)
        if not analise:
            raise ValueError("Análise causal não encontrada.")

        grupos: Dict[str, List[Dict[str, Any]]] = {
            "FATO": [],
            "FAVORAVEL": [],
            "CONTRARIA": [],
            "ALTERNATIVA": [],
            "CONFUNDIDORA": [],
            "LACUNA": [],
        }
        for ev in analise["evidencias"]:
            grupos.setdefault(ev["tipo"], []).append(ev)

        favor = sum(float(x["peso"]) for x in grupos["FAVORAVEL"])
        contra = sum(float(x["peso"]) for x in grupos["CONTRARIA"])
        alternativas = sum(float(x["peso"]) for x in grupos["ALTERNATIVA"])
        confundidoras = sum(float(x["peso"]) for x in grupos["CONFUNDIDORA"])
        fatos = sum(float(x["peso"]) for x in grupos["FATO"])

        # Heurística conservadora: evidência favorável aumenta confiança,
        # enquanto evidência contrária, alternativas e confundidores reduzem.
        bruto = (
            0.15
            + min(0.20, fatos * 0.08)
            + min(0.55, favor * 0.22)
            - min(0.45, contra * 0.22)
            - min(0.30, alternativas * 0.12)
            - min(0.30, confundidoras * 0.14)
        )
        confianca = round(self._limitar_confianca(bruto), 4)

        tem_hipotese = bool((analise.get("hipotese_principal") or "").strip())
        tem_favoravel = bool(grupos["FAVORAVEL"])
        tem_contraria_ou_alternativa = bool(
            grupos["CONTRARIA"] or grupos["ALTERNATIVA"] or grupos["CONFUNDIDORA"]
        )

        if not tem_hipotese:
            conclusao = (
                "Não há hipótese causal principal definida. "
                "É necessário formular uma hipótese testável."
            )
            status = "HIPOTESE_AUSENTE"
        elif not tem_favoravel:
            conclusao = (
                "A hipótese existe, mas ainda não há evidência favorável suficiente "
                "para sustentar uma relação causal."
            )
            status = "EVIDENCIA_INSUFICIENTE"
        elif confianca >= 0.75 and not tem_contraria_ou_alternativa:
            conclusao = (
                "Há evidência consistente com a hipótese, mas a causalidade permanece "
                "provisória até que explicações alternativas e confundidores sejam testados."
            )
            status = "HIPOTESE_FORTALECIDA"
        elif confianca >= 0.45:
            conclusao = (
                "A hipótese é plausível, porém as evidências ainda permitem explicações "
                "alternativas. Não tratar correlação como causalidade comprovada."
            )
            status = "HIPOTESE_PLAUSIVEL"
        else:
            conclusao = (
                "A hipótese causal permanece fraca ou contestada. "
                "Não há base suficiente para afirmar causalidade."
            )
            status = "HIPOTESE_FRACA"

        if grupos["LACUNA"]:
            proxima = grupos["LACUNA"][0]["descricao"]
        elif grupos["CONFUNDIDORA"]:
            proxima = (
                "Testar a variável de confusão: "
                + grupos["CONFUNDIDORA"][0]["descricao"]
            )
        elif grupos["ALTERNATIVA"]:
            proxima = (
                "Comparar a hipótese principal com a explicação alternativa: "
                + grupos["ALTERNATIVA"][0]["descricao"]
            )
        else:
            proxima = (
                "Buscar uma observação ou teste que possa diferenciar causalidade "
                "de mera correlação."
            )

        agora = datetime.now().isoformat()
        with self._conectar() as conn:
            conn.execute(
                """
                UPDATE ashley_analises_causais
                SET conclusao_provisoria = ?,
                    confianca = ?,
                    status = ?,
                    proxima_verificacao = ?,
                    atualizado_em = ?
                WHERE id = ?
                """,
                (conclusao, confianca, status, proxima, agora, analise_id),
            )
            conn.commit()

        return {
            "v18_ativo": True,
            "analise_id": analise_id,
            "problema": analise["problema"],
            "hipotese_principal": analise["hipotese_principal"],
            "fatos": [x["descricao"] for x in grupos["FATO"]],
            "evidencias_favoraveis": [x["descricao"] for x in grupos["FAVORAVEL"]],
            "evidencias_contrarias": [x["descricao"] for x in grupos["CONTRARIA"]],
            "causas_alternativas": [x["descricao"] for x in grupos["ALTERNATIVA"]],
            "variaveis_confusao": [x["descricao"] for x in grupos["CONFUNDIDORA"]],
            "lacunas": [x["descricao"] for x in grupos["LACUNA"]],
            "confianca_causal": confianca,
            "status": status,
            "conclusao_provisoria": conclusao,
            "proxima_verificacao": proxima,
            "regra": (
                "Conclusão causal é provisória. Correlação, sequência temporal "
                "ou plausibilidade isoladas não provam causalidade."
            ),
            "governanca": (
                "O V18 fornece análise e próximos testes; não autoriza ações "
                "externas ou de alto impacto."
            ),
        }

    def analisar_estrutura(
        self,
        problema: str,
        hipotese_principal: str,
        fatos: Optional[List[str]] = None,
        evidencias_favoraveis: Optional[List[str]] = None,
        evidencias_contrarias: Optional[List[str]] = None,
        causas_alternativas: Optional[List[str]] = None,
        variaveis_confusao: Optional[List[str]] = None,
        lacunas: Optional[List[str]] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Atalho determinístico para testes e integração futura com o Hub.
        Persiste a análise e retorna a avaliação V18.
        """
        analise_id = self.criar_analise(
            problema=problema,
            hipotese_principal=hipotese_principal,
            user_id=user_id,
        )

        colecoes = (
            ("FATO", fatos or []),
            ("FAVORAVEL", evidencias_favoraveis or []),
            ("CONTRARIA", evidencias_contrarias or []),
            ("ALTERNATIVA", causas_alternativas or []),
            ("CONFUNDIDORA", variaveis_confusao or []),
            ("LACUNA", lacunas or []),
        )
        for tipo, itens in colecoes:
            for item in itens:
                self.registrar_evidencia(
                    analise_id=analise_id,
                    tipo=tipo,
                    descricao=item,
                    peso=0.7,
                    origem="estrutura_v18",
                )

        return self.avaliar_analise(analise_id)
