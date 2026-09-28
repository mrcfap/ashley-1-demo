from dataclasses import dataclass


@dataclass
class ResultadoReflexao:
    sucesso: bool
    licao: str
    confianca: float
    status: str
    deve_registrar: bool


class MotorReflexao:
    """
    Camada de reflexão da Ashley 1.0.

    Responsabilidades:
    - avaliar resultados;
    - diferenciar sucesso de falha;
    - produzir uma lição operacional;
    - atribuir confiança;
    - impedir que qualquer ocorrência vire verdade permanente.
    """

    def avaliar(
        self,
        objetivo: str,
        estrategia: str,
        resultado: str = "",
        erro: str = "",
        sucesso: bool | None = None
    ) -> ResultadoReflexao:

        objetivo = (objetivo or "").strip()
        estrategia = (estrategia or "").strip()
        resultado = (resultado or "").strip()
        erro = (erro or "").strip()

        if not objetivo:
            return ResultadoReflexao(
                sucesso=False,
                licao="Objetivo ausente; não há experiência válida para consolidar.",
                confianca=0.0,
                status="descartado",
                deve_registrar=False
            )

        # Falha explícita
        if erro:
            licao = (
                f"A estratégia '{estrategia or 'não especificada'}' "
                f"encontrou o problema: {erro}. "
                "Antes de repetir a abordagem, verificar a causa da falha "
                "e ajustar os parâmetros ou a estratégia."
            )

            return ResultadoReflexao(
                sucesso=False,
                licao=licao,
                confianca=0.65,
                status="provisorio",
                deve_registrar=True
            )

        # Quando o executor informa explicitamente sucesso/falha
        if sucesso is not None:

            if sucesso:
                licao = (
                    f"A estratégia '{estrategia or 'não especificada'}' "
                    "produziu resultado satisfatório para este objetivo."
                )

                return ResultadoReflexao(
                    sucesso=True,
                    licao=licao,
                    confianca=0.75,
                    status="provisorio",
                    deve_registrar=True
                )

            licao = (
                f"A estratégia '{estrategia or 'não especificada'}' "
                "não concluiu o objetivo. Uma abordagem alternativa "
                "deve ser considerada na próxima tentativa."
            )

            return ResultadoReflexao(
                sucesso=False,
                licao=licao,
                confianca=0.55,
                status="provisorio",
                deve_registrar=True
            )

        # Sem evidência suficiente
        if not resultado:
            return ResultadoReflexao(
                sucesso=False,
                licao="Não houve evidência suficiente para avaliar a execução.",
                confianca=0.20,
                status="incerto",
                deve_registrar=False
            )

        return ResultadoReflexao(
            sucesso=True,
            licao=(
                "Foi obtido um resultado, mas ele ainda precisa de "
                "validação antes de ser considerado aprendizado consolidado."
            ),
            confianca=0.40,
            status="incerto",
            deve_registrar=True
        )


class CicloAprendizado:
    """
    Une reflexão e memória estratégica.
    """

    def __init__(self, memoria):
        self.memoria = memoria
        self.reflexao = MotorReflexao()

    def processar(
        self,
        objetivo,
        estrategia,
        resultado="",
        erro="",
        sucesso=None
    ):
        avaliacao = self.reflexao.avaliar(
            objetivo=objetivo,
            estrategia=estrategia,
            resultado=resultado,
            erro=erro,
            sucesso=sucesso
        )

        if avaliacao.deve_registrar:
            self.memoria.registrar_experiencia(
                objetivo=objetivo,
                estrategia=estrategia,
                resultado=resultado,
                sucesso=avaliacao.sucesso,
                erro=erro,
                licao=avaliacao.licao,
                confianca=avaliacao.confianca,
                status=avaliacao.status
            )

        return avaliacao