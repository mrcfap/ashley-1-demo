import json
import re

from app.memory.memoria_estrategica import MemoriaEstrategica
from app.evolution.reflexao import CicloAprendizado
from app.tools.ferramentas import FerramentasAshley


class OrquestradorAshley:
    """
    Coordena memória, ferramentas, reflexão e autocorreção
    da Ashley 1.0.
    """

    def __init__(self, db_path):
        self.memoria = MemoriaEstrategica(db_path)
        self.aprendizado = CicloAprendizado(self.memoria)
        self.ferramentas = FerramentasAshley()
        self.max_tentativas = 2

    def contexto_memoria(self, objetivo):
        return self.memoria.formatar_contexto(
            objetivo,
            limite=5
        )

    def precisa_pesquisar_web(self, mensagem):
        """
        Primeira camada de decisão.
        Pesquisa quando a pergunta indicar necessidade de
        informação atual, externa ou explicitamente pesquisada.
        Posteriormente essa decisão também poderá ser auxiliada
        pelo modelo Gemini.
        """
        texto = (mensagem or "").lower().strip()

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

    async def executar_busca_web(
        self,
        objetivo,
        consulta=None
    ):
        """
        Executa pesquisa web com limite de tentativas.
        Sucessos e falhas podem alimentar o ciclo
        de aprendizado estratégico.
        """
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
                "Não foi possível concluir "
                "a pesquisa."
            )
        }

    def _reformular_consulta(self, objetivo):
        """
        Reformulação controlada para a segunda tentativa.
        """
        texto = re.sub(
            r"\s+",
            " ",
            objetivo
        ).strip()

        return (
            f"{texto} informações atualizadas "
            f"fontes confiáveis"
        )

    async def preparar_contexto(
        self,
        objetivo
    ):
        """
        Decide se precisa usar a web e monta o contexto
        que será entregue ao modelo.
        """
        resultado_web = None

        if self.precisa_pesquisar_web(
            objetivo
        ):
            resultado_web = (
                await self.executar_busca_web(
                    objetivo
                )
            )

        contexto = (
            self.montar_contexto_para_modelo(
                objetivo,
                resultado_web
            )
        )

        return {
            "contexto": contexto,
            "web_usada": (
                resultado_web is not None
            ),
            "resultado_web": resultado_web
        }

    def montar_contexto_para_modelo(
        self,
        objetivo,
        resultado_ferramenta=None
    ):
        """
        Produz contexto estruturado para o Gemini.
        """
        memoria = self.contexto_memoria(
            objetivo
        )

        partes = [
            "MEMÓRIA ESTRATÉGICA:",
            memoria
        ]

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

            partes.append(
                "\nINSTRUÇÃO SOBRE A PESQUISA:"
            )

            partes.append(
                "Use os resultados acima somente quando "
                "forem relevantes para responder ao usuário. "
                "Não invente informações ausentes nos resultados."
            )

        return "\n".join(partes)