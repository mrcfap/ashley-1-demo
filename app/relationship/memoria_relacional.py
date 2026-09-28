from datetime import datetime, timezone
import re

from app.memory.memoria_estrategica import MemoriaEstrategica


class MemoriaRelacional:
    """
    Camada de inteligência relacional da ASHLEY 1.0.

    Responsabilidades:
    - avaliar se uma informação merece ser lembrada;
    - classificar o tipo de memória;
    - calcular importância e confiança;
    - evitar armazenamento de informações triviais;
    - armazenar memórias vinculadas ao usuário;
    - recuperar contexto pessoal relevante;
    - ajudar Ashley a aprender como trabalhar
      melhor com cada pessoa.

    Esta classe NÃO substitui MemoriaEstrategica.
    Ela utiliza MemoriaEstrategica como camada
    de persistência.
    """

    CATEGORIAS_VALIDAS = {
        "perfil",
        "preferencia",
        "forma_trabalho",
        "projeto",
        "decisao",
        "feedback",
        "relacionamento",
        "contexto",
    }

    # Categorias com tendência maior à permanência.
    PESO_CATEGORIA = {
        "perfil": 0.85,
        "preferencia": 0.80,
        "forma_trabalho": 0.90,
        "projeto": 0.80,
        "decisao": 0.85,
        "feedback": 0.75,
        "relacionamento": 0.75,
        "contexto": 0.55,
    }

    # Expressões muito triviais que normalmente
    # não justificam memória permanente.
    EXPRESSOES_TRIVIAIS = {
        "ok",
        "okay",
        "beleza",
        "certo",
        "correto",
        "entendi",
        "obrigado",
        "obrigada",
        "valeu",
        "sim",
        "não",
        "nao",
        "bom dia",
        "boa tarde",
        "boa noite",
        "até mais",
        "ate mais",
    }

    def __init__(
        self,
        db_path="data/ashley_memoria.db",
        memoria_estrategica=None,
    ):
        if memoria_estrategica is not None:
            self.memoria = memoria_estrategica
        else:
            self.memoria = MemoriaEstrategica(db_path)

    # ==================================================
    # NORMALIZAÇÃO
    # ==================================================

    def _normalizar_texto(self, texto):
        if texto is None:
            return ""

        return " ".join(
            str(texto).strip().split()
        )

    def _normalizar_chave(self, chave):
        """
        Converte uma descrição em uma chave estável.

        Exemplo:
        "Preferência por passo a passo"
        vira:
        "preferencia_por_passo_a_passo"
        """

        chave = self._normalizar_texto(chave).lower()

        substituicoes = {
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
            "ç": "c",
        }

        for origem, destino in substituicoes.items():
            chave = chave.replace(origem, destino)

        chave = re.sub(
            r"[^a-z0-9]+",
            "_",
            chave,
        )

        return chave.strip("_")

    # ==================================================
    # AVALIAÇÃO DE CANDIDATO A MEMÓRIA
    # ==================================================

    def avaliar_candidato(
        self,
        conteudo,
        categoria,
        importancia=None,
        confianca=0.8,
        permanencia=0.7,
        utilidade_futura=0.7,
    ):
        """
        Decide se determinada informação merece
        virar memória de longo prazo.

        Retorna a avaliação, mas ainda não grava.
        """

        conteudo = self._normalizar_texto(conteudo)
        categoria = (
            self._normalizar_texto(categoria)
            .lower()
        )

        if not conteudo:
            return {
                "guardar": False,
                "motivo": "conteudo_vazio",
                "pontuacao": 0.0,
            }

        if categoria not in self.CATEGORIAS_VALIDAS:
            return {
                "guardar": False,
                "motivo": "categoria_invalida",
                "pontuacao": 0.0,
            }

        texto_minusculo = conteudo.lower()

        if texto_minusculo in self.EXPRESSOES_TRIVIAIS:
            return {
                "guardar": False,
                "motivo": "informacao_trivial",
                "pontuacao": 0.0,
            }

        # Mensagens extremamente curtas tendem
        # a não possuir contexto suficiente.
        if len(conteudo) < 12:
            return {
                "guardar": False,
                "motivo": "conteudo_curto_demais",
                "pontuacao": 0.1,
            }

        confianca = self._limitar_01(confianca)
        permanencia = self._limitar_01(permanencia)
        utilidade_futura = self._limitar_01(
            utilidade_futura
        )

        peso_categoria = self.PESO_CATEGORIA[
            categoria
        ]

        if importancia is None:
            importancia = (
                peso_categoria * 0.40
                + permanencia * 0.30
                + utilidade_futura * 0.30
            )
        else:
            importancia = self._limitar_01(
                importancia
            )

        # Pontuação geral para decidir armazenamento.
        pontuacao = (
            importancia * 0.35
            + confianca * 0.20
            + permanencia * 0.20
            + utilidade_futura * 0.25
        )

        pontuacao = round(
            self._limitar_01(pontuacao),
            3,
        )

        # Nesta primeira versão usamos 0.60.
        # Depois esse limiar poderá ser adaptativo.
        guardar = pontuacao >= 0.60

        return {
            "guardar": guardar,
            "motivo": (
                "memoria_relevante"
                if guardar
                else "relevancia_insuficiente"
            ),
            "categoria": categoria,
            "conteudo": conteudo,
            "importancia": round(
                importancia,
                3,
            ),
            "confianca": round(
                confianca,
                3,
            ),
            "permanencia": round(
                permanencia,
                3,
            ),
            "utilidade_futura": round(
                utilidade_futura,
                3,
            ),
            "pontuacao": pontuacao,
        }

    # ==================================================
    # REGISTRO INTELIGENTE
    # ==================================================

    def considerar_memoria(
        self,
        user_id,
        categoria,
        chave,
        conteudo,
        importancia=None,
        confianca=0.8,
        permanencia=0.7,
        utilidade_futura=0.7,
        origem="conversation",
    ):
        """
        Avalia e, caso seja relevante,
        grava a memória do usuário.
        """

        if user_id is None:
            return {
                "sucesso": False,
                "guardada": False,
                "erro": "user_id_obrigatorio",
            }

        avaliacao = self.avaliar_candidato(
            conteudo=conteudo,
            categoria=categoria,
            importancia=importancia,
            confianca=confianca,
            permanencia=permanencia,
            utilidade_futura=utilidade_futura,
        )

        if not avaliacao["guardar"]:
            return {
                "sucesso": True,
                "guardada": False,
                "avaliacao": avaliacao,
            }

        chave_normalizada = self._normalizar_chave(
            chave
        )

        if not chave_normalizada:
            return {
                "sucesso": False,
                "guardada": False,
                "erro": "chave_invalida",
            }

        memoria = (
            self.memoria.guardar_memoria_longo_prazo(
                categoria=avaliacao["categoria"],
                chave=chave_normalizada,
                conteudo=avaliacao["conteudo"],
                importancia=avaliacao[
                    "importancia"
                ],
                confianca=avaliacao[
                    "confianca"
                ],
                origem=origem,
                user_id=user_id,
            )
        )

        return {
            "sucesso": True,
            "guardada": True,
            "avaliacao": avaliacao,
            "memoria": memoria,
        }

    # ==================================================
    # RECUPERAÇÃO RELACIONAL
    # ==================================================

    def recuperar_contexto(
        self,
        user_id,
        consulta,
        limite=5,
    ):
        """
        Recupera memórias pessoais relevantes
        para a conversa atual.
        """

        if user_id is None:
            return []

        consulta = self._normalizar_texto(
            consulta
        )

        if not consulta:
            return []

        return (
            self.memoria.buscar_memorias_relevantes(
                user_id=user_id,
                consulta=consulta,
                limite=limite,
            )
        )

    # ==================================================
    # FORMATAÇÃO PARA O MODELO
    # ==================================================

    def montar_contexto_relacional(
        self,
        user_id,
        consulta,
        limite=5,
    ):
        """
        Transforma as memórias recuperadas em
        contexto que posteriormente será entregue
        ao modelo de linguagem.
        """

        memorias = self.recuperar_contexto(
            user_id=user_id,
            consulta=consulta,
            limite=limite,
        )

        if not memorias:
            return (
                "Nenhuma memória pessoal relevante "
                "foi encontrada para esta interação."
            )

        linhas = [
            "Memórias pessoais relevantes do usuário:"
        ]

        for memoria in memorias:
            linhas.append(
                "- "
                f"[{memoria['categoria']}] "
                f"{memoria['conteudo']} "
                f"(confiança: "
                f"{memoria['confianca']:.2f}; "
                f"importância: "
                f"{memoria['importancia']:.2f})"
            )

        return "\n".join(linhas)

    # ==================================================
    # UTILITÁRIOS
    # ==================================================

    def _limitar_01(self, valor):
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                valor,
            ),
        )

    def diagnostico(self):
        """
        Informações básicas do módulo para testes.
        """

        return {
            "modulo": "memoria_relacional",
            "status": "operacional",
            "categorias": sorted(
                self.CATEGORIAS_VALIDAS
            ),
            "versao": "1.0",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }