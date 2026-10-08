import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class EstrategiaCriativa:
    nome: str
    descricao: str


class MotorCriatividadeDisruptiva:
    """V20 — Motor de Criatividade Disruptiva e Pensamento Lateral."""

    VERSAO = "V20.0"

    def __init__(self, gemini_service=None):
        self.gemini = gemini_service
        self.estrategias: List[EstrategiaCriativa] = [
            EstrategiaCriativa("Inversão", "Inverter uma regra considerada natural ou obrigatória."),
            EstrategiaCriativa("Eliminação", "Retirar um elemento considerado indispensável."),
            EstrategiaCriativa("Exagero", "Levar uma característica ao extremo para revelar novas possibilidades."),
            EstrategiaCriativa("Substituição", "Trocar um componente central por algo vindo de outro domínio."),
            EstrategiaCriativa("Analogia distante", "Resolver o problema usando princípios de uma área aparentemente não relacionada."),
            EstrategiaCriativa("Restrição artificial", "Criar deliberadamente uma limitação para obrigar o surgimento de outra solução."),
            EstrategiaCriativa("Mudança de perspectiva", "Observar o problema pelo ponto de vista de outro agente, sistema ou contexto."),
            EstrategiaCriativa("Combinação improvável", "Fundir conceitos distantes para produzir uma nova arquitetura de solução."),
        ]
        self.dominios = [
            "biologia", "psicologia", "arquitetura", "música", "ecologia",
            "economia", "jogos", "medicina", "astronomia", "logística",
            "educação", "sistemas sociais", "engenharia", "neurociência", "arte",
        ]

    def status(self) -> Dict[str, Any]:
        return {
            "motor": "criatividade_disruptiva",
            "versao": self.VERSAO,
            "ativo": True,
            "gemini_disponivel": self.gemini is not None,
            "estrategias": len(self.estrategias),
            "dominios": len(self.dominios),
        }

    def selecionar_estrategias(self, quantidade: int = 3) -> List[Dict[str, str]]:
        quantidade = max(1, min(quantidade, len(self.estrategias)))
        return [asdict(item) for item in random.sample(self.estrategias, quantidade)]

    def gerar_colisoes(self, quantidade: int = 3) -> List[str]:
        quantidade = max(1, min(quantidade, len(self.dominios)))
        return random.sample(self.dominios, quantidade)

    def preparar_exploracao(self, problema: str, contexto: Optional[str] = None) -> Dict[str, Any]:
        problema = (problema or "").strip()
        if not problema:
            raise ValueError("O V20 precisa receber um problema ou desafio.")

        return {
            "versao": self.VERSAO,
            "problema": problema,
            "contexto": contexto or "",
            "estrategias": self.selecionar_estrategias(4),
            "dominios_colisao": self.gerar_colisoes(4),
            "objetivo": (
                "Produzir soluções não óbvias sem abandonar utilidade, "
                "coerência, segurança e viabilidade."
            ),
        }

    def construir_prompt(self, problema: str, contexto: Optional[str] = None) -> str:
        exploracao = self.preparar_exploracao(problema, contexto)
        estrategias = "\n".join(
            f"- {e['nome']}: {e['descricao']}" for e in exploracao["estrategias"]
        )
        dominios = ", ".join(exploracao["dominios_colisao"])

        return f"""
Você está executando o V20 da Ashley:
Motor de Criatividade Disruptiva e Pensamento Lateral.

DESAFIO:
{exploracao['problema']}

CONTEXTO:
{exploracao['contexto'] or 'Nenhum contexto adicional informado.'}

ESTRATÉGIAS DE RUPTURA:
{estrategias}

DOMÍNIOS PARA COLISÃO CONCEITUAL:
{dominios}

Sua tarefa não é simplesmente produzir uma ideia criativa.

Execute o seguinte processo:
1. Identifique as premissas escondidas do problema.
2. Questione quais dessas premissas realmente precisam existir.
3. Gere pelo menos 5 hipóteses significativamente diferentes.
4. Use as estratégias de ruptura fornecidas.
5. Faça analogias com os domínios de colisão.
6. Evite clichês e simples variações da mesma solução.
7. Critique as próprias hipóteses.
8. Descarte ideias que sejam apenas extravagantes sem utilidade.
9. Combine ou transforme as melhores hipóteses.
10. Apresente as 3 propostas mais promissoras.

Para cada proposta apresente:
NOME:
PREMISSA QUEBRADA:
IDEIA:
POR QUE É DIFERENTE:
UTILIDADE:
VIABILIDADE:
RISCOS:
PRÓXIMO EXPERIMENTO:

Não afirme que algo nunca existiu no mundo sem evidência.
Originalidade deve ser tratada como hipótese até ser verificada.
""".strip()

    async def executar(self, problema: str, contexto: Optional[str] = None) -> Dict[str, Any]:
        if self.gemini is None:
            raise RuntimeError("GeminiService não foi conectado ao V20.")

        prompt = self.construir_prompt(problema, contexto)

        sistema = """
Você é a camada de expansão criativa do V20 da Ashley.
Explore possibilidades não óbvias, questione premissas e desenvolva hipóteses úteis.
Criatividade não significa aleatoriedade sem propósito.

Priorize:
- originalidade;
- coerência;
- utilidade;
- viabilidade;
- capacidade de experimentação.

Não afirme que uma ideia é inédita no mundo sem verificação externa.
""".strip()

        resposta, modelo = await self.gemini.chat_com_fallback(
            system=sistema,
            message=prompt,
            history=[],
        )

        return {
            "motor": "criatividade_disruptiva",
            "versao": self.VERSAO,
            "problema": problema,
            "resultado": resposta,
            "modelo": modelo,
        }
