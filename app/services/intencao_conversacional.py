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
    # Perguntas técnicas explícitas têm precedência sobre termos de projeto.
    padroes_acao = (
        r"\b(?:fa[cç]a|faca|implemente|corrija|conserte|atualize|desenvolva|"
        r"execute|rode|teste|audite|publique|configure|estruture|analise)\b",
        r"\b(?:quero que voce|pode fazer|preciso que voce)\b",
    )
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
    if intencao == "compartilhamento":
        return (
            "INTENÇÃO DETECTADA: o usuário está apenas compartilhando algo que "
            "ele está fazendo. Reconheça a informação com naturalidade; não "
            "ofereça relatórios, cronogramas, testes, próximos passos nem "
            "perguntas automáticas. Não afirme que registrou uma memória "
            "sem confirmação da gravação."
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
