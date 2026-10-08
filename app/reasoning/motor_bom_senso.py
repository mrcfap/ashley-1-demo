from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional


class MotorBomSensoCoerenciaMundo:
    """
    Ashley V19 — Motor de Bom Senso e Coerência do Mundo (MBCM).

    Objetivo:
    avaliar se uma ação, hipótese ou descrição é coerente com propriedades
    básicas do mundo, sem transformar plausibilidade em certeza e sem usar
    a avaliação como autorização para ações externas.

    Primeira versão:
    - local e determinística;
    - sem dependência obrigatória de API externa;
    - persistência SQLite;
    - separa fatos fornecidos, conhecimento local, inferências e incertezas;
    - preparada para fontes externas opcionais (ex.: ConceptNet) no futuro.
    """

    VERSAO = "V19.1"

    STATUS = {
        "COERENTE",
        "POSSIVEL_COM_RESTRICOES",
        "INCERTO",
        "INCOMPATIVEL",
        "PERIGOSO",
    }

    def __init__(self, db_path: str = "data/ashley_memoria.db"):
        self.db_path = db_path
        self._inicializar_banco()

        # Base pequena e explícita para o MVP. Não pretende representar
        # conhecimento universal; apenas permite validar o mecanismo.
        self._conhecimento_local = {
            "vidro": {
                "propriedades": ["frágil", "pode quebrar sob impacto"],
                "riscos": ["fragmentos cortantes quando quebrado"],
            },
            "copo": {
                "propriedades": ["recipiente", "pode conter líquidos"],
                "usos": ["conter água e outras bebidas"],
            },
            "fogo": {
                "propriedades": ["produz calor", "pode causar queimaduras"],
                "riscos": ["pode incendiar materiais combustíveis"],
            },
            "agua": {
                "propriedades": ["líquido", "molha superfícies"],
                "riscos": ["pode danificar equipamentos elétricos energizados"],
            },
            "eletricidade": {
                "propriedades": ["pode energizar equipamentos"],
                "riscos": ["pode causar choque elétrico"],
            },
        }

    # --------------------------------------------------
    # Persistência
    # --------------------------------------------------

    def _conectar(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_banco(self):
        with self._conectar() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ashley_avaliacoes_bom_senso (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    objeto TEXT,
                    acao TEXT NOT NULL,
                    contexto TEXT,
                    status TEXT NOT NULL,
                    confianca REAL NOT NULL,
                    justificativa TEXT,
                    conhecimento_json TEXT,
                    inferencias_json TEXT,
                    incertezas_json TEXT,
                    criado_em TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # --------------------------------------------------
    # Utilidades
    # --------------------------------------------------

    @staticmethod
    def _normalizar(texto: Optional[str]) -> str:
        texto = str(texto or "").lower().strip()
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = re.sub(r"\s+", " ", texto)
        return texto

    @staticmethod
    def _limitar_confianca(valor: float) -> float:
        return round(max(0.0, min(1.0, float(valor))), 3)

    def consultar_conhecimento_local(
        self,
        objeto: str,
        contexto: str = "",
    ) -> Dict[str, Any]:
        texto = self._normalizar(f"{objeto} {contexto}")
        encontrados: List[Dict[str, Any]] = []

        for conceito, dados in self._conhecimento_local.items():
            if conceito in texto:
                encontrados.append(
                    {
                        "conceito": conceito,
                        "origem": "base_local_v19",
                        "propriedades": list(dados.get("propriedades", [])),
                        "usos": list(dados.get("usos", [])),
                        "riscos": list(dados.get("riscos", [])),
                    }
                )

        return {
            "encontrado": bool(encontrados),
            "itens": encontrados,
            "regra": (
                "Conhecimento recuperado é contexto de apoio; "
                "não é prova automática sobre o caso concreto."
            ),
        }

    # --------------------------------------------------
    # Avaliação
    # --------------------------------------------------

    def avaliar_acao(
        self,
        objeto: str,
        acao: str,
        contexto: str = "",
        fatos: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        persistir: bool = True,
    ) -> Dict[str, Any]:
        fatos = [str(x) for x in (fatos or []) if str(x).strip()]
        objeto_n = self._normalizar(objeto)
        acao_n = self._normalizar(acao)
        contexto_n = self._normalizar(contexto)

        conhecimento = self.consultar_conhecimento_local(objeto, contexto)
        itens = conhecimento["itens"]

        propriedades = []
        usos = []
        riscos = []
        for item in itens:
            propriedades.extend(item.get("propriedades", []))
            usos.extend(item.get("usos", []))
            riscos.extend(item.get("riscos", []))

        inferencias: List[str] = []
        incertezas: List[str] = []
        restricoes: List[str] = []
        sinais_perigo = 0
        sinais_incompatibilidade = 0
        sinais_coerencia = 0

        texto_mundo = self._normalizar(
            " ".join(propriedades + usos + riscos + fatos + [contexto])
        )

        # Regras determinísticas pequenas e auditáveis.
        impacto = any(
            termo in acao_n
            for termo in [
                "jogar no chao", "arremessar", "bater", "derrubar",
                "quebrar", "golpear",
            ]
        )
        fragil = any(
            termo in texto_mundo
            for termo in ["fragil", "pode quebrar", "quebravel"]
        )
        cortante = any(
            termo in texto_mundo
            for termo in ["cortante", "fragmentos"]
        )

        if impacto and fragil:
            sinais_perigo += 2
            restricoes.append("Evitar impacto em objeto identificado como frágil.")
            inferencias.append(
                "Impacto sobre material frágil torna quebra uma consequência plausível."
            )

        if impacto and cortante:
            sinais_perigo += 2
            inferencias.append(
                "Se houver quebra, fragmentos podem introduzir risco físico."
            )

        colocar_liquido = any(
            termo in acao_n
            for termo in ["colocar agua", "colocar líquido", "colocar liquido",
                           "encher", "servir agua", "servir líquido", "servir liquido"]
        )
        recipiente = any(
            termo in texto_mundo for termo in ["recipiente", "conter liquidos"]
        )
        if colocar_liquido and recipiente:
            sinais_coerencia += 2
            inferencias.append(
                "Usar um recipiente para conter líquido é compatível com sua função conhecida."
            )

        fogo = "fogo" in objeto_n or "fogo" in contexto_n or "fogo" in acao_n
        tocar = any(t in acao_n for t in ["tocar", "encostar", "segurar com a mao"])
        queimadura = "queimadura" in texto_mundo or "produz calor" in texto_mundo
        if fogo and tocar and queimadura:
            sinais_perigo += 3
            restricoes.append("Evitar contato corporal direto com fonte de calor.")
            inferencias.append(
                "Contato direto com fonte de calor pode causar dano físico."
            )

        # Riscos condicionais só são ativados quando as pré-condições
        # aparecem no caso concreto. Um risco armazenado na memória não
        # deve, sozinho, criar a condição que o ativa.
        texto_caso = self._normalizar(
            " ".join([objeto, acao, contexto] + fatos)
        )
        equipamento_eletrico_no_caso = any(
            t in texto_caso
            for t in [
                "equipamento eletrico", "aparelho eletrico", "tomada",
                "fio eletrico", "cabo eletrico", "computador", "notebook",
                "televisao", "tv", "eletrodomestico",
            ]
        )
        energizado_no_caso = any(
            t in texto_caso
            for t in [
                "energizado", "ligado", "na tomada", "corrente eletrica",
                "com energia",
            ]
        )
        molhar = any(
            t in acao_n
            for t in ["molhar", "jogar agua", "colocar agua", "derramar agua"]
        )

        if equipamento_eletrico_no_caso and energizado_no_caso and molhar:
            sinais_perigo += 3
            restricoes.append(
                "Não aplicar líquido a equipamento energizado sem verificar segurança."
            )
            inferencias.append(
                "No caso concreto há líquido, equipamento elétrico e indicação de energização; "
                "essa combinação torna o risco elétrico relevante."
            )

        impossibilidade = any(
            t in acao_n
            for t in [
                "atravessar parede solida sem abrir",
                "estar em dois lugares ao mesmo tempo",
            ]
        )
        if impossibilidade:
            sinais_incompatibilidade += 3
            inferencias.append(
                "A ação descrita conflita com restrições físicas básicas representadas pelo V19."
            )

        if not conhecimento["encontrado"]:
            incertezas.append(
                "A base local V19 não possui conhecimento suficiente sobre o objeto/contexto."
            )

        if sinais_perigo >= 3:
            status = "PERIGOSO"
            confianca = 0.82 + min(0.12, 0.03 * sinais_perigo)
            justificativa = (
                "Há sinais convergentes de risco físico. A avaliação recomenda "
                "não tratar a ação como segura sem mitigação adequada."
            )
        elif sinais_incompatibilidade >= 3:
            status = "INCOMPATIVEL"
            confianca = 0.88
            justificativa = (
                "A ação conflita com restrições básicas representadas pelo motor."
            )
        elif sinais_perigo > 0:
            status = "POSSIVEL_COM_RESTRICOES"
            confianca = 0.68
            justificativa = (
                "A ação pode ser fisicamente possível, mas há restrições ou riscos relevantes."
            )
        elif sinais_coerencia >= 2:
            status = "COERENTE"
            confianca = 0.80
            justificativa = (
                "A ação é compatível com propriedades ou usos conhecidos do objeto."
            )
        else:
            status = "INCERTO"
            confianca = 0.35 if conhecimento["encontrado"] else 0.20
            justificativa = (
                "Não há evidência suficiente para classificar a ação como coerente, "
                "incompatível ou perigosa."
            )
            incertezas.append(
                "Ausência de conflito detectado não equivale a confirmação de segurança."
            )

        confianca = self._limitar_confianca(confianca)

        resultado = {
            "v19_ativo": True,
            "versao": self.VERSAO,
            "objeto": objeto,
            "acao": acao,
            "contexto": contexto,
            "fatos_fornecidos": fatos,
            "conhecimento_recuperado": conhecimento,
            "inferencias": inferencias,
            "restricoes": restricoes,
            "incertezas": list(dict.fromkeys(incertezas)),
            "status": status,
            "confianca": confianca,
            "justificativa": justificativa,
            "regra": (
                "Bom senso é uma avaliação de coerência e plausibilidade, não uma "
                "prova universal nem uma autorização de execução."
            ),
            "governanca": (
                "O V19 não autoriza ações externas, destrutivas, financeiras, "
                "de segurança ou de alto impacto."
            ),
        }

        if persistir:
            resultado["avaliacao_id"] = self._persistir_avaliacao(
                user_id=user_id,
                resultado=resultado,
            )

        return resultado

    def _persistir_avaliacao(
        self,
        user_id: Optional[int],
        resultado: Dict[str, Any],
    ) -> int:
        agora = datetime.now().isoformat()
        with self._conectar() as conn:
            cur = conn.execute(
                """
                INSERT INTO ashley_avaliacoes_bom_senso (
                    user_id, objeto, acao, contexto, status, confianca,
                    justificativa, conhecimento_json, inferencias_json,
                    incertezas_json, criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    resultado.get("objeto"),
                    resultado.get("acao"),
                    resultado.get("contexto"),
                    resultado.get("status"),
                    resultado.get("confianca"),
                    resultado.get("justificativa"),
                    json.dumps(
                        resultado.get("conhecimento_recuperado"),
                        ensure_ascii=False,
                    ),
                    json.dumps(resultado.get("inferencias"), ensure_ascii=False),
                    json.dumps(resultado.get("incertezas"), ensure_ascii=False),
                    agora,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def obter_avaliacao(self, avaliacao_id: int) -> Optional[Dict[str, Any]]:
        with self._conectar() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM ashley_avaliacoes_bom_senso
                WHERE id = ?
                """,
                (int(avaliacao_id),),
            ).fetchone()

        if not row:
            return None

        item = dict(row)
        for campo in ["conhecimento_json", "inferencias_json", "incertezas_json"]:
            try:
                item[campo] = json.loads(item[campo] or "null")
            except json.JSONDecodeError:
                pass
        return item

    def estado_v19(self) -> Dict[str, Any]:
        return {
            "motor": "Motor de Bom Senso e Coerência do Mundo",
            "versao": self.VERSAO,
            "ativo": True,
            "modo": "local_deterministico",
            "fonte_externa_obrigatoria": False,
            "status_possiveis": sorted(self.STATUS),
            "principios": [
                "não confundir ausência de conflito com segurança",
                "separar conhecimento recuperado de inferência",
                "expressar incerteza quando faltar conhecimento",
                "não transformar plausibilidade em fato",
                "preservar governança para ações reais",
            ],
        }


# Alias curto para facilitar integração no Cognitive Hub.
MotorBomSenso = MotorBomSensoCoerenciaMundo
