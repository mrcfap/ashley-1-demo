from datetime import datetime
from typing import Any, Dict, Optional


class AshleyCognitiveHub:
    """
    Ashley Cognitive Hub

    Camada de consolidação cognitiva da Ashley.

    Responsabilidades:
    - coordenar os motores cognitivos existentes;
    - decidir quais motores são relevantes para cada interação;
    - reduzir redundância de contexto;
    - fornecer observabilidade do estado cognitivo;
    - preservar a governança e a autorização humana.

    O Hub NÃO substitui os motores V12, V13, V14, V15, V17, V18, V19, V20 ou V21.\n    O V17 reutiliza o motor V12 para transformar decisões e consequências\n    em experiência operacional, sem criar um motor paralelo.\n    Ele coordena esses componentes.
    """

    def __init__(
        self,
        continuidade=None,
        mrac=None,
        fpa=None,
        historia=None,
        raciocinio_causal=None,
        bom_senso=None,
        criatividade=None,
        diretor_adaptativo=None,
    ):
        self.continuidade = continuidade
        self.mrac = mrac
        self.fpa = fpa
        self.historia = historia
        self.raciocinio_causal = raciocinio_causal
        self.bom_senso = bom_senso
        self.criatividade = criatividade
        self.diretor_adaptativo = diretor_adaptativo

        self.versao = "1.4-V21"
        self.ativo = True

    # ==========================================================
    # DISPONIBILIDADE DOS MOTORES
    # ==========================================================

    def motores_disponiveis(self) -> Dict[str, bool]:
        return {
            "v12_continuidade": self.continuidade is not None,
            "v13_mrac": self.mrac is not None,
            "v14_fpa": self.fpa is not None,
            "v15_historia": self.historia is not None,
            "v17_experiencia_decisao": (
                self.continuidade is not None
                and hasattr(self.continuidade, "orientar_por_experiencia")
            ),
            "v18_raciocinio_causal": (
                self.raciocinio_causal is not None
                and hasattr(self.raciocinio_causal, "analisar_estrutura")
            ),
            "v19_bom_senso": (
                self.bom_senso is not None
                and hasattr(self.bom_senso, "avaliar_acao")
            ),
            "v20_criatividade_disruptiva": (
                self.criatividade is not None
                and hasattr(self.criatividade, "executar")
            ),
            "v21_diretor_adaptativo_consequencia": (
                self.diretor_adaptativo is not None
                and hasattr(self.diretor_adaptativo, "planejar")
                and hasattr(self.diretor_adaptativo, "analisar_consequencia")
            ),
        }

    # ==========================================================
    # ROTEAMENTO COGNITIVO
    # ==========================================================

    def selecionar_motores(
        self,
        mensagem: str,
        complexidade: str = "baixa",
    ) -> Dict[str, Any]:

        texto = (mensagem or "").lower()

        motores = {
            "continuidade": False,
            "mrac": False,
            "fpa": True,
            "historia": False,
            "v17_experiencia": False,
            "v18_causal": False,
            "v19_bom_senso": False,
            "v20_criatividade": False,
            "v21_diretor_adaptativo": False,
        }

        motivos = []

        # V12 — Continuidade Cognitiva
        gatilhos_continuidade = (
            "projeto",
            "objetivo",
            "continuar",
            "continuidade",
            "próximo passo",
            "proximo passo",
            "onde paramos",
            "pendência",
            "pendencia",
            "tarefa",
        )

        if any(g in texto for g in gatilhos_continuidade):
            motores["continuidade"] = True
            motivos.append("A interação envolve objetivo, tarefa ou continuidade.")

        # V13 — MRAC
        gatilhos_risco = (
            "risco",
            "problema",
            "erro",
            "falha",
            "perigo",
            "segurança",
            "seguranca",
            "autonomia",
            "decisão",
            "decisao",
            "alerta",
        )

        if any(g in texto for g in gatilhos_risco):
            motores["mrac"] = True
            motivos.append("A interação possui sinais de risco, decisão ou governança.")

        # V15 — História Compartilhada
        gatilhos_historia = (
            "antes",
            "anterior",
            "histórico",
            "historico",
            "experiência",
            "experiencia",
            "aprendemos",
            "decidimos",
            "já fizemos",
            "ja fizemos",
            "memória",
            "memoria",
            "continuidade",
        )

        if any(g in texto for g in gatilhos_historia):
            motores["historia"] = True
            motivos.append("Experiências anteriores podem contribuir para a resposta.")

        # V17 — Experiência, Decisão e Consequência
        # O V17 vive dentro do V12 e reutiliza o histórico real de decisões.
        gatilhos_experiencia_decisao = (
            "decisão",
            "decisao",
            "decidir",
            "escolher",
            "estratégia",
            "estrategia",
            "alternativa",
            "consequência",
            "consequencia",
            "resultado",
            "funcionou",
            "não funcionou",
            "nao funcionou",
            "aprendizado",
            "aprendemos",
            "experiência",
            "experiencia",
            "fizemos antes",
            "já fizemos",
            "ja fizemos",
            "melhor caminho",
            "o que fazer",
        )

        v17_disponivel = (
            self.continuidade is not None
            and hasattr(self.continuidade, "orientar_por_experiencia")
        )
        if v17_disponivel and any(
            g in texto for g in gatilhos_experiencia_decisao
        ):
            motores["v17_experiencia"] = True
            motores["continuidade"] = True
            motivos.append(
                "V17: experiências anteriores podem orientar a decisão atual."
            )

        # V18 — Raciocínio Causal
        # Ativa análise causal quando a interação busca explicar por que algo
        # aconteceu, testar uma causa ou distinguir correlação de causalidade.
        gatilhos_causais = (
            "causa",
            "causou",
            "causar",
            "causal",
            "causalidade",
            "por que aconteceu",
            "porque aconteceu",
            "motivo da falha",
            "origem do problema",
            "razão do problema",
            "razao do problema",
            "devido a",
            "provocou",
            "correlação",
            "correlacao",
            "explicação alternativa",
            "explicacao alternativa",
            "variável de confusão",
            "variavel de confusao",
            "hipótese",
            "hipotese",
        )

        v18_disponivel = (
            self.raciocinio_causal is not None
            and hasattr(self.raciocinio_causal, "analisar_estrutura")
        )
        if v18_disponivel and any(g in texto for g in gatilhos_causais):
            motores["v18_causal"] = True
            motivos.append(
                "V18: a interação exige análise de hipótese, evidência e causalidade."
            )

        # V19 — Bom Senso e Coerência do Mundo
        # Ativa quando a interação pede avaliação de plausibilidade prática,
        # compatibilidade física, risco contextual ou uso coerente de objetos.
        gatilhos_bom_senso = (
            "faz sentido",
            "é seguro",
            "e seguro",
            "é perigoso",
            "e perigoso",
            "pode quebrar",
            "pode queimar",
            "pode machucar",
            "jogar no chão",
            "jogar no chao",
            "jogar água",
            "jogar agua",
            "molhar",
            "frágil",
            "fragil",
            "vidro",
            "fogo",
            "tomada",
            "equipamento elétrico",
            "equipamento eletrico",
            "notebook ligado",
            "mundo real",
            "bom senso",
            "coerente",
            "incompatível",
            "incompativel",
        )

        v19_disponivel = (
            self.bom_senso is not None
            and hasattr(self.bom_senso, "avaliar_acao")
        )
        if v19_disponivel and any(g in texto for g in gatilhos_bom_senso):
            motores["v19_bom_senso"] = True
            motivos.append(
                "V19: a interação exige avaliação de bom senso, coerência ou risco contextual."
            )

        # V20 — Criatividade Disruptiva e Pensamento Lateral
        # Ativa quando a interação pede inovação, alternativas não convencionais,
        # ruptura de premissas ou exploração criativa estruturada.
        gatilhos_criatividade = (
            "criatividade",
            "criativo",
            "criativa",
            "inovação",
            "inovacao",
            "inovador",
            "inovadora",
            "disruptivo",
            "disruptiva",
            "pensamento lateral",
            "fora da caixa",
            "ideia diferente",
            "ideias diferentes",
            "nova abordagem",
            "abordagem diferente",
            "alternativa incomum",
            "alternativas incomuns",
            "quebrar premissa",
            "quebrar premissas",
            "romper premissa",
            "romper premissas",
            "reinventar",
            "diferencial",
            "diferente das",
        )

        v20_disponivel = (
            self.criatividade is not None
            and hasattr(self.criatividade, "executar")
        )
        if v20_disponivel and any(g in texto for g in gatilhos_criatividade):
            motores["v20_criatividade"] = True
            motivos.append(
                "V20: a interação pede exploração criativa, ruptura de premissas "
                "ou geração de alternativas não convencionais."
            )

        # V21 — Diretor Cognitivo Adaptativo por Consequência
        # Ativa para objetivos complexos que exigem decomposição adaptativa,
        # especialistas temporários, coordenação de dependências ou aprendizagem
        # explícita pela comparação entre resultado esperado e observado.
        gatilhos_v21 = (
            "objetivo complexo",
            "problema complexo",
            "decompor",
            "decomposição",
            "decomposicao",
            "dividir em etapas",
            "especialistas",
            "especialista temporário",
            "especialista temporario",
            "multiagente",
            "multi-agente",
            "coordenar agentes",
            "planejamento adaptativo",
            "diretor cognitivo",
            "resultado esperado",
            "resultado observado",
            "aprender com o resultado",
            "aprender com a consequência",
            "aprender com a consequencia",
            "consequência observada",
            "consequencia observada",
            "previsto",
            "ocorrido",
        )

        v21_disponivel = (
            self.diretor_adaptativo is not None
            and hasattr(self.diretor_adaptativo, "planejar")
            and hasattr(self.diretor_adaptativo, "analisar_consequencia")
        )

        if v21_disponivel and (
            complexidade == "alta"
            or any(g in texto for g in gatilhos_v21)
        ):
            motores["v21_diretor_adaptativo"] = True
            motores["continuidade"] = True
            motivos.append(
                "V21: a interação exige planejamento adaptativo, coordenação "
                "de especialistas ou aprendizagem por consequência."
            )

        # Complexidade alta amplia a observação,
        # mas não força todos os motores indiscriminadamente.
        if complexidade == "alta":
            motores["continuidade"] = True
            motores["mrac"] = True
            motivos.append("Complexidade alta exige maior supervisão cognitiva.")

        return {
            "motores": motores,
            "motivos": motivos,
        }

    def contexto_experiencia_v17(
        self,
        mensagem: str,
        objetivo_id: Optional[int] = None,
        limite: int = 5,
    ) -> Dict[str, Any]:
        """
        Recupera orientação V17 usando o mesmo MotorContinuidadeCognitiva.

        Este método não executa ações e não altera a governança.
        Apenas fornece experiência anterior como contexto cognitivo.
        """
        if (
            self.continuidade is None
            or not hasattr(self.continuidade, "orientar_por_experiencia")
        ):
            return {
                "v17_ativo": False,
                "ha_experiencia_relevante": False,
                "motivo": "Motor V17 indisponível.",
            }

        return self.continuidade.orientar_por_experiencia(
            contexto_atual=mensagem,
            objetivo_id=objetivo_id,
            limite=limite,
        )

    def contexto_causal_v18(
        self,
        problema: str,
        hipotese_principal: str,
        fatos=None,
        evidencias_favoraveis=None,
        evidencias_contrarias=None,
        causas_alternativas=None,
        variaveis_confusao=None,
        lacunas=None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executa o V18 de forma estruturada.

        O resultado é contexto analítico: não autoriza ações externas,
        não substitui governança e não transforma hipótese em fato.
        """
        if (
            self.raciocinio_causal is None
            or not hasattr(self.raciocinio_causal, "analisar_estrutura")
        ):
            return {
                "v18_ativo": False,
                "motivo": "Motor V18 indisponível.",
            }

        return self.raciocinio_causal.analisar_estrutura(
            problema=problema,
            hipotese_principal=hipotese_principal,
            fatos=fatos,
            evidencias_favoraveis=evidencias_favoraveis,
            evidencias_contrarias=evidencias_contrarias,
            causas_alternativas=causas_alternativas,
            variaveis_confusao=variaveis_confusao,
            lacunas=lacunas,
            user_id=user_id,
        )

    def contexto_bom_senso_v19(
        self,
        objeto: str,
        acao: str,
        contexto: str = "",
        fatos=None,
        user_id: Optional[int] = None,
        persistir: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa o V19 de forma estruturada.

        O V19 avalia coerência, plausibilidade e risco contextual.
        A avaliação não equivale a autorização de execução.
        """
        if (
            self.bom_senso is None
            or not hasattr(self.bom_senso, "avaliar_acao")
        ):
            return {
                "v19_ativo": False,
                "motivo": "Motor V19 indisponível.",
            }

        return self.bom_senso.avaliar_acao(
            objeto=objeto,
            acao=acao,
            contexto=contexto,
            fatos=fatos,
            user_id=user_id,
            persistir=persistir,
        )

    async def contexto_criatividade_v20(
        self,
        problema: str,
    ) -> Dict[str, Any]:
        """
        Executa o V20 de forma estruturada.

        O V20 gera hipóteses e alternativas criativas. Seu resultado é
        exploratório: não autoriza ações externas e deve passar pelos motores
        de validação, causalidade, bom senso e governança quando aplicável.
        """
        if (
            self.criatividade is None
            or not hasattr(self.criatividade, "executar")
        ):
            return {
                "v20_ativo": False,
                "motivo": "Motor V20 indisponível.",
            }

        try:
            resultado = await self.criatividade.executar(problema)
        except Exception as exc:
            return {
                "v20_ativo": False,
                "motivo": "Falha ao executar o Motor V20.",
                "erro": f"{type(exc).__name__}: {exc}",
            }

        return {
            "v20_ativo": True,
            "resultado": resultado,
        }

    async def contexto_diretor_v21(
        self,
        objetivo: str,
        contexto: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Solicita ao V21 um plano adaptativo.

        O resultado é um plano cognitivo. Ele não concede permissões,
        não autoriza ações externas e não altera o próprio código.
        """
        if (
            self.diretor_adaptativo is None
            or not hasattr(self.diretor_adaptativo, "planejar")
        ):
            return {
                "v21_ativo": False,
                "motivo": "Motor V21 indisponível.",
            }

        try:
            return await self.diretor_adaptativo.planejar(
                objetivo=objetivo,
                contexto=contexto,
            )
        except Exception as exc:
            return {
                "v21_ativo": False,
                "motivo": "Falha ao executar o planejamento do Motor V21.",
                "erro": f"{type(exc).__name__}: {exc}",
            }

    async def contexto_consequencia_v21(
        self,
        ciclo_id: str,
        resultado_observado: Any,
        efeitos_inesperados: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Fecha o ciclo de aprendizagem do V21 comparando expectativa e realidade.
        """
        if (
            self.diretor_adaptativo is None
            or not hasattr(self.diretor_adaptativo, "analisar_consequencia")
        ):
            return {
                "v21_ativo": False,
                "motivo": "Motor V21 indisponível.",
            }

        try:
            return await self.diretor_adaptativo.analisar_consequencia(
                ciclo_id=ciclo_id,
                resultado_observado=resultado_observado,
                efeitos_inesperados=efeitos_inesperados,
            )
        except Exception as exc:
            return {
                "v21_ativo": False,
                "motivo": "Falha ao analisar consequência no Motor V21.",
                "erro": f"{type(exc).__name__}: {exc}",
            }


    # ==========================================================
    # GOVERNANÇA
    # ==========================================================

    def classificar_governanca(self, acao: Optional[str]) -> Dict[str, Any]:

        texto = (acao or "").lower()

        alto_impacto = (
            "deletar",
            "apagar",
            "excluir",
            "pagamento",
            "comprar",
            "vender",
            "transferir",
            "senha",
            "permissão",
            "permissao",
            "segurança",
            "seguranca",
            "produção",
            "producao",
            "deploy",
        )

        if any(g in texto for g in alto_impacto):
            return {
                "nivel": "alto",
                "autorizacao_humana": True,
                "motivo": "A ação pode produzir impacto relevante ou irreversível.",
            }

        return {
            "nivel": "baixo",
            "autorizacao_humana": False,
            "motivo": "Nenhum indicador de alto impacto foi detectado.",
        }

    # ==========================================================
    # OBSERVABILIDADE
    # ==========================================================

    def estado_hub(self) -> Dict[str, Any]:

        return {
            "sistema": "Ashley Cognitive Hub",
            "versao": self.versao,
            "ativo": self.ativo,
            "motores": self.motores_disponiveis(),
            "timestamp": datetime.now().isoformat(),
        }