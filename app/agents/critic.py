from typing import Any, Dict, Optional
from datetime import datetime


class CriticAshley:
    """
    Agente responsável por validar resultados produzidos
    durante a execução de uma tarefa.

    O Critic não executa ferramentas e não altera o sistema.
    Ele analisa o resultado e informa se a execução pode ser
    aceita ou se deve ser revista.
    """

    def __init__(self):
        self.nome = "CriticAshley"
        self.versao = "1.0"

    def validar_resultado(
        self,
        objetivo: str,
        resultado: Any,
        plano: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        plano = plano or {}

        problemas = []
        observacoes = []

        # -----------------------------------------
        # 1. VERIFICAR EXISTÊNCIA DO RESULTADO
        # -----------------------------------------

        if resultado is None:
            problemas.append(
                "Nenhum resultado foi produzido."
            )

        # -----------------------------------------
        # 2. VALIDAR RESULTADO DE FERRAMENTA
        # -----------------------------------------

        if isinstance(resultado, dict):

            if "sucesso" in resultado:
                if not resultado.get("sucesso"):
                    erro = resultado.get("erro")

                    if erro:
                        problemas.append(
                            f"A execução informou falha: {erro}"
                        )
                    else:
                        problemas.append(
                            "A execução informou falha."
                        )

            if "dados" in resultado:
                dados = resultado.get("dados")

                if dados is None:
                    problemas.append(
                        "A execução não retornou dados."
                    )

                elif isinstance(
                    dados,
                    (list, tuple, dict, str)
                ) and len(dados) == 0:
                    problemas.append(
                        "A execução retornou dados vazios."
                    )

        # -----------------------------------------
        # 3. VERIFICAR PLANO
        # -----------------------------------------

        if plano:
            status_plano = plano.get("status")

            if status_plano != "planejado":
                observacoes.append(
                    "O plano recebido não está marcado "
                    "como planejado."
                )

        # -----------------------------------------
        # 4. DECISÃO
        # -----------------------------------------

        aprovado = len(problemas) == 0

        if aprovado:
            decisao = "aprovado"
            recomendacao = "responder_usuario"
        else:
            decisao = "reprovado"
            recomendacao = "revisar_execucao"

        # -----------------------------------------
        # 5. RETORNO ESTRUTURADO
        # -----------------------------------------

        return {
            "critic": self.nome,
            "versao": self.versao,
            "criado_em": datetime.now().isoformat(),
            "objetivo": objetivo,
            "aprovado": aprovado,
            "decisao": decisao,
            "problemas": problemas,
            "observacoes": observacoes,
            "recomendacao": recomendacao,
            "status": "validado"
        }