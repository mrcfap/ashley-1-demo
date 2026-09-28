from pathlib import Path
import json
import re

from app.memory.memoria_estrategica import MemoriaEstrategica
from app.relationship.memoria_relacional import MemoriaRelacional
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
        user_id=None
    ):
        self.db_path = db_path
        self.user_id = user_id

        self.memoria = MemoriaEstrategica(db_path)

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
        objetivo
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
                investigacao_v7=instrucoes_investigacao
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
        investigacao_v7=None
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

        partes = [
            "=== CONTEXTO INTERNO DA ASHLEY ===",

            "\nMEMÓRIA ESTRATÉGICA:",
            memoria_estrategica
        ]

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
            "max_tentativas_web": (
                self.max_tentativas
            ),
            "max_replanejamentos": (
                self.max_replanejamentos
            )
        }