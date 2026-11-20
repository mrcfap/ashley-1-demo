"""Classificação leve da intenção conversacional, sem chamadas ao LLM."""
import re
import unicodedata


def _norm(texto):
    texto = unicodedata.normalize("NFKD", str(texto or "").casefold())
    return "".join(c for c in texto if not unicodedata.combining(c))


def classificar_intencao(mensagem):
    t = _norm(mensagem).strip()
    if not t:
        return "conversa"
    if re.search(r"\b(?:diferenciais?|vantagens? competitivas?|o que (?:a |ela )?(?:tem|oferece) de diferente)\b", t) and re.search(r"\b(?:axyntora|ashley|ashen|mercado|outras? ias?|concorrentes?)\b", t):
        return "diferenciais_axyntora"
    # Reações afetivas breves são conversa, não pedidos de planejamento.
    # Evita transformar surpresa, elogios e risadas em análises psicológicas.
    if re.fullmatch(
        r"(?:nossa|uau|caramba|incrivel|sensacional|excelente|"
        r"me surpreendeu(?: agora)?|voce me surpreendeu(?: agora)?|"
        r"que surpresa|adorei|gostei muito|muito bom|boa|haha+|kk+)"
        r"[! .]*", t
    ):
        return "reacao_espontanea"
    # Perguntas técnicas explícitas têm precedência sobre termos de projeto.
    padroes_acao = (
        r"\b(?:fa[cç]a|faca|implemente|corrija|conserte|atualize|desenvolva|"
        r"execute|rode|teste|audite|publique|configure|estruture|analise)\b",
        r"\b(?:quero que voce|pode fazer|preciso que voce)\b",
    )
    if re.search(r"\b(?:auto ?evolucao|autoprogramacao|evolua|evoluir)\b", t) and re.search(r"\b(?:voce|sua|seu|seus|propria|proprio|agentes|autonomia|evolua|evoluir)\b", t):
        return "autoevolucao_solicitada"
    if any(re.search(p, t) for p in padroes_acao):
        return "acao_solicitada"
    if re.search(r"\b(?:como implementar|como corrigir|o que devemos fazer|"
                 r"quais melhorias|qual o plano|me de um plano)\b", t):
        return "planejamento"
    # Relato do usuário sobre ações próprias não é ordem para a assistente.
    if re.search(r"\b(?:estou|vou|acabei de|ja estou|estamos)\b", t):
        return "compartilhamento"
    return "conversa"


def orientacao_conversacional(mensagem):
    intencao = classificar_intencao(mensagem)
    if intencao == "diferenciais_axyntora":
        return (
            "INTENÇÃO DETECTADA: usuário pergunta pelos diferenciais da Axyntora. "
            "Responda diretamente e de modo natural, como alguém que conhece o produto, "
            "sem relatório de fatos versus hipóteses e sem encerrar oferecendo auditoria, "
            "testes, roadmap ou escolha de motor. Cite exemplos concretos: Ashley e Ashen "
            "com estilos e vozes distintos, memória persistente e continuidade de contexto, "
            "idiomas configurados e voz neural, arquitetura modular de motores, "
            "autoevolução governada com autorização humana, e recursos multimodais. "
            "Diferencie recursos implementados de recursos comprovados em operação; "
            "não afirme que todos os 35 idiomas estão homologados no ambiente atual. "
            "Não declare exclusividade nem superioridade frente a concorrentes sem "
            "comparação mensurada; explique que o valor potencial está na combinação "
            "de memória, adaptação e continuidade. Não invente nomes ou capacidades "
            "de motores, nem diga que realizou ações externas."
        )
    if intencao == "reacao_espontanea":
        return (
            "INTENÇÃO DETECTADA: reação espontânea de surpresa, alegria, "
            "humor ou admiração. Responda de modo breve, caloroso e natural, "
            "como numa conversa humana. Não interprete o estado psicológico "
            "do usuário, não explique por que ele se surpreendeu, não faça "
            "relatório nem redirecione para projetos, livros ou gestão. "
            "Não termine com pergunta automática. Se houver uma ideia "
            "criativa anterior, pode continuá-la com uma frase curta e "
            "coerente, sem prometer capacidades inexistentes."
        )
    if intencao == "compartilhamento":
        return (
            "INTENÇÃO DETECTADA: o usuário está apenas compartilhando algo que "
            "ele está fazendo. Reconheça a informação com naturalidade; não "
            "ofereça relatórios, cronogramas, testes, próximos passos nem "
            "perguntas automáticas. Não afirme que registrou uma memória "
            "sem confirmação da gravação."
        )
    if intencao == "autoevolucao_solicitada":
        return (
            "INTENÇÃO DETECTADA: o usuário autorizou uma evolução governada. "
            "Não responda com relatório de fatos/hipóteses/critério/próximo passo "
            "nem peça um fato pessoal como condição. A autorização do usuário "
            "não significa que o código foi alterado. Se não houver ferramenta "
            "de execução acessível nesta chamada, diga brevemente que não pode "
            "executar a autoprogramação por este chat, sem fingir ter iniciado "
            "agentes, testes, gravações ou deploy. Quando houver ferramenta "
            "autorizada, respeite sandbox, aprovação, testes e rollback; nunca "
            "alegue sucesso sem retorno verificável."
        )
    if intencao in ("acao_solicitada", "planejamento"):
        return (
            "INTENÇÃO DETECTADA: há pedido de ação ou planejamento. "
            "Atenda ao pedido de forma objetiva; diferencie o que foi "
            "executado do que é apenas proposta. Não invente ações."
        )
    return (
        "INTENÇÃO DETECTADA: conversa ou pergunta direta. Responda ao que "
        "foi perguntado; não encerre com sugestões de testes, tarefas ou "
        "planos não solicitados."
    )
