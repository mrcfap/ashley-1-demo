from pathlib import Path
import json
import re
from app.initiative.motor_ressonancia import MotorRessonanciaAntecipacao
from app.adaptive.motor_personalidade_adaptativa import MotorPersonalidadeAdaptativa
from app.history.historia_compartilhada import MotorHistoriaCompartilhada
from app.hub.cognitive_hub import AshleyCognitiveHub

from app.memory.memoria_estrategica import MemoriaEstrategica
from app.relationship.memoria_relacional import MemoriaRelacional
from app.relationship.motor_conexao_humana import MotorConexaoHumana
from app.evolution.reflexao import CicloAprendizado
from app.tools.ferramentas import FerramentasAshley
from app.agents.planner import PlannerAshley
from app.agents.critic import CriticAshley
from app.cases.motor_casos import MotorCasos
from app.cases.motor_resolucao import MotorResolucao
from app.cases.ciclo_adaptativo import CicloAdaptativoResolucao
from app.cases.investigacao_conversacional import InvestigacaoConversacional


from app.evolution.motor_autoevolucao import MotorAutoEvolucao

from app.evolution.self_coding_engine import SelfCodingEngine
from app.evolution.autonomous_coding_loop import AutonomousCodingLoop
from app.evolution.evolution_engine_v11 import EvolutionEngineV11
from app.core.motor_continuidade_cognitiva import MotorContinuidadeCognitiva
from app.reasoning.motor_raciocinio_causal import MotorRaciocinioCausal
from app.reasoning.motor_bom_senso import MotorBomSenso
from app.services.gemini_service import GeminiService
from app.creativity.motor_criatividade_disruptiva import MotorCriatividadeDisruptiva
from app.adaptive_director.diretor_cognitivo_adaptativo import DiretorCognitivoAdaptativoConsequencia

class OrquestradorAshley:
    """
    Orquestrador central da ASHLEY 1.0.

    Fluxo operacional:

    entrada
        ↓
    memória
        ↓
    Planner
        ↓
    ferramenta
        ↓
    Critic
        ↓
    aprovado? ── sim ──> resposta
        │
        não
        ↓
    Reflection Loop
        ↓
    reformulação
        ↓
    nova execução
        ↓
    Critic
    """

    def __init__(
        self,
        db_path="data/ashley_memoria.db",
        user_id=None,
        gemini_service=None
    ):
        self.db_path = db_path
        self.user_id = user_id

        self.memoria = MemoriaEstrategica(db_path)

        self.motor_conexao = MotorConexaoHumana(db_path)

        self.memoria_relacional = MemoriaRelacional(
            db_path=db_path,
            memoria_estrategica=self.memoria
        )

        self.aprendizado = CicloAprendizado(
            self.memoria
        )

        self.ferramentas = FerramentasAshley()

        self.planner = PlannerAshley()

        self.critic = CriticAshley()

        # Motor persistente de resolução e acompanhamento de casos.
        self.motor_casos = MotorCasos(db_path)

        # V4: estrutura diagnóstico, hipóteses, plano e próxima ação.
        self.motor_resolucao = MotorResolucao(db_path)

        # V5: ciclo adaptativo após execução e observação de resultados.
        self.ciclo_adaptativo = CicloAdaptativoResolucao(db_path)

        # V7: coleta progressiva de evidências durante a conversa.
        self.investigacao = InvestigacaoConversacional(db_path)

        # V8: autoavaliação e evolução governada.
        self.autoevolucao = MotorAutoEvolucao(db_path)
        self.self_coder = SelfCodingEngine(project_root=Path.cwd())
        self.autonomous_coder = AutonomousCodingLoop(self.self_coder)
        self.evolution_v11 = EvolutionEngineV11(db_path, self.self_coder, self.autonomous_coder)

        # V12: continuidade cognitiva persistente.
        self.continuidade = MotorContinuidadeCognitiva(db_path)

        # V13: Motor de Ressonância e Antecipação (MRAC).
        self.mrac = MotorRessonanciaAntecipacao(db_path)

        # V14: Framework de Personalidade Adaptativa (FPA).
        self.fpa = MotorPersonalidadeAdaptativa(db_path)

        # V15: Motor de História Compartilhada.
        self.historia = MotorHistoriaCompartilhada(db_path)

        # V18: Motor de Raciocínio Causal.
        self.raciocinio_causal = MotorRaciocinioCausal(db_path)

        # V19: Motor de Bom Senso e Coerência do Mundo.
        self.bom_senso = MotorBomSenso(db_path)

        # V20: Motor de Criatividade Disruptiva e Pensamento Lateral.
        # Aceita uma instância Gemini já existente; se nenhuma for fornecida,
        # cria uma instância compatível com a estrutura atual do projeto.
        self.gemini_service = gemini_service or GeminiService(
            root=Path.cwd(),
            generated_dir=Path.cwd() / "generated"
        )
        self.criatividade = MotorCriatividadeDisruptiva(
            gemini_service=self.gemini_service
        )

        # V21: Diretor Cognitivo Adaptativo por Consequência.
        # Compartilha o mesmo GeminiService da Ashley e mantém memória própria
        # de planos, previsões, resultados observados e lições.
        self.diretor_adaptativo = DiretorCognitivoAdaptativoConsequencia(
            gemini_service=self.gemini_service,
            db_path="data/ashley_v21.db"
        )

        # Cognitive Hub: coordena V12-V21 sem substituir os motores.
        self.hub = AshleyCognitiveHub(
            continuidade=self.continuidade,
            mrac=self.mrac,
            fpa=self.fpa,
            historia=self.historia,
            raciocinio_causal=self.raciocinio_causal,
            bom_senso=self.bom_senso,
            criatividade=self.criatividade,
            diretor_adaptativo=self.diretor_adaptativo
        )

        # Tentativas internas da ferramenta web.
        self.max_tentativas = 2

        # Número máximo de replanejamentos após
        # reprovação do Critic.
        self.max_replanejamentos = 1

    # ==================================================
    # IDENTIDADE
    # ==================================================

    def definir_usuario(self, user_id):

        if user_id is None:
            self.user_id = None
            return

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            raise ValueError(
                "user_id deve ser um número inteiro."
            )

        if user_id <= 0:
            raise ValueError(
                "user_id deve ser maior que zero."
            )

        self.user_id = user_id

    def usuario_atual(self):
        return self.user_id

    # ==================================================
    # MEMÓRIA ESTRATÉGICA
    # ==================================================

    def contexto_memoria(self, objetivo):

        return self.memoria.formatar_contexto(
            objetivo,
            limite=5
        )

    def buscar_experiencias_para_planner(
        self,
        objetivo,
        limite=5
    ):

        experiencias_brutas = (
            self.memoria.buscar_experiencias_relevantes(
                objetivo,
                limite=limite
            )
        )

        return (
            self.planner.converter_experiencias_memoria(
                experiencias_brutas
            )
        )

    # ==================================================
    # MEMÓRIA RELACIONAL
    # ==================================================

    def contexto_relacional(
        self,
        objetivo,
        limite=5
    ):

        if self.user_id is None:
            return (
                "Nenhum usuário identificado. "
                "Memórias pessoais não foram consultadas."
            )

        return (
            self.memoria_relacional
            .montar_contexto_relacional(
                user_id=self.user_id,
                consulta=objetivo,
                limite=limite
            )
        )

    def considerar_memoria_usuario(
        self,
        categoria,
        chave,
        conteudo,
        importancia=None,
        confianca=0.8,
        permanencia=0.7,
        utilidade_futura=0.7,
        origem="conversation"
    ):

        if self.user_id is None:
            return {
                "sucesso": False,
                "guardada": False,
                "erro": "usuario_nao_identificado"
            }

        return (
            self.memoria_relacional
            .considerar_memoria(
                user_id=self.user_id,
                categoria=categoria,
                chave=chave,
                conteudo=conteudo,
                importancia=importancia,
                confianca=confianca,
                permanencia=permanencia,
                utilidade_futura=utilidade_futura,
                origem=origem
            )
        )

    # ==================================================
    # CASOS / ACOMPANHAMENTO
    # ==================================================

    def criar_caso(
        self,
        titulo,
        descricao,
        objetivo="",
        prioridade=3
    ):
        if self.user_id is None:
            raise ValueError(
                "É necessário identificar o usuário antes de criar um caso."
            )

        return self.motor_casos.criar_caso(
            user_id=self.user_id,
            titulo=titulo,
            descricao=descricao,
            objetivo=objetivo,
            prioridade=prioridade
        )

    def casos_ativos(self, limite=10):
        if self.user_id is None:
            return []

        return self.motor_casos.listar_casos(
            user_id=self.user_id,
            incluir_resolvidos=False,
            limite=limite
        )

    def caso_ativo(self):
        if self.user_id is None:
            return None

        return self.motor_casos.caso_ativo(
            self.user_id
        )

    def registrar_evento_caso(
        self,
        caso_id,
        tipo,
        conteudo,
        dados=None
    ):
        if self.user_id is None:
            raise ValueError(
                "É necessário identificar o usuário."
            )

        self.motor_casos.registrar_evento(
            caso_id=caso_id,
            user_id=self.user_id,
            tipo=tipo,
            conteudo=conteudo,
            dados=dados
        )

    def adicionar_acao_caso(
        self,
        caso_id,
        descricao,
        responsavel="usuario",
        prazo=None
    ):
        if self.user_id is None:
            raise ValueError(
                "É necessário identificar o usuário."
            )

        return self.motor_casos.adicionar_acao(
            caso_id=caso_id,
            user_id=self.user_id,
            descricao=descricao,
            responsavel=responsavel,
            prazo=prazo
        )

    def atualizar_status_caso(
        self,
        caso_id,
        status,
        observacao=""
    ):
        if self.user_id is None:
            raise ValueError(
                "É necessário identificar o usuário."
            )

        return self.motor_casos.atualizar_status(
            caso_id=caso_id,
            user_id=self.user_id,
            status=status,
            observacao=observacao
        )

    def contexto_casos(self):
        return self.motor_casos.contexto_usuario(
            self.user_id
        )


    # ==================================================
    # INTELIGÊNCIA DE CASOS V2
    # ==================================================

    def analisar_intencao_caso(self, mensagem):
        """
        Classificação conservadora para continuidade de problemas.

        Não cria um caso para toda conversa. Identifica sinais suficientes
        para orientar o modelo entre:
        CONVERSA_NORMAL, CRIAR_CASO, CONTINUAR_CASO e ATUALIZAR_RESULTADO.

        A criação persistente automática fica desativada nesta etapa:
        primeiro a Ashley usa a decisão para conduzir a conversa; depois
        poderemos permitir abertura automática com critérios mais fortes.
        """
        texto = re.sub(r"\s+", " ", (mensagem or "").lower()).strip()

        if not texto:
            return {
                "decisao": "CONVERSA_NORMAL",
                "confianca": 1.0,
                "caso_id": None,
                "motivos": ["mensagem_vazia"],
                "persistencia_elegivel": False
            }

        casos = self.casos_ativos(limite=10)

        sinais_resultado = [
            "deu certo", "não deu certo", "nao deu certo",
            "funcionou", "não funcionou", "nao funcionou",
            "fiz aquilo", "eu fiz", "já fiz", "ja fiz",
            "resultado", "melhorou", "piorou", "continua igual",
            "continua ruim", "resolvi", "consegui", "não consegui",
            "nao consegui"
        ]

        sinais_continuidade = [
            "aquele problema", "aquela questão", "aquela questao",
            "aquilo que", "como combinamos", "como você falou",
            "como voce falou", "sobre isso", "continuando",
            "voltando ao assunto", "sobre o problema",
            "sobre o caso", "o que fazemos agora",
            "qual o próximo passo", "qual o proximo passo"
        ]

        sinais_problema = [
            "problema", "dificuldade", "não consigo", "nao consigo",
            "preciso resolver", "precisamos resolver", "está dando errado",
            "esta dando errado", "não está funcionando", "nao esta funcionando",
            "perdendo clientes", "vendas caíram", "vendas cairam",
            "prejuízo", "prejuizo", "atrasado", "atrasada",
            "conflito", "crise", "falha", "erro recorrente",
            "não sei o que fazer", "nao sei o que fazer",
            "me ajude a resolver", "ajude a resolver",
            "quero resolver"
        ]

        sinais_objetivo = [
            "quero", "preciso", "precisamos", "objetivo",
            "meta", "gostaria", "tentando", "buscando",
            "melhorar", "resolver", "aumentar", "reduzir",
            "organizar", "implementar", "corrigir"
        ]

        motivos = []

        if casos and any(x in texto for x in sinais_resultado):
            caso = casos[0]
            return {
                "decisao": "ATUALIZAR_RESULTADO",
                "confianca": 0.88,
                "caso_id": caso.get("id"),
                "motivos": ["sinal_de_resultado", "existe_caso_ativo"],
                "persistencia_elegivel": False
            }

        if casos and any(x in texto for x in sinais_continuidade):
            caso = casos[0]
            return {
                "decisao": "CONTINUAR_CASO",
                "confianca": 0.86,
                "caso_id": caso.get("id"),
                "motivos": ["sinal_de_continuidade", "existe_caso_ativo"],
                "persistencia_elegivel": False
            }

        pontos = 0

        if any(x in texto for x in sinais_problema):
            pontos += 2
            motivos.append("problema_identificado")

        if any(x in texto for x in sinais_objetivo):
            pontos += 1
            motivos.append("objetivo_ou_intencao_identificado")

        if len(texto) >= 80:
            pontos += 1
            motivos.append("contexto_suficiente")

        if pontos >= 3:
            return {
                "decisao": "CRIAR_CASO",
                "confianca": min(0.90, 0.60 + (pontos * 0.08)),
                "caso_id": None,
                "motivos": motivos,
                "persistencia_elegivel": True
            }

        return {
            "decisao": "CONVERSA_NORMAL",
            "confianca": 0.80,
            "caso_id": None,
            "motivos": motivos or ["sem_sinais_suficientes"],
            "persistencia_elegivel": False
        }

    def instrucoes_inteligencia_casos(self, mensagem):
        analise = self.analisar_intencao_caso(mensagem)
        decisao = analise["decisao"]

        regras = [
            "=== INTELIGÊNCIA DE RESOLUÇÃO E ACOMPANHAMENTO ===",
            f"DECISÃO OPERACIONAL: {decisao}",
            f"CONFIANÇA: {analise['confianca']}",
            f"CASO RELACIONADO: {analise.get('caso_id')}",
            "REGRAS:",
            "- Converse de forma natural, humana, objetiva e respeitosa.",
            "- Diferencie fatos confirmados, hipóteses e informações faltantes.",
            "- Não invente diagnóstico, causa, resultado ou memória.",
            "- Procure compreender causa, objetivo, restrições e tentativas anteriores.",
            "- Proponha soluções plausíveis, concretas e executáveis.",
            "- Quando houver alternativas, explique vantagens, riscos e dependências.",
            "- Transforme a solução escolhida em próximos passos observáveis.",
            "- Use ferramentas e pesquisa quando informação externa atual for necessária.",
            "- Não execute ações externas de alto impacto sem autorização apropriada.",
            "- Em temas de alto risco, preserve supervisão humana e explicite incertezas.",
        ]

        if decisao == "CRIAR_CASO":
            regras.extend([
                "- Há sinais de um problema acompanhável.",
                "- Investigue o suficiente antes de tratar uma hipótese como causa.",
                "- Ajude a definir resultado desejado e primeiro próximo passo.",
                "- Se a condução V3 confirmar persistência, o caso pode ser tratado como aberto."
            ])

        elif decisao == "CONTINUAR_CASO":
            regras.extend([
                "- Existe sinal de continuidade de um caso ativo.",
                "- Retome o contexto já registrado antes de propor novo plano.",
                "- Pergunte apenas pelo que realmente estiver faltando."
            ])

        elif decisao == "ATUALIZAR_RESULTADO":
            regras.extend([
                "- O usuário parece estar relatando resultado de uma ação anterior.",
                "- Compare resultado observado com o objetivo do caso.",
                "- Identifique o que mudou e proponha manter, corrigir ou reavaliar.",
                "- Considere atualização persistente somente quando a condução V3 a registrar."
            ])

        else:
            regras.append(
                "- Trate como conversa normal; não force a criação de um caso."
            )

        return "\n".join(regras), analise


    # ==================================================
    # CONDUÇÃO AUTÔNOMA DE CASOS V3
    # ==================================================

    def _titulo_caso_da_mensagem(self, mensagem, limite=80):
        texto = re.sub(r"\s+", " ", (mensagem or "")).strip()
        if not texto:
            return "Novo caso"
        if len(texto) <= limite:
            return texto
        return texto[:limite - 3].rstrip() + "..."

    def conduzir_caso_automaticamente(self, mensagem, analise=None):
        """
        Executa persistência controlada das decisões da Inteligência de Casos.

        Autonomia permitida aqui:
        - abrir caso quando os critérios da V2 forem fortes;
        - registrar continuidade;
        - registrar resultados;
        - mover o caso para REAVALIACAO quando chega um resultado.

        Não executa ações externas, financeiras, contratuais, destrutivas
        ou de permissões.
        """
        if self.user_id is None:
            return {
                "executado": False,
                "acao": "SEM_USUARIO",
                "caso_id": None
            }

        analise = analise or self.analisar_intencao_caso(mensagem)
        decisao = analise.get("decisao", "CONVERSA_NORMAL")
        confianca = float(analise.get("confianca", 0.0) or 0.0)

        if decisao == "CONVERSA_NORMAL":
            return {
                "executado": False,
                "acao": "CONVERSA_NORMAL",
                "caso_id": None
            }

        if decisao == "CRIAR_CASO":
            # Só persiste automaticamente com confiança alta.
            if confianca < 0.84:
                return {
                    "executado": False,
                    "acao": "CRIACAO_NAO_CONFIRMADA",
                    "caso_id": None,
                    "motivo": "confianca_insuficiente"
                }

            caso = self.criar_caso(
                titulo=self._titulo_caso_da_mensagem(mensagem),
                descricao=mensagem,
                objetivo=(
                    "Compreender o problema, identificar causas plausíveis, "
                    "definir uma solução executável e acompanhar o resultado."
                ),
                prioridade=3
            )

            self.atualizar_status_caso(
                caso_id=caso["id"],
                status="DIAGNOSTICO",
                observacao=(
                    "Caso aberto automaticamente pela Inteligência de Casos V3 "
                    "após identificação de problema acompanhável."
                )
            )

            return {
                "executado": True,
                "acao": "CASO_CRIADO",
                "caso_id": caso["id"],
                "status": "DIAGNOSTICO"
            }

        caso_id = analise.get("caso_id")
        if not caso_id:
            return {
                "executado": False,
                "acao": "CASO_NAO_LOCALIZADO",
                "caso_id": None
            }

        if decisao == "CONTINUAR_CASO":
            self.registrar_evento_caso(
                caso_id=caso_id,
                tipo="CONTINUIDADE",
                conteudo=mensagem,
                dados={
                    "origem": "conversa",
                    "confianca": confianca
                }
            )

            return {
                "executado": True,
                "acao": "CONTINUIDADE_REGISTRADA",
                "caso_id": caso_id
            }

        if decisao == "ATUALIZAR_RESULTADO":
            self.registrar_evento_caso(
                caso_id=caso_id,
                tipo="RESULTADO_RELATADO",
                conteudo=mensagem,
                dados={
                    "origem": "conversa",
                    "confianca": confianca
                }
            )

            self.atualizar_status_caso(
                caso_id=caso_id,
                status="REAVALIACAO",
                observacao=(
                    "Novo resultado relatado pelo usuário; "
                    "o caso precisa ser reavaliado."
                )
            )

            return {
                "executado": True,
                "acao": "RESULTADO_REGISTRADO",
                "caso_id": caso_id,
                "status": "REAVALIACAO"
            }

        return {
            "executado": False,
            "acao": "DECISAO_NAO_EXECUTADA",
            "caso_id": caso_id
        }


    # ==================================================
    # MOTOR DE RESOLUÇÃO V4
    # ==================================================

    def registrar_diagnostico_caso(
        self, caso_id, resumo, fatos=None, informacoes_faltantes=None
    ):
        if self.user_id is None:
            raise ValueError("É necessário identificar o usuário.")
        return self.motor_resolucao.registrar_diagnostico(
            caso_id=caso_id,
            user_id=self.user_id,
            resumo=resumo,
            fatos=fatos,
            informacoes_faltantes=informacoes_faltantes
        )

    def adicionar_hipotese_caso(
        self, caso_id, hipotese, evidencia="", confianca=0.5
    ):
        if self.user_id is None:
            raise ValueError("É necessário identificar o usuário.")
        return self.motor_resolucao.adicionar_hipotese(
            caso_id=caso_id,
            user_id=self.user_id,
            hipotese=hipotese,
            evidencia=evidencia,
            confianca=confianca
        )

    def criar_plano_resolucao_caso(
        self, caso_id, objetivo, estrategia, criterio_sucesso=""
    ):
        if self.user_id is None:
            raise ValueError("É necessário identificar o usuário.")
        plano_id = self.motor_resolucao.criar_plano(
            caso_id=caso_id,
            user_id=self.user_id,
            objetivo=objetivo,
            estrategia=estrategia,
            criterio_sucesso=criterio_sucesso
        )
        self.atualizar_status_caso(
            caso_id=caso_id,
            status="PLANO",
            observacao="Plano de resolução estruturado pela camada V4."
        )
        return plano_id

    def definir_proxima_acao_caso(
        self, caso_id, descricao, responsavel="usuario", prazo=None
    ):
        if self.user_id is None:
            raise ValueError("É necessário identificar o usuário.")
        acao_id = self.motor_resolucao.definir_proxima_acao(
            caso_id=caso_id,
            user_id=self.user_id,
            descricao=descricao,
            responsavel=responsavel,
            prazo=prazo
        )
        self.registrar_evento_caso(
            caso_id=caso_id,
            tipo="PROXIMA_ACAO",
            conteudo=descricao,
            dados={"responsavel": responsavel, "prazo": prazo, "acao_v4_id": acao_id}
        )
        return acao_id

    def contexto_resolucao_caso(self, caso_id):
        if self.user_id is None or not caso_id:
            return {}
        return self.motor_resolucao.contexto_caso(
            caso_id=caso_id,
            user_id=self.user_id
        )

    def instrucoes_motor_resolucao(self, analise_caso):
        caso_id = (analise_caso or {}).get("caso_id")
        if not caso_id:
            caso = self.caso_ativo()
            caso_id = caso.get("id") if isinstance(caso, dict) else None

        contexto = self.contexto_resolucao_caso(caso_id) if caso_id else {}
        ciclo_v5 = self.contexto_ciclo_adaptativo(caso_id) if caso_id else {}

        return (
            "=== MOTOR DE RESOLUÇÃO V4 + CICLO ADAPTATIVO V5 ===\n"
            "Conduza casos pelo ciclo: DIAGNÓSTICO -> HIPÓTESES -> PLANO -> "
            "AÇÕES -> RESULTADO -> REAVALIAÇÃO -> RESOLVIDO.\n"
            "Antes de recomendar uma ação, separe fatos confirmados de hipóteses.\n"
            "Não trate hipótese como causa comprovada.\n"
            "Quando houver informação insuficiente, identifique exatamente o que falta.\n"
            "Quando houver base suficiente, proponha um plano concreto e um critério de sucesso.\n"
            "Mantenha uma próxima ação clara, observável e atribuída a um responsável.\n"
            "Ações externas relevantes continuam dependendo de autorização apropriada.\n"
            "Ao receber um resultado, compare-o ao critério de sucesso; não declare "
            "resolução sem evidência observável suficiente.\n"
            "ESTADO ESTRUTURADO DO CASO:\n"
            + json.dumps(contexto, ensure_ascii=False)[:6000]
            + "\nHISTÓRICO ADAPTATIVO V5:\n"
            + json.dumps(ciclo_v5, ensure_ascii=False)[:4000]
        )


    # ==================================================
    # CICLO ADAPTATIVO DE RESOLUÇÃO V5
    # ==================================================

    def avaliar_resultado_caso(
        self,
        caso_id,
        resultado_observado,
        classificacao,
        criterio_atendido=False,
        justificativa="",
        acao_id=None,
        proxima_acao=None
    ):
        """
        Fecha uma iteração do caso sem inventar evidência.

        SUCESSO + critério atendido -> RESOLVIDO
        PARCIAL -> REAVALIACAO e mantém/aprimora a estratégia
        FALHA -> REAVALIACAO e reduz confiança das hipóteses abertas
        INCONCLUSIVO -> AGUARDANDO_RESULTADO ou REAVALIACAO

        Se houver proxima_acao, ela é persistida pela V4.
        """
        if self.user_id is None:
            raise ValueError("É necessário identificar o usuário.")

        classificacao = str(classificacao).upper().strip()

        avaliacao_id = self.ciclo_adaptativo.registrar_avaliacao(
            caso_id=caso_id,
            user_id=self.user_id,
            classificacao=classificacao,
            resultado_observado=resultado_observado,
            criterio_atendido=criterio_atendido,
            justificativa=justificativa,
            acao_id=acao_id
        )

        if acao_id is not None:
            self.motor_resolucao.concluir_proxima_acao(
                acao_id=acao_id,
                user_id=self.user_id,
                resultado=resultado_observado
            )

        ajuste_hipoteses = []
        novo_status = "REAVALIACAO"

        if classificacao == "SUCESSO" and criterio_atendido:
            novo_status = "RESOLVIDO"
            ajuste_hipoteses = (
                self.ciclo_adaptativo.ajustar_confianca_hipoteses(
                    caso_id, self.user_id, 0.10
                )
            )
            adaptacao = (
                "Critério de sucesso atendido. Caso encerrado como resolvido."
            )

        elif classificacao == "PARCIAL":
            ajuste_hipoteses = (
                self.ciclo_adaptativo.ajustar_confianca_hipoteses(
                    caso_id, self.user_id, 0.05
                )
            )
            adaptacao = (
                "Resultado parcial: preservar evidências úteis e definir "
                "uma nova ação de validação ou melhoria."
            )

        elif classificacao == "FALHA":
            ajuste_hipoteses = (
                self.ciclo_adaptativo.ajustar_confianca_hipoteses(
                    caso_id, self.user_id, -0.15
                )
            )
            adaptacao = (
                "Ação não produziu o resultado esperado: reavaliar hipótese, "
                "estratégia e informações faltantes."
            )

        else:
            novo_status = "AGUARDANDO_RESULTADO"
            adaptacao = (
                "Evidência inconclusiva: não declarar sucesso ou falha; "
                "coletar informação adicional."
            )

        self.ciclo_adaptativo.registrar_adaptacao(
            caso_id=caso_id,
            user_id=self.user_id,
            tipo=classificacao,
            descricao=adaptacao
        )

        self.registrar_evento_caso(
            caso_id=caso_id,
            tipo="AVALIACAO_V5",
            conteudo=resultado_observado,
            dados={
                "avaliacao_id": avaliacao_id,
                "classificacao": classificacao,
                "criterio_atendido": bool(criterio_atendido),
                "ajuste_hipoteses": ajuste_hipoteses
            }
        )

        self.atualizar_status_caso(
            caso_id=caso_id,
            status=novo_status,
            observacao=adaptacao
        )

        nova_acao_id = None
        if novo_status != "RESOLVIDO" and proxima_acao:
            nova_acao_id = self.definir_proxima_acao_caso(
                caso_id=caso_id,
                descricao=proxima_acao,
                responsavel="usuario"
            )

        return {
            "avaliacao_id": avaliacao_id,
            "caso_id": caso_id,
            "classificacao": classificacao,
            "criterio_atendido": bool(criterio_atendido),
            "novo_status": novo_status,
            "ajuste_hipoteses": ajuste_hipoteses,
            "nova_acao_id": nova_acao_id,
            "adaptacao": adaptacao
        }

    def contexto_ciclo_adaptativo(self, caso_id):
        if self.user_id is None or not caso_id:
            return {}
        return self.ciclo_adaptativo.historico(
            caso_id=caso_id,
            user_id=self.user_id,
            limite=10
        )


    # ==================================================
    # CONDUÇÃO AUTOMÁTICA ESTRUTURADA V6
    # ==================================================

    def estruturar_caso_inicial_automaticamente(self, mensagem, conducao_caso):
        """
        Cria o primeiro estado útil do caso sem inventar causa.

        A V6 transforma um caso recém-aberto em:
        diagnóstico inicial -> hipótese conservadora -> plano -> próxima ação.

        Nesta camada determinística, a mensagem do usuário é tratada como relato,
        não como prova independente. Causas específicas permanecem desconhecidas
        até que existam evidências suficientes.
        """
        if self.user_id is None:
            return {"executado": False, "motivo": "usuario_nao_identificado"}

        conducao_caso = conducao_caso or {}
        if conducao_caso.get("acao") != "CASO_CRIADO":
            return {"executado": False, "motivo": "caso_nao_foi_criado_agora"}

        caso_id = conducao_caso.get("caso_id")
        if not caso_id:
            return {"executado": False, "motivo": "caso_id_ausente"}

        atual = self.contexto_resolucao_caso(caso_id)
        if (
            atual.get("diagnostico")
            or atual.get("hipoteses")
            or atual.get("plano_ativo")
            or atual.get("proxima_acao")
        ):
            return {
                "executado": False,
                "motivo": "estrutura_inicial_ja_existe",
                "caso_id": caso_id
            }

        relato = re.sub(r"\s+", " ", (mensagem or "")).strip()
        if len(relato) > 1200:
            relato = relato[:1197].rstrip() + "..."

        diagnostico_id = self.registrar_diagnostico_caso(
            caso_id=caso_id,
            resumo=(
                "Problema relatado pelo usuário e aberto para investigação. "
                "A causa ainda não foi comprovada."
            ),
            fatos=[
                f"Relato do usuário: {relato}"
            ],
            informacoes_faltantes=[
                "Qual é o resultado concreto que indicará que o problema foi resolvido?",
                "Quando o problema começou e o que mudou antes dele aparecer?",
                "Quais tentativas já foram feitas e quais resultados produziram?",
                "Quais dados objetivos podem confirmar ou refutar as possíveis causas?"
            ]
        )

        hipotese_id = self.adicionar_hipotese_caso(
            caso_id=caso_id,
            hipotese=(
                "A causa principal ainda é indeterminada; é necessário coletar "
                "evidências antes de priorizar uma explicação específica."
            ),
            evidencia=(
                "Existe um problema relatado, mas ainda não há evidência suficiente "
                "para atribuir uma causa."
            ),
            confianca=0.20
        )

        plano_id = self.criar_plano_resolucao_caso(
            caso_id=caso_id,
            objetivo=(
                "Compreender o problema com evidências suficientes para definir "
                "uma intervenção plausível e verificável."
            ),
            estrategia=(
                "Clarificar resultado desejado, levantar linha do tempo, mudanças "
                "recentes, tentativas anteriores e dados observáveis; depois comparar "
                "hipóteses antes de escolher a intervenção."
            ),
            criterio_sucesso=(
                "Ter evidências suficientes para priorizar uma causa ou mecanismo "
                "plausível e definir uma ação cujo resultado possa ser observado."
            )
        )

        proxima_acao_id = self.definir_proxima_acao_caso(
            caso_id=caso_id,
            descricao=(
                "Obter do usuário o resultado desejado, quando o problema começou, "
                "o que mudou antes dele e o que já foi tentado."
            ),
            responsavel="ashley"
        )

        self.registrar_evento_caso(
            caso_id=caso_id,
            tipo="ESTRUTURACAO_AUTOMATICA_V6",
            conteudo="Estrutura inicial de resolução criada automaticamente.",
            dados={
                "diagnostico_id": diagnostico_id,
                "hipotese_id": hipotese_id,
                "plano_id": plano_id,
                "proxima_acao_id": proxima_acao_id
            }
        )

        return {
            "executado": True,
            "caso_id": caso_id,
            "diagnostico_id": diagnostico_id,
            "hipotese_id": hipotese_id,
            "plano_id": plano_id,
            "proxima_acao_id": proxima_acao_id
        }


    # ==================================================
    # INVESTIGAÇÃO CONVERSACIONAL ADAPTATIVA V7
    # ==================================================

    def investigar_resposta_conversacional(self, mensagem, analise_caso, conducao_caso):
        """
        Relaciona uma resposta natural ao caso ativo e atualiza a investigação.

        Não cria uma causa automaticamente. O objetivo desta camada é impedir
        que a Ashley "esqueça" respostas relevantes e permitir que escolha a
        próxima lacuna informacional de maneira consistente.
        """
        if self.user_id is None:
            return {"executado": False, "motivo": "usuario_nao_identificado"}

        analise_caso = analise_caso or {}
        conducao_caso = conducao_caso or {}

        caso_id = (
            analise_caso.get("caso_id")
            or conducao_caso.get("caso_id")
        )

        if not caso_id:
            caso = self.caso_ativo()
            caso_id = caso.get("id") if isinstance(caso, dict) else None

        if not caso_id:
            return {"executado": False, "motivo": "sem_caso_ativo"}

        # Caso recém-criado: a V6 já estruturou a abertura. A V7 começa
        # a trabalhar nas mensagens subsequentes.
        if conducao_caso.get("acao") == "CASO_CRIADO":
            ctx = self.investigacao.contexto(caso_id, self.user_id)
            return {
                "executado": False,
                "motivo": "aguardando_primeira_resposta",
                "caso_id": caso_id,
                **ctx
            }

        achados = self.investigacao.extrair_sinais(mensagem)

        for campo, valor in achados.items():
            self.investigacao.registrar(
                caso_id=caso_id,
                user_id=self.user_id,
                campo=campo,
                valor=valor,
                confianca=0.72
            )

        if achados:
            self.registrar_evento_caso(
                caso_id=caso_id,
                tipo="EVIDENCIA_CONVERSACIONAL_V7",
                conteudo=mensagem,
                dados={
                    "campos_atualizados": list(achados.keys()),
                    "origem": "conversa"
                }
            )

        ctx = self.investigacao.contexto(caso_id, self.user_id)

        # Mantém uma única próxima ação investigativa coerente com o que falta.
        if ctx.get("proxima_pergunta"):
            acao_id = self.definir_proxima_acao_caso(
                caso_id=caso_id,
                descricao=ctx["proxima_pergunta"],
                responsavel="ashley"
            )
        else:
            acao_id = None
            self.atualizar_status_caso(
                caso_id=caso_id,
                status="REAVALIACAO",
                observacao=(
                    "Coleta investigativa inicial concluída; evidências devem "
                    "ser reavaliadas antes de escolher intervenção."
                )
            )

        return {
            "executado": bool(achados),
            "caso_id": caso_id,
            "campos_atualizados": list(achados.keys()),
            "respondidos": ctx["respondidos"],
            "faltantes": ctx["faltantes"],
            "proxima_pergunta": ctx["proxima_pergunta"],
            "proxima_acao_id": acao_id
        }

    def contexto_investigacao_caso(self, caso_id):
        if self.user_id is None or not caso_id:
            return {}
        return self.investigacao.contexto(caso_id, self.user_id)

    def instrucoes_investigacao_v7(self, caso_id):
        ctx = self.contexto_investigacao_caso(caso_id)
        if not ctx:
            return ""

        return (
            "=== INVESTIGAÇÃO CONVERSACIONAL V7 ===\n"
            "Use as respostas já coletadas; não faça o usuário repetir informação.\n"
            "Não trate correlação temporal como causa comprovada.\n"
            "Faça preferencialmente uma pergunta útil por vez.\n"
            "Quando a coleta inicial estiver suficiente, reavalie hipóteses antes "
            "de recomendar uma intervenção.\n"
            "ESTADO DA INVESTIGAÇÃO:\n"
            + json.dumps(ctx, ensure_ascii=False)[:5000]
        )


    # ==================================================
    # AUTOEVOLUÇÃO GOVERNADA V8
    # ==================================================

    def registrar_sinal_evolucao(self, categoria, descricao, severidade=1,
                                 componente="orquestrador", sugestao=None,
                                 risco="MEDIO", titulo=None,
                                 plano_teste=None, criterio_sucesso=None,
                                 rollback=None):
        sinal = {
            "categoria": categoria,
            "descricao": descricao,
            "severidade": severidade,
            "componente": componente,
            "sugestao": sugestao,
            "risco": risco,
            "titulo": titulo or "Melhoria proposta pela Ashley",
            "plano_teste": plano_teste,
            "criterio_sucesso": criterio_sucesso,
            "rollback": rollback
        }
        return self.autoevolucao.ciclo_reflexao(self.user_id, [sinal])

    def painel_autoevolucao(self):
        return self.autoevolucao.painel(self.user_id)

    def aprovar_melhoria(self, proposta_id):
        return self.autoevolucao.aprovar(proposta_id)

    def registrar_teste_melhoria(self, proposta_id, resultado,
                                 metricas=None, passou=False):
        return self.autoevolucao.registrar_experimento(
            proposta_id=proposta_id,
            resultado=resultado,
            metricas=metricas,
            passou=passou,
            ambiente="sandbox"
        )

    # ==================================================
    # SELF-CODING ENGINE V9
    # ==================================================
    def inventario_codigo(self):
        return self.self_coder.inventario()

    def criar_workspace_evolucao(self, proposta_id):
        return str(self.self_coder.criar_workspace(proposta_id))

    def avaliar_risco_codigo(self, arquivos, descricao=""):
        return self.self_coder.avaliar_risco(arquivos, descricao)

    def aplicar_codigo_candidato(self, workspace, arquivo, novo_conteudo):
        return self.self_coder.aplicar_conteudo_candidato(workspace, arquivo, novo_conteudo)

    def diff_codigo_candidato(self, workspace, arquivo):
        return self.self_coder.diff(workspace, arquivo)

    def testar_codigo_candidato(self, workspace, comandos=None):
        sintaxe=self.self_coder.validar_python(workspace)
        if not sintaxe["ok"]:
            return {"ok":False,"sintaxe":sintaxe,"testes":None}
        testes=self.self_coder.executar_testes(workspace,comandos=comandos)
        return {"ok":testes["ok"],"sintaxe":sintaxe,"testes":testes}

    def promover_codigo_candidato(self, workspace, arquivos, risco, autorizado=False):
        return self.self_coder.promover(workspace,arquivos,autorizado=autorizado,risco=risco)

    def rollback_codigo(self, backup_root):
        return self.self_coder.rollback(backup_root)

    # ==================================================
    # AUTONOMOUS CODING LOOP V10
    # ==================================================
    def obter_proposta_evolucao(self, proposta_id):
        painel = self.painel_autoevolucao()
        for proposta in painel.get("propostas", []):
            if proposta.get("id") == proposta_id:
                return proposta
        raise ValueError("Proposta de evolução não encontrada.")

    def prompt_autoprogramacao(self, proposta_id):
        proposta = self.obter_proposta_evolucao(proposta_id)
        return self.autonomous_coder.prompt(proposta)

    def aplicar_autoprogramacao(self, proposta_id, resposta_modelo, comandos=None):
        proposta = self.obter_proposta_evolucao(proposta_id)
        resultado = self.autonomous_coder.aplicar_e_testar(
            proposta, resposta_modelo, comandos=comandos
        )
        self.registrar_teste_melhoria(
            proposta_id=proposta_id,
            resultado=("V10 gerou código candidato em sandbox. "
                       + ("Testes aprovados." if resultado["ok"] else "Testes falharam.")),
            metricas={
                "sintaxe_ok": int(resultado["sintaxe"]["ok"]),
                "testes_ok": int(resultado["testes"]["ok"]),
                "arquivo": resultado["arquivo"]
            },
            passou=resultado["ok"]
        )
        return resultado

    # ==================================================
    # DEFINITIVE EVOLUTION ENGINE V11
    # ==================================================
    def observar_desempenho_v11(self, mensagem, resposta=None, erro=None, preparacao=None):
        return self.evolution_v11.observar_interacao(
            self.user_id, mensagem, resposta=resposta, erro=erro, preparacao=preparacao
        )

    def painel_evolucao_v11(self):
        return self.evolution_v11.painel(self.user_id)

    def politica_evolucao_v11(self, **mudancas):
        return self.evolution_v11.definir_politica(self.user_id, **mudancas)

    def detectar_e_criar_propostas_v11(self):
        criadas=[]
        politica=self.evolution_v11.politica(self.user_id)
        if not politica["auto_propor"]:
            return criadas
        for cand in self.evolution_v11.candidatos(self.user_id):
            anterior=self.evolution_v11.ja_tem_ciclo(self.user_id,cand["fingerprint"])
            if anterior and anterior["estado"] not in {"REJEITADO","FALHOU"}:
                continue
            ciclo=self.evolution_v11.abrir_ciclo(self.user_id,cand)
            risco="MEDIO" if cand["componente"] in {"orquestrador","planner","runtime"} else "BAIXO"
            propostas=self.registrar_sinal_evolucao(
                categoria=cand["categoria"],
                descricao=cand["descricao"],
                severidade=cand["severidade"],
                componente=cand["componente"] or "geral",
                sugestao=("Investigar a causa no código, produzir uma alteração pequena "
                          "e reversível e medir se reduz a recorrência do sinal."),
                risco=risco,
                titulo=f"V11: melhorar {cand['categoria']}"
            )
            if propostas:
                pid=propostas[0]["id"]
                self.evolution_v11.atualizar_ciclo(ciclo,"PROPOSTA_CRIADA",pid)
                criadas.append({"ciclo_id":ciclo,"proposta":propostas[0]})
        return criadas


    # ==================================================
    # CONTINUIDADE COGNITIVA V12
    # ==================================================

    def estado_continuidade(self):
        return self.continuidade.gerar_relatorio_continuidade()

    def criar_objetivo_continuo(self, titulo, descricao="", contexto_origem="",
                                motivo="", prioridade="normal", proxima_acao="",
                                criterio_conclusao="", origem_informacao="usuario",
                                grau_confianca=1.0, objetivo_pai_id=None):
        return self.continuidade.criar_objetivo(
            titulo=titulo, descricao=descricao, contexto_origem=contexto_origem,
            motivo=motivo, prioridade=prioridade, proxima_acao=proxima_acao,
            criterio_conclusao=criterio_conclusao,
            origem_informacao=origem_informacao,
            grau_confianca=grau_confianca,
            objetivo_pai_id=objetivo_pai_id
        )

    def avaliar_acao_continuidade(self, acao_proposta, tipo_acao, objetivo_id=None):
        return self.continuidade.avaliar_risco_e_autonomia(
            acao_proposta, tipo_acao, objetivo_id
        )

    def instrucoes_continuidade_cognitiva(self):
        estado = self.estado_continuidade()
        objetivo = estado.get("objetivo_prioritario")
        if not objetivo:
            return (
                "=== CONTINUIDADE COGNITIVA V12 ===\n"
                "Nenhum objetivo persistente ativo neste momento.\n"
                "Não invente objetivos, decisões ou pendências."
            )

        resumo = {
            "id": objetivo.get("id"),
            "titulo": objetivo.get("titulo"),
            "descricao": objetivo.get("descricao"),
            "status": objetivo.get("status"),
            "progresso": objetivo.get("progresso"),
            "prioridade": objetivo.get("prioridade"),
            "motivo": objetivo.get("motivo"),
            "proxima_acao": objetivo.get("proxima_acao"),
            "dependencia": objetivo.get("dependencia"),
            "bloqueio": objetivo.get("bloqueio"),
            "criterio_conclusao": objetivo.get("criterio_conclusao"),
            "origem_informacao": objetivo.get("origem_informacao"),
            "grau_confianca": objetivo.get("grau_confianca"),
        }
        return (
            "=== CONTINUIDADE COGNITIVA V12 ===\n"
            "Use este estado persistente somente quando for relevante.\n"
            "Diferencie memória registrada de inferência nova.\n"
            "Não trate uma próxima ação como ação já executada.\n"
            "Ações de risco moderado ou alto exigem a governança apropriada.\n"
            "OBJETIVO PRIORITÁRIO PERSISTENTE:\n"
            + json.dumps(resumo, ensure_ascii=False)[:5000]
        )

    # ==================================================
    # RESSONÂNCIA E ANTECIPAÇÃO V13 (MRAC)
    # ==================================================

    def estado_mrac(self):
        return self.mrac.estado_mrac(
            user_id=self.user_id
        )

    def contexto_iniciativa_mrac(self):
        return self.mrac.gerar_contexto_iniciativa(
            user_id=self.user_id,
            limite=5
        )

    def registrar_ponto_cego_mrac(
        self,
        projeto,
        decisao,
        risco_identificado,
        contraponto,
        nivel_risco=1
    ):
        return self.mrac.registrar_ponto_cego(
            projeto=projeto,
            decisao=decisao,
            risco_identificado=risco_identificado,
            contraponto=contraponto,
            nivel_risco=nivel_risco,
            user_id=self.user_id
        )

    def criar_alerta_mrac(
        self,
        tipo,
        titulo,
        descricao,
        prioridade=3
    ):
        return self.mrac.criar_alerta(
            tipo=tipo,
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade,
            user_id=self.user_id
        )

    # ==================================================
    # PERSONALIDADE ADAPTATIVA V14 (FPA)
    # ==================================================

    def estado_fpa(self):
        return self.fpa.estado_fpa(
            user_id=self.user_id
        )

    def contexto_personalidade_adaptativa(self):
        return self.fpa.gerar_contexto_adaptativo(
            user_id=self.user_id
        )

    def adaptar_personalidade(
        self,
        mensagem,
        complexidade="baixa",
        repeticoes_erro=0,
        bloqueios=0
    ):
        return self.fpa.analisar_interacao(
            mensagem=mensagem,
            complexidade=complexidade,
            repeticoes_erro=repeticoes_erro,
            bloqueios=bloqueios,
            user_id=self.user_id
        )

    # ==================================================
    # HISTÓRIA COMPARTILHADA V15
    # ==================================================

    def contexto_historia_compartilhada(self, mensagem, limite=3):
        return self.historia.gerar_contexto_historico(
            consulta=mensagem,
            user_id=self.user_id,
            limite=limite
        )

    def registrar_episodio_historia(self, **dados):
        dados.setdefault("user_id", self.user_id)
        return self.historia.registrar_episodio(**dados)

    # ==================================================
    # ASHLEY COGNITIVE HUB
    # ==================================================

    def estado_cognitive_hub(self):
        return self.hub.estado_hub()

    # Alias público curto para diagnóstico e compatibilidade.
    def estado_hub(self):
        return self.hub.estado_hub()

    def selecionar_motores_cognitivos(self, mensagem, complexidade="baixa"):
        return self.hub.selecionar_motores(
            mensagem=mensagem,
            complexidade=complexidade
        )

    def classificar_governanca_hub(self, acao):
        return self.hub.classificar_governanca(acao)

    # Alias explícito para uso externo/testes do roteador do Hub.
    def selecionar_motores_hub(self, mensagem, complexidade="baixa"):
        return self.hub.selecionar_motores(
            mensagem=mensagem,
            complexidade=complexidade
        )

    # ==================================================
    # RACIOCÍNIO CAUSAL V18
    # ==================================================

    def analisar_causalidade_v18(
        self,
        problema,
        hipotese_principal,
        fatos=None,
        evidencias_favoraveis=None,
        evidencias_contrarias=None,
        causas_alternativas=None,
        variaveis_confusao=None,
        lacunas=None
    ):
        """Executa análise causal estruturada sem autorizar ações externas."""
        return self.hub.contexto_causal_v18(
            problema=problema,
            hipotese_principal=hipotese_principal,
            fatos=fatos,
            evidencias_favoraveis=evidencias_favoraveis,
            evidencias_contrarias=evidencias_contrarias,
            causas_alternativas=causas_alternativas,
            variaveis_confusao=variaveis_confusao,
            lacunas=lacunas,
            user_id=self.user_id
        )

    def instrucoes_raciocinio_causal_v18(self):
        return (
            "=== RACIOCÍNIO CAUSAL V18 ===\n"
            "Separe fatos observados, hipótese causal e inferências.\n"
            "Sequência temporal e correlação, isoladamente, não provam causalidade.\n"
            "Procure evidências favoráveis e contrárias, causas alternativas e "
            "variáveis de confusão.\n"
            "Expresse a conclusão como provisória e compatível com a evidência.\n"
            "Quando faltar evidência, indique a próxima observação ou teste que "
            "mais ajudaria a diferenciar as hipóteses.\n"
            "O V18 orienta análise; não autoriza ação externa ou de alto impacto."
        )

    # ==================================================
    # BOM SENSO E COERÊNCIA DO MUNDO V19
    # ==================================================

    def avaliar_bom_senso_v19(
        self,
        objeto,
        acao,
        contexto="",
        fatos=None,
        persistir=True
    ):
        """Executa avaliação V19 sem transformar plausibilidade em autorização."""
        return self.hub.contexto_bom_senso_v19(
            objeto=objeto,
            acao=acao,
            contexto=contexto,
            fatos=fatos,
            user_id=self.user_id,
            persistir=persistir
        )

    def instrucoes_bom_senso_v19(self):
        return (
            "=== BOM SENSO E COERÊNCIA DO MUNDO V19 ===\n"
            "Diferencie conhecimento recuperado, fatos do caso e inferências.\n"
            "Não ative um risco apenas porque ele existe na memória: verifique "
            "se as pré-condições estão presentes no contexto concreto.\n"
            "Ausência de conflito detectado não equivale a confirmação de segurança.\n"
            "Quando faltar conhecimento, expresse incerteza em vez de inventar.\n"
            "Bom senso avalia coerência e plausibilidade; não prova universalmente "
            "uma conclusão e não autoriza ação externa ou de alto impacto."
        )

    # ==================================================
    # CRIATIVIDADE DISRUPTIVA V20
    # ==================================================

    async def explorar_criatividade_v20(self, problema):
        """Executa o V20 pelo Cognitive Hub sem autorizar ações externas."""
        return await self.hub.contexto_criatividade_v20(
            problema=problema
        )

    def instrucoes_criatividade_v20(self):
        return (
            "=== CRIATIVIDADE DISRUPTIVA V20 ===\n"
            "Gere alternativas exploratórias sem tratar novidade como verdade ou superioridade.\n"
            "Questione premissas, explore analogias e combinações não convencionais.\n"
            "Separe hipótese criativa de recomendação validada.\n"
            "Antes de ação concreta, submeta consequências, plausibilidade, riscos e "
            "governança aos motores apropriados.\n"
            "O V20 amplia o espaço de possibilidades; não autoriza execução externa."
        )

    async def ciclo_criatividade_validada_v20(self, problema):
        """
        Executa o ciclo:
        V20 -> V18 -> V19 -> Critic -> governança.

        O V20 abre possibilidades. As camadas seguintes não "provam" que uma
        ideia é boa; elas registram limites causais, plausibilidade, crítica e
        necessidade de autorização antes de qualquer ação externa.
        """
        exploracao = await self.explorar_criatividade_v20(problema)

        if not exploracao.get("v20_ativo"):
            return {
                "executado": False,
                "etapa": "v20",
                "v20": exploracao,
                "v18": None,
                "v19": None,
                "critic": None,
                "governanca": None,
                "aprovado_para_consideracao": False
            }

        resultado_v20 = exploracao.get("resultado")
        texto_ideias = (
            resultado_v20
            if isinstance(resultado_v20, str)
            else json.dumps(resultado_v20, ensure_ascii=False, default=str)
        )

        # V18: trata a proposta criativa como hipótese a ser testada, nunca
        # como causa/efeito já demonstrado.
        try:
            v18 = self.analisar_causalidade_v18(
                problema=problema,
                hipotese_principal=texto_ideias[:12000],
                fatos=[],
                evidencias_favoraveis=[],
                evidencias_contrarias=[],
                causas_alternativas=[],
                variaveis_confusao=[],
                lacunas=[
                    "A proposta foi gerada criativamente e ainda precisa de evidência.",
                    "Efeitos, custos, riscos e resultados ainda não foram demonstrados."
                ]
            )
        except Exception as exc:
            v18 = {
                "executado": False,
                "erro": f"{type(exc).__name__}: {exc}"
            }

        # V19: verifica coerência/plausibilidade sem transformar isso em
        # autorização de execução.
        try:
            v19 = self.avaliar_bom_senso_v19(
                objeto="proposta criativa V20",
                acao=texto_ideias[:12000],
                contexto=problema,
                fatos=[],
                persistir=False
            )
        except Exception as exc:
            v19 = {
                "executado": False,
                "erro": f"{type(exc).__name__}: {exc}"
            }

        plano_validacao = {
            "tipo": "validacao_criatividade_v20",
            "etapas": ["V20", "V18", "V19", "Critic", "Governanca"],
            "regra": (
                "Criatividade gera hipótese; validação causal, bom senso, crítica "
                "e governança precedem qualquer implementação."
            )
        }

        try:
            critic = self.validar_execucao(
                objetivo=problema,
                resultado={
                    "proposta_v20": resultado_v20,
                    "analise_v18": v18,
                    "analise_v19": v19
                },
                plano=plano_validacao
            )
        except Exception as exc:
            critic = {
                "aprovado": False,
                "erro": f"{type(exc).__name__}: {exc}"
            }

        # A governança classifica a eventual adoção/implementação da proposta.
        try:
            governanca = self.classificar_governanca_hub(
                f"Implementar proposta criativa para: {problema}"
            )
        except Exception as exc:
            governanca = {
                "erro": f"{type(exc).__name__}: {exc}"
            }

        aprovado_critic = bool(
            isinstance(critic, dict) and critic.get("aprovado", False)
        )

        return {
            "executado": True,
            "etapa": "ciclo_completo",
            "v20": exploracao,
            "v18": v18,
            "v19": v19,
            "critic": critic,
            "governanca": governanca,
            "aprovado_para_consideracao": aprovado_critic,
            "regra_execucao": (
                "Aprovação para consideração não autoriza ação externa. "
                "A governança e as permissões aplicáveis continuam obrigatórias."
            )
        }


    # ==================================================
    # DIRETOR COGNITIVO ADAPTATIVO POR CONSEQUÊNCIA V21
    # ==================================================

    def estado_v21(self):
        """Retorna capacidades e limites operacionais do V21."""
        return self.diretor_adaptativo.status()

    async def planejar_objetivo_v21(self, objetivo, contexto=None):
        """
        Solicita planejamento adaptativo pelo Cognitive Hub.

        O plano pode criar especialistas temporários, mas não concede
        permissões nem autoriza ações externas.
        """
        return await self.hub.contexto_diretor_v21(
            objetivo=objetivo,
            contexto=contexto
        )

    async def executar_especialista_v21(
        self,
        especialista,
        objetivo,
        contexto_acumulado=None
    ):
        """
        Executa raciocínio textual de um especialista temporário.
        Ferramentas e ações externas continuam fora da autorização do V21.
        """
        return await self.diretor_adaptativo.executar_especialista(
            especialista=especialista,
            objetivo=objetivo,
            contexto_acumulado=contexto_acumulado
        )

    async def aprender_consequencia_v21(
        self,
        ciclo_id,
        resultado_observado,
        efeitos_inesperados=None
    ):
        """Fecha o ciclo previsto x observado e registra uma lição revisável."""
        return await self.hub.contexto_consequencia_v21(
            ciclo_id=ciclo_id,
            resultado_observado=resultado_observado,
            efeitos_inesperados=efeitos_inesperados
        )

    async def executar_ciclo_v21(self, planejamento):
        """
        Executa, em ordem de dependência, os especialistas temporários de um
        planejamento V21 já criado. Não executa ferramentas externas e não
        fecha aprendizagem por consequência sem resultado observado real.

        Em FALLBACK_LOCAL, o ciclo permanece planejado/aguardando provedor:
        não inventa resultados de especialistas quando o LLM está indisponível.
        """
        # Aceita tanto um objetivo textual quanto um planejamento V21 já pronto.
        # Isso mantém compatibilidade com o uso público mais natural:
        # await executar_ciclo_v21("meu objetivo")
        if isinstance(planejamento, str):
            objetivo = planejamento.strip()
            if not objetivo:
                return {
                    "v21_ativo": False,
                    "fase": "EXECUCAO_ESPECIALISTAS",
                    "status": "OBJETIVO_VAZIO",
                    "resultados": [],
                    "concluidos": []
                }
            planejamento = await self.planejar_objetivo_v21(
                objetivo=objetivo,
                contexto={
                    "origem": "executar_ciclo_v21",
                    "experiencias_recentes": self.experiencias_v21(limite=3)
                }
            )

        planejamento = planejamento or {}

        # Contratos aceitos:
        # 1) envelope V21: {"modo": ..., "plano": {...}}
        # 2) plano direto: {"ciclo_id": ..., "especialistas": [...]}
        if isinstance(planejamento, dict) and isinstance(planejamento.get("plano"), dict):
            plano = planejamento.get("plano")
        elif (
            isinstance(planejamento, dict)
            and "ciclo_id" in planejamento
            and isinstance(planejamento.get("especialistas"), list)
        ):
            plano = planejamento
            planejamento = {"modo": "PLANO_DIRETO", "plano": plano}
        else:
            plano = None

        if not isinstance(plano, dict):
            return {
                "v21_ativo": False,
                "fase": "EXECUCAO_ESPECIALISTAS",
                "status": "SEM_PLANO_VALIDO",
                "resultados": [],
                "concluidos": [],
                "detalhe": "O V21 não retornou um envelope/plano reconhecível."
            }

        # Se o planejamento foi produzido pelo fallback porque o provedor falhou,
        # não fazemos uma segunda chamada inútil ao mesmo provedor nem simulamos
        # resultados cognitivos que não ocorreram.
        if planejamento.get("modo") == "FALLBACK_LOCAL":
            return {
                "v21_ativo": True,
                "fase": "EXECUCAO_ESPECIALISTAS",
                "status": "AGUARDANDO_PROVEDOR",
                "ciclo_id": plano.get("ciclo_id"),
                "modo_planejamento": "FALLBACK_LOCAL",
                "resultados": [],
                "concluidos": [],
                "pendentes": [
                    esp.get("id") for esp in plano.get("especialistas", [])
                    if isinstance(esp, dict)
                ],
                "regra": (
                    "O plano local foi preservado, mas nenhum especialista foi "
                    "simulado sem provedor. A execução poderá ser retomada quando "
                    "o serviço cognitivo estiver disponível."
                )
            }

        concluidos = []
        resultados = []
        falhas = []
        total = len(plano.get("especialistas", []))

        while len(concluidos) < total:
            prontos = self.diretor_adaptativo.proximos_especialistas(
                plano=plano,
                concluidos=concluidos
            )
            prontos = [
                esp for esp in prontos
                if isinstance(esp, dict) and esp.get("id") not in concluidos
            ]

            if not prontos:
                break

            houve_progresso = False
            for especialista in prontos:
                esp_id = especialista.get("id")
                try:
                    resultado = await self.executar_especialista_v21(
                        especialista=especialista,
                        objetivo=plano.get("objetivo", ""),
                        contexto_acumulado={
                            "resultados_anteriores": resultados
                        }
                    )
                    resultados.append(resultado)
                    concluidos.append(esp_id)
                    houve_progresso = True
                except Exception as exc:
                    falhas.append({
                        "especialista_id": esp_id,
                        "erro": f"{type(exc).__name__}: {exc}"
                    })
                    return {
                        "v21_ativo": True,
                        "fase": "EXECUCAO_ESPECIALISTAS",
                        "status": "BLOQUEADO_PROVEDOR_OU_EXECUCAO",
                        "ciclo_id": plano.get("ciclo_id"),
                        "resultados": resultados,
                        "concluidos": concluidos,
                        "falhas": falhas,
                        "requer_validacao": True
                    }

            if not houve_progresso:
                break

        pendentes = [
            esp.get("id") for esp in plano.get("especialistas", [])
            if isinstance(esp, dict) and esp.get("id") not in concluidos
        ]
        status = "CONCLUIDO" if not pendentes and not falhas else "PARCIAL"

        # Critic valida somente o material realmente produzido.
        validacao = None
        if resultados:
            try:
                validacao = self.validar_execucao(
                    objetivo=plano.get("objetivo", ""),
                    resultado={"especialistas_v21": resultados},
                    plano={
                        "estrategia": plano.get("estrategia"),
                        "resultado_esperado": plano.get("resultado_esperado_geral")
                    }
                )
            except Exception as exc:
                validacao = {
                    "aprovado": False,
                    "erro_validacao": f"{type(exc).__name__}: {exc}"
                }

        return {
            "v21_ativo": True,
            "fase": "EXECUCAO_ESPECIALISTAS",
            "status": status,
            "ciclo_id": plano.get("ciclo_id"),
            "resultados": resultados,
            "concluidos": concluidos,
            "pendentes": pendentes,
            "falhas": falhas,
            "validacao_critic": validacao,
            "aguardando_resultado_observado": status == "CONCLUIDO",
            "regra": (
                "A aprendizagem por consequência só será fechada quando houver "
                "resultado observado; saída textual de especialista não é consequência real."
            )
        }

    def experiencias_v21(self, limite=5):
        """Consulta lições recentes sem chamar o Gemini."""
        return self.diretor_adaptativo.memoria.experiencias_recentes(
            limite=limite
        )

    def instrucoes_v21(self):
        return (
            "=== DIRETOR COGNITIVO ADAPTATIVO POR CONSEQUÊNCIA V21 ===\n"
            "Para objetivos complexos, decomponha o problema em especialistas "
            "temporários apenas quando isso trouxer benefício real.\n"
            "Respeite dependências entre especialistas e não trate um papel "
            "temporário como um novo modelo treinado.\n"
            "Antes da execução, registre o resultado esperado. Depois, compare "
            "o esperado com o resultado observado e extraia uma lição proporcional "
            "à evidência.\n"
            "Uma experiência isolada não vira regra universal.\n"
            "O V21 não concede permissões, não altera o próprio código e não "
            "autoriza ações externas ou de alto impacto."
        )


    # ==================================================
    # ESPECIALISTAS DINÂMICOS V16
    # ==================================================

    def selecionar_especialistas_dinamicos(self, objetivo, max_especialistas=4):
        """Seleciona papéis temporários sem criar agentes autônomos paralelos."""
        texto = re.sub(r"\s+", " ", (objetivo or "").lower()).strip()
        catalogo = [
            ("software", "Especialista de Software",
             ["código","codigo","python","api","fastapi","bug","erro","program","backend","frontend","banco de dados","arquitetura","deploy","servidor","github"],
             "Analisar arquitetura, implementação, testes, falhas e integração técnica."),
            ("pesquisa", "Especialista de Pesquisa",
             ["pesquise","pesquisa","fonte","evidência","evidencia","atual","hoje","recente","mercado","concorrente","tendência","tendencia"],
             "Identificar fatos que exigem fontes atuais e separar evidência de inferência."),
            ("produto", "Especialista de Produto",
             ["produto","cliente","usuário","usuario","mvp","funcionalidade","experiência","experiencia","roadmap","diferencial","mercado"],
             "Avaliar valor para o usuário, escopo, prioridade, diferenciação e viabilidade."),
            ("financeiro", "Especialista Financeiro",
             ["investidor","investimento","receita","custo","preço","preco","lucro","faturamento","caixa","valuation","cota","financeiro"],
             "Estruturar premissas financeiras e distinguir projeções, custos e fatos."),
            ("causal", "Especialista de Raciocínio Causal",
             ["causa","causou","por que","efeito","impacto","resultado","hipótese","hipotese","correlação","correlacao"],
             "Separar correlação de causalidade, explicitar hipóteses e variáveis de confusão."),
            ("risco", "Especialista de Risco e Governança",
             ["risco","segurança","seguranca","permissão","permissao","privacidade","biometr","senha","produção","producao","pagamento","contrato","excluir","apagar"],
             "Avaliar risco, reversibilidade, permissões e necessidade de autorização humana."),
            ("criatividade", "Especialista de Exploração Criativa",
             ["ideia","inovador","inovação","inovacao","criativo","diferencial","inventar","alternativa","brainstorm"],
             "Gerar alternativas sem apresentar novidade ou viabilidade como fato não verificado.")
        ]
        candidatos = []
        for ident, papel, sinais, missao in catalogo:
            pontos = sum(1 for sinal in sinais if sinal in texto)
            if pontos:
                candidatos.append({
                    "id": ident, "papel": papel, "missao": missao,
                    "pontuacao": pontos
                })
        candidatos.sort(key=lambda x: (-x["pontuacao"], x["id"]))
        selecionados = candidatos[:max(1, int(max_especialistas or 1))]
        complexidade = "alta" if len(selecionados) >= 3 or len(texto) >= 500 else (
            "media" if len(selecionados) >= 2 or len(texto) >= 220 else "baixa"
        )
        return {
            "versao": "V16",
            "modo": "especialistas_temporarios",
            "complexidade": complexidade,
            "quantidade": len(selecionados),
            "especialistas": selecionados,
            "regras": [
                "Papéis temporários não são identidades autônomas.",
                "Seleção não autoriza ação externa.",
                "Fatos atuais exigem ferramenta ou fonte apropriada.",
                "Governança e Critic permanecem ativos."
            ]
        }

    def contexto_especialistas_dinamicos(self, objetivo):
        selecao = self.selecionar_especialistas_dinamicos(objetivo)
        if not selecao["especialistas"]:
            return None, selecao
        linhas = [
            "=== ESPECIALISTAS DINÂMICOS V16 ===",
            "Use as perspectivas abaixo sem substituir Planner, ferramentas, Critic ou governança."
        ]
        for esp in selecao["especialistas"]:
            linhas.append(f"- {esp['papel']}: {esp['missao']}")
        linhas.extend([
            "Consolide as perspectivas em uma única resposta coerente.",
            "Não invente consenso, execução, fonte, dado ou resultado."
        ])
        return "\n".join(linhas), selecao

    # ==================================================
    # IDENTIDADE VISUAL V1
    # ==================================================

    def contexto_identidade_visual(self, reconhecimento):
        """Aceita identidade somente quando o reconhecimento local diz 'conhecido'."""
        reconhecimento = reconhecimento or {}
        classificacao = str(reconhecimento.get("classificacao") or "").lower().strip()
        identidade = reconhecimento.get("identidade") if classificacao == "conhecido" else None
        return {
            "origem": "visao_local",
            "classificacao": classificacao or None,
            "identidade": identidade,
            "melhor_candidato": reconhecimento.get("melhor_candidato"),
            "similaridade": reconhecimento.get("similaridade"),
            "confianca_deteccao": reconhecimento.get("confianca_deteccao"),
            "pode_assumir_identidade": bool(classificacao == "conhecido" and identidade),
            "regra": "Não inferir identidade em estado incerto, desconhecido ou sem identidade."
        }

    # ==================================================
    # PLANNER
    # ==================================================

    def criar_plano(self, objetivo):

        experiencias = (
            self.buscar_experiencias_para_planner(
                objetivo,
                limite=5
            )
        )

        ferramentas_disponiveis = [
            "pesquisa_web"
        ]

        return self.planner.criar_plano(
            objetivo=objetivo,
            experiencias=experiencias,
            ferramentas_disponiveis=ferramentas_disponiveis,
            contexto={
                "user_id": self.user_id
            }
        )

    # ==================================================
    # CRITIC
    # ==================================================

    def validar_execucao(
        self,
        objetivo,
        resultado,
        plano
    ):

        return self.critic.validar_resultado(
            objetivo=objetivo,
            resultado=resultado,
            plano=plano
        )

    # ==================================================
    # DECISÃO DE PESQUISA WEB
    # ==================================================

    def precisa_pesquisar_web(self, mensagem):

        texto = (
            mensagem or ""
        ).lower().strip()

        indicadores = [
            "pesquise",
            "pesquisa",
            "pesquisar",
            "procure na internet",
            "busque na internet",
            "busca na internet",
            "na internet",
            "na web",
            "notícias",
            "noticia",
            "notícias de hoje",
            "hoje",
            "agora",
            "atualmente",
            "atualizado",
            "atualizada",
            "atualização",
            "últimas notícias",
            "última notícia",
            "mais recente",
            "recentemente",
            "preço atual",
            "cotação",
            "resultado de hoje",
            "quem ganhou",
            "o que aconteceu",
            "lançamento",
            "versão mais recente"
        ]

        return any(
            indicador in texto
            for indicador in indicadores
        )

    def plano_requer_web(
        self,
        plano,
        objetivo
    ):

        if isinstance(plano, dict):

            ferramenta = plano.get(
                "ferramenta_sugerida"
            )

            if ferramenta == "pesquisa_web":
                return True

        return self.precisa_pesquisar_web(
            objetivo
        )

    # ==================================================
    # PESQUISA WEB
    # ==================================================

    async def executar_busca_web(
        self,
        objetivo,
        consulta=None
    ):

        consulta_atual = (
            consulta or objetivo
        ).strip()

        ultimo_erro = ""

        for tentativa in range(
            1,
            self.max_tentativas + 1
        ):

            resultado = (
                await self.ferramentas
                .pesquisar_web(
                    consulta_atual
                )
            )

            if resultado.sucesso:

                resumo = json.dumps(
                    resultado.dados,
                    ensure_ascii=False
                )[:6000]

                self.aprendizado.processar(
                    objetivo=objetivo,
                    estrategia=(
                        f"Pesquisa web DDGS: "
                        f"{consulta_atual}"
                    ),
                    resultado=resumo,
                    sucesso=True
                )

                return {
                    "sucesso": True,
                    "tentativa": tentativa,
                    "consulta": consulta_atual,
                    "dados": resultado.dados,
                    "erro": ""
                }

            ultimo_erro = resultado.erro

            self.aprendizado.processar(
                objetivo=objetivo,
                estrategia=(
                    f"Pesquisa web DDGS: "
                    f"{consulta_atual}"
                ),
                resultado="",
                erro=resultado.erro,
                sucesso=False
            )

            if tentativa < self.max_tentativas:

                consulta_atual = (
                    self._reformular_consulta(
                        objetivo
                    )
                )

        return {
            "sucesso": False,
            "tentativa": self.max_tentativas,
            "consulta": consulta_atual,
            "dados": [],
            "erro": (
                ultimo_erro
                or
                "Não foi possível concluir a pesquisa."
            )
        }

    # ==================================================
    # REFLEXÃO / REFORMULAÇÃO
    # ==================================================

    def _reformular_consulta(
        self,
        objetivo,
        validacao=None
    ):
        """
        Reformula a consulta.

        Se houver uma reprovação do Critic,
        considera os problemas detectados para
        criar uma nova estratégia de pesquisa.
        """

        texto = re.sub(
            r"\s+",
            " ",
            objetivo
        ).strip()

        complemento = (
            "informações atualizadas "
            "fontes confiáveis"
        )

        if validacao:

            problemas = validacao.get(
                "problemas",
                []
            )

            if problemas:

                resumo_problemas = " ".join(
                    str(problema)
                    for problema in problemas
                )

                return (
                    f"{texto} "
                    f"{complemento} "
                    f"reformular pesquisa devido a: "
                    f"{resumo_problemas}"
                )

        return (
            f"{texto} {complemento}"
        )

    async def executar_reflection_loop(
        self,
        objetivo,
        plano,
        resultado_inicial,
        validacao_inicial
    ):
        """
        Ciclo controlado de recuperação.

        Se o Critic reprovar a execução:
        - analisa os problemas;
        - reformula a consulta;
        - executa novamente;
        - submete novamente ao Critic.

        O número de replanejamentos é limitado.
        """

        resultado_atual = resultado_inicial
        validacao_atual = validacao_inicial

        historico = []

        replanejamentos = 0

        while (
            validacao_atual
            and
            not validacao_atual.get(
                "aprovado",
                False
            )
            and
            replanejamentos
            < self.max_replanejamentos
        ):

            replanejamentos += 1

            problemas = validacao_atual.get(
                "problemas",
                []
            )

            consulta_reformulada = (
                self._reformular_consulta(
                    objetivo=objetivo,
                    validacao=validacao_atual
                )
            )

            historico.append({
                "replanejamento": replanejamentos,
                "motivo": problemas,
                "nova_consulta": consulta_reformulada
            })

            resultado_atual = (
                await self.executar_busca_web(
                    objetivo=objetivo,
                    consulta=consulta_reformulada
                )
            )

            validacao_atual = (
                self.validar_execucao(
                    objetivo=objetivo,
                    resultado=resultado_atual,
                    plano=plano
                )
            )

            historico[-1][
                "resultado_aprovado"
            ] = validacao_atual.get(
                "aprovado",
                False
            )

        return {
            "resultado": resultado_atual,
            "validacao": validacao_atual,
            "replanejamentos": replanejamentos,
            "historico": historico,
            "recuperado": (
                replanejamentos > 0
                and
                bool(
                    validacao_atual
                    and
                    validacao_atual.get(
                        "aprovado",
                        False
                    )
                )
            )
        }

    # ==================================================
    # PREPARAÇÃO DO CONTEXTO
    # ==================================================

    async def preparar_contexto(
        self,
        objetivo,
        reconhecimento_visual=None
    ):

        # 0. Inteligência de casos: decide como conduzir a conversa.
        instrucoes_casos, analise_caso = (
            self.instrucoes_inteligencia_casos(objetivo)
        )

        # 0.1 Persistência autônoma controlada.
        conducao_caso = self.conduzir_caso_automaticamente(
            mensagem=objetivo,
            analise=analise_caso
        )

        # V6: se um novo caso acabou de nascer, cria uma estrutura inicial
        # útil e conservadora sem inventar causas específicas.
        estruturacao_v6 = self.estruturar_caso_inicial_automaticamente(
            mensagem=objetivo,
            conducao_caso=conducao_caso
        )

        # V7: em mensagens subsequentes, registra evidências relatadas e
        # seleciona a próxima lacuna informacional relevante.
        investigacao_v7 = self.investigar_resposta_conversacional(
            mensagem=objetivo,
            analise_caso=analise_caso,
            conducao_caso=conducao_caso
        )

        # Recalcula o contexto de casos depois da persistência,
        # para que o modelo já veja o estado atualizado nesta resposta.
        instrucoes_casos, analise_caso_pos = (
            self.instrucoes_inteligencia_casos(objetivo)
        )

        # Mantém a decisão original como intenção e anexa o efeito persistido.
        analise_caso["conducao"] = conducao_caso
        analise_caso["estado_pos_persistencia"] = analise_caso_pos

        # 0.2 Motor de Resolução V4.
        analise_para_resolucao = dict(analise_caso)
        if not analise_para_resolucao.get("caso_id"):
            analise_para_resolucao["caso_id"] = conducao_caso.get("caso_id")
        instrucoes_resolucao = self.instrucoes_motor_resolucao(
            analise_para_resolucao
        )

        caso_id_contexto = (
            analise_para_resolucao.get("caso_id")
            or investigacao_v7.get("caso_id")
        )
        instrucoes_investigacao = self.instrucoes_investigacao_v7(
            caso_id_contexto
        ) if caso_id_contexto else ""

        # Cognitive Hub: seleciona quais motores cognitivos devem participar
        # desta interação, reduzindo contexto redundante sem substituir V12-V15.
        roteamento_hub = self.selecionar_motores_cognitivos(objetivo)
        motores_hub = roteamento_hub.get("motores", {})

        # Identidade Visual V1: transforma o resultado biométrico local em
        # contexto conservador. Somente a classificação "conhecido" autoriza
        # o uso da identidade; estados incerto/desconhecido nunca são assumidos.
        contexto_identidade = (
            self.contexto_identidade_visual(reconhecimento_visual)
            if reconhecimento_visual
            else None
        )
        if contexto_identidade:
            roteamento_hub = dict(roteamento_hub)
            roteamento_hub["identidade_visual"] = contexto_identidade

        # V12: recupera continuidade somente quando o Hub a considerar relevante.
        instrucoes_continuidade = (
            self.instrucoes_continuidade_cognitiva()
            if motores_hub.get("continuidade")
            else None
        )

        # V13: recupera pontos cegos e alertas somente quando necessário.
        contexto_mrac = (
            self.contexto_iniciativa_mrac()
            if motores_hub.get("mrac")
            else None
        )

        # V14: permanece ativo como camada adaptativa de comunicação.
        estado_fpa_atual = self.adaptar_personalidade(
            mensagem=objetivo
        )
        contexto_fpa = (
            self.contexto_personalidade_adaptativa()
            if motores_hub.get("fpa", True)
            else None
        )

        # V15: consulta episódios anteriores apenas quando houver relevância histórica.
        contexto_historia = (
            self.contexto_historia_compartilhada(objetivo)
            if motores_hub.get("historia")
            else None
        )

        # V17: transforma decisões e consequências anteriores em experiência
        # reutilizável. Usa o mesmo motor V12; não cria memória paralela.
        contexto_experiencia_v17 = (
            self.hub.contexto_experiencia_v17(
                mensagem=objetivo,
                objetivo_id=None,
                limite=5
            )
            if motores_hub.get("v17_experiencia")
            else None
        )

        # V20: quando o Hub detectar uma demanda criativa, executa divergência
        # e passa a proposta pelo ciclo V18 -> V19 -> Critic -> governança.
        contexto_criatividade_v20 = (
            await self.ciclo_criatividade_validada_v20(objetivo)
            if motores_hub.get("v20_criatividade")
            else None
        )

        # V21: quando o Cognitive Hub identificar um objetivo complexo,
        # solicita planejamento adaptativo e injeta o plano no contexto.
        # O V21 não concede permissões nem autoriza ações externas.
        contexto_diretor_v21 = (
            await self.planejar_objetivo_v21(
                objetivo=objetivo,
                contexto={
                    "roteamento_hub": roteamento_hub,
                    "experiencias_recentes": self.experiencias_v21(limite=3)
                }
            )
            if motores_hub.get("v21_diretor_adaptativo")
            else None
        )

        # V21.2: conduz automaticamente os especialistas somente quando existe
        # um plano válido. Em fallback local, preserva o plano e aguarda o
        # provedor em vez de inventar resultados.
        execucao_diretor_v21 = (
            await self.executar_ciclo_v21(contexto_diretor_v21)
            if contexto_diretor_v21 and contexto_diretor_v21.get("v21_ativo")
            else None
        )

        # V16: especialistas temporários para tarefas que pedem perspectivas específicas.
        contexto_especialistas, especialistas_v16 = (
            self.contexto_especialistas_dinamicos(objetivo)
        )

        # 1. Planner.
        plano = self.criar_plano(
            objetivo
        )

        resultado_web = None
        validacao = None

        reflection = {
            "replanejamentos": 0,
            "historico": [],
            "recuperado": False
        }

        # 2. Ferramenta.
        if self.plano_requer_web(
            plano,
            objetivo
        ):

            resultado_web = (
                await self.executar_busca_web(
                    objetivo
                )
            )

            # 3. Critic.
            validacao = (
                self.validar_execucao(
                    objetivo=objetivo,
                    resultado=resultado_web,
                    plano=plano
                )
            )

            # 4. Reflection Loop somente
            # se o Critic reprovar.
            if not validacao.get(
                "aprovado",
                False
            ):

                reflection = (
                    await self.executar_reflection_loop(
                        objetivo=objetivo,
                        plano=plano,
                        resultado_inicial=resultado_web,
                        validacao_inicial=validacao
                    )
                )

                resultado_web = (
                    reflection["resultado"]
                )

                validacao = (
                    reflection["validacao"]
                )

        # 5. Contexto consolidado.
        contexto = (
            self.montar_contexto_para_modelo(
                objetivo=objetivo,
                resultado_ferramenta=resultado_web,
                plano=plano,
                validacao=validacao,
                reflection=reflection,
                inteligencia_casos=instrucoes_casos,
                motor_resolucao=instrucoes_resolucao,
                investigacao_v7=instrucoes_investigacao,
                continuidade_cognitiva=instrucoes_continuidade,
                ressonancia_antecipacao=contexto_mrac,
                personalidade_adaptativa=contexto_fpa,
                historia_compartilhada=contexto_historia,
                experiencia_decisao_v17=contexto_experiencia_v17,
                cognitive_hub=roteamento_hub,
                criatividade_validada_v20=contexto_criatividade_v20,
                diretor_adaptativo_v21=(
                    {
                        "planejamento": contexto_diretor_v21,
                        "execucao_especialistas": execucao_diretor_v21
                    }
                    if contexto_diretor_v21
                    else None
                ),
                especialistas_dinamicos=contexto_especialistas,
                identidade_visual=contexto_identidade
            )
        )

        return {
            "contexto": contexto,
            "user_id": self.user_id,
            "memoria_relacional_usada": (
                self.user_id is not None
            ),
            "web_usada": (
                resultado_web is not None
            ),
            "resultado_web": resultado_web,
            "plano": plano,
            "validacao": validacao,
            "reflection": reflection,
            "analise_caso": analise_caso,
            "conducao_caso": conducao_caso,
            "estruturacao_v6": estruturacao_v6,
            "investigacao_v7": investigacao_v7,
            "continuidade_cognitiva": instrucoes_continuidade,
            "ressonancia_antecipacao_v13": contexto_mrac,
            "personalidade_adaptativa_v14": estado_fpa_atual,
            "historia_compartilhada_v15": contexto_historia,
            "experiencia_decisao_v17": contexto_experiencia_v17,
            "criatividade_validada_v20": contexto_criatividade_v20,
            "diretor_adaptativo_v21": contexto_diretor_v21,
            "execucao_especialistas_v21": execucao_diretor_v21,
            "cognitive_hub": roteamento_hub,
            "cognitive_hub_estado": self.estado_cognitive_hub(),
            "especialistas_dinamicos_v16": especialistas_v16,
            "identidade_visual_v1": contexto_identidade,
            "motor_resolucao_v4": True,
            "conducao_estruturada_v6": True
        }

    # ==================================================
    # CONTEXTO PARA O MODELO
    # ==================================================

    def montar_contexto_para_modelo(
        self,
        objetivo,
        resultado_ferramenta=None,
        plano=None,
        validacao=None,
        reflection=None,
        inteligencia_casos=None,
        motor_resolucao=None,
        investigacao_v7=None,
        continuidade_cognitiva=None,
        ressonancia_antecipacao=None,
        personalidade_adaptativa=None,
        historia_compartilhada=None,
        experiencia_decisao_v17=None,
        cognitive_hub=None,
        criatividade_validada_v20=None,
        diretor_adaptativo_v21=None,
        especialistas_dinamicos=None,
        identidade_visual=None
    ):

        memoria_estrategica = (
            self.contexto_memoria(
                objetivo
            )
        )

        memoria_relacional = (
            self.contexto_relacional(
                objetivo
            )
        )

        contexto_casos = (
            self.contexto_casos()
        )

        # O Hub controla a injeção real de V12-V15 no prompt.
        # Motores não selecionados não ocupam contexto do modelo.
        partes = [
            "=== CONTEXTO INTERNO DA ASHLEY ===",
            "\nASHLEY COGNITIVE HUB:",
            json.dumps(cognitive_hub or {}, ensure_ascii=False)[:3000],
        ]

        if identidade_visual:
            partes.extend([
                "\nIDENTIDADE VISUAL VALIDADA (V1):",
                json.dumps(identidade_visual, ensure_ascii=False)[:2000],
                (
                    "REGRA DE IDENTIDADE VISUAL: use o nome da pessoa somente se "
                    "'pode_assumir_identidade' for verdadeiro. Em estado incerto, "
                    "desconhecido ou ausente, não atribua identidade."
                )
            ])

        if especialistas_dinamicos:
            partes.extend([
                "\nORQUESTRAÇÃO DE ESPECIALISTAS (V16):",
                especialistas_dinamicos
            ])

        if continuidade_cognitiva:
            partes.extend([
                "\nCONTINUIDADE COGNITIVA (V12):",
                continuidade_cognitiva
            ])

        if ressonancia_antecipacao:
            partes.extend([
                "\nRESSONÂNCIA E ANTECIPAÇÃO (MRAC V13):",
                ressonancia_antecipacao
            ])

        if personalidade_adaptativa:
            partes.extend([
                "\nPERSONALIDADE ADAPTATIVA (FPA V14):",
                personalidade_adaptativa
            ])

        if historia_compartilhada:
            partes.extend([
                "\nHISTÓRIA COMPARTILHADA (V15):",
                historia_compartilhada
            ])

        if experiencia_decisao_v17:
            partes.extend([
                "\nEXPERIÊNCIA, DECISÃO E CONSEQUÊNCIA (V17):",
                json.dumps(
                    experiencia_decisao_v17,
                    ensure_ascii=False
                )[:6000],
                (
                    "REGRA V17: experiências anteriores são precedentes, não ordens. "
                    "Use aprendizados relevantes para orientar a decisão atual, "
                    "revalide diferenças de contexto e preserve a governança. "
                    "Não trate sucesso passado como garantia de sucesso futuro."
                )
            ])

        if criatividade_validada_v20:
            partes.extend([
                "\nCRIATIVIDADE VALIDADA (V20 -> V18 -> V19 -> CRITIC -> GOVERNANÇA):",
                json.dumps(
                    criatividade_validada_v20,
                    ensure_ascii=False,
                    default=str
                )[:12000],
                (
                    "REGRA DO CICLO CRIATIVO: trate a saída do V20 como exploração. "
                    "Considere as objeções e lacunas de V18/V19 e a validação do Critic. "
                    "Não apresente novidade como eficácia comprovada. "
                    "Não execute ação externa apenas porque a proposta foi aprovada "
                    "para consideração; respeite a governança."
                )
            ])

        if diretor_adaptativo_v21:
            partes.extend([
                "\nDIRETOR COGNITIVO ADAPTATIVO POR CONSEQUÊNCIA (V21):",
                json.dumps(
                    diretor_adaptativo_v21,
                    ensure_ascii=False,
                    default=str
                )[:12000],
                self.instrucoes_v21(),
                (
                    "REGRA OPERACIONAL V21: use o plano como coordenação cognitiva "
                    "para o objetivo atual. Respeite dependências entre especialistas. "
                    "Não alegue que uma etapa, ferramenta ou ação externa foi executada "
                    "sem evidência real. O plano não concede novas permissões. "
                    "Resultados futuros devem ser comparados ao resultado esperado "
                    "antes de gerar uma lição reutilizável."
                )
            ])

        partes.extend([
            "\nMEMÓRIA ESTRATÉGICA:",
            memoria_estrategica
        ])

        if plano:

            partes.append(
                "\nPLANO OPERACIONAL:"
            )

            partes.append(
                json.dumps(
                    plano,
                    ensure_ascii=False
                )[:6000]
            )

        partes.extend([
            "\nMEMÓRIA RELACIONAL DO USUÁRIO:",
            memoria_relacional,
            "\nCASOS E ACOMPANHAMENTOS ATIVOS:",
            contexto_casos,
            (
                "\nINSTRUÇÃO DE CONTINUIDADE: "
                "Se houver um caso ativo relacionado à mensagem atual, "
                "considere seu objetivo, ações, resultados e estado antes "
                "de propor o próximo passo. Não invente eventos ou resultados."
            )
        ])

        if inteligencia_casos:
            partes.extend([
                "\nDECISÃO DA INTELIGÊNCIA DE CASOS:",
                inteligencia_casos
            ])

        if motor_resolucao:
            partes.extend([
                "\nMOTOR DE RESOLUÇÃO E PRÓXIMA AÇÃO:",
                motor_resolucao
            ])

        if investigacao_v7:
            partes.extend([
                "\nINVESTIGAÇÃO CONVERSACIONAL:",
                investigacao_v7
            ])

        if resultado_ferramenta:

            partes.append(
                "\nRESULTADO REAL DE FERRAMENTA WEB:"
            )

            partes.append(
                json.dumps(
                    resultado_ferramenta,
                    ensure_ascii=False
                )[:7000]
            )

        if validacao:

            partes.append(
                "\nVALIDAÇÃO DO CRITIC:"
            )

            partes.append(
                json.dumps(
                    validacao,
                    ensure_ascii=False
                )[:4000]
            )

            if validacao.get(
                "aprovado",
                False
            ):

                partes.append(
                    "\nINSTRUÇÃO DE VALIDAÇÃO: "
                    "O resultado da ferramenta foi aprovado "
                    "pelo Critic e pode ser considerado "
                    "na resposta."
                )

            else:

                partes.append(
                    "\nINSTRUÇÃO DE VALIDAÇÃO: "
                    "O resultado permaneceu reprovado "
                    "pelo Critic. Não apresente dados "
                    "insuficientes ou falhos como se "
                    "fossem confiáveis."
                )

        if (
            reflection
            and
            reflection.get(
                "replanejamentos",
                0
            ) > 0
        ):

            partes.append(
                "\nREFLECTION LOOP:"
            )

            partes.append(
                json.dumps(
                    reflection,
                    ensure_ascii=False
                )[:5000]
            )

        partes.extend([
            "\nINSTRUÇÕES DE PLANEJAMENTO E MEMÓRIA:",
            (
                "Considere o plano operacional como orientação "
                "para organizar a execução da tarefa. "
                "Use os aprendizados de experiências anteriores "
                "quando forem relevantes para o objetivo atual. "
                "Use memórias pessoais apenas como contexto "
                "para compreender melhor o usuário e a "
                "continuidade da interação. "
                "Não trate uma memória como verdade absoluta "
                "quando houver evidência mais recente em "
                "contrário. "
                "A mensagem atual do usuário tem prioridade "
                "sobre memórias antigas conflitantes."
            )
        ])

        return "\n".join(partes)

    # ==================================================
    # DIAGNÓSTICO
    # ==================================================

    def diagnostico(self):

        return {
            "orquestrador": "Ashley 1.0",
            "user_id": self.user_id,
            "memoria_estrategica": True,
            "memoria_relacional": True,
            "planner": True,
            "critic": True,
            "reflection_loop": True,
            "ferramentas": True,
            "motor_casos": True,
            "inteligencia_casos_v2": True,
            "conducao_autonoma_casos_v3": True,
            "motor_resolucao_v4": True,
            "ciclo_adaptativo_v5": True,
            "conducao_estruturada_v6": True,
            "investigacao_conversacional_v7": True,
            "autoevolucao_governada_v8": True,
            "self_coding_engine_v9": True,
            "autonomous_coding_loop_v10": True,
            "definitive_evolution_engine_v11": True,
            "continuidade_cognitiva_v12": True,
            "ressonancia_antecipacao_v13": True,
            "personalidade_adaptativa_v14": True,
            "historia_compartilhada_v15": True,
            "ashley_cognitive_hub": True,
            "criatividade_disruptiva_v20": True,
            "ciclo_criatividade_validada_v20": True,
            "diretor_cognitivo_adaptativo_v21": True,
            "aprendizagem_consequencia_v21": True,
            "especialistas_dinamicos_v16": True,
            "experiencia_decisao_consequencia_v17": True,
            "identidade_visual_v1": True,
            "cognitive_hub_estado": self.estado_cognitive_hub(),
            "max_tentativas_web": (
                self.max_tentativas
            ),
            "max_replanejamentos": (
                self.max_replanejamentos
            )
        }