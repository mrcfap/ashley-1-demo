from dataclasses import dataclass

from ddgs import DDGS


@dataclass
class ResultadoFerramenta:
    sucesso: bool
    dados: list
    erro: str = ""
    ferramenta: str = ""
    consulta: str = ""


class FerramentasAshley:
    """
    Camada de ferramentas externas da Ashley 1.0.

    Pesquisa web gratuita usando DDGS.
    Não necessita chave de API.
    """

    def __init__(self):
        self.max_resultados = 5

    async def pesquisar_web(
        self,
        consulta: str,
        limite: int = 5
    ):
        consulta = (consulta or "").strip()

        if not consulta:
            return ResultadoFerramenta(
                sucesso=False,
                dados=[],
                erro="Consulta vazia.",
                ferramenta="ddgs_web",
                consulta=consulta
            )

        limite = max(
            1,
            min(limite, 10)
        )

        try:
            resultados_brutos = DDGS().text(
                consulta,
                max_results=limite
            )

            resultados = []

            for item in resultados_brutos:
                resultados.append(
                    {
                        "titulo": item.get(
                            "title",
                            ""
                        ),
                        "url": item.get(
                            "href",
                            ""
                        ),
                        "conteudo": item.get(
                            "body",
                            ""
                        )
                    }
                )

            if not resultados:
                return ResultadoFerramenta(
                    sucesso=False,
                    dados=[],
                    erro=(
                        "Nenhum resultado relevante "
                        "foi encontrado."
                    ),
                    ferramenta="ddgs_web",
                    consulta=consulta
                )

            return ResultadoFerramenta(
                sucesso=True,
                dados=resultados,
                erro="",
                ferramenta="ddgs_web",
                consulta=consulta
            )

        except Exception as exc:
            return ResultadoFerramenta(
                sucesso=False,
                dados=[],
                erro=(
                    "Falha na pesquisa web: "
                    f"{type(exc).__name__}: {exc}"
                ),
                ferramenta="ddgs_web",
                consulta=consulta
            )