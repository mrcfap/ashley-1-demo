"""Recuperação lexical limitada de declarações do usuário na sessão atual.

Não executa texto recuperado como instrução; não consulta outras sessões/usuários.
"""
import math
import re
import unicodedata
from collections import Counter

_STOP = set('a o os as de da do das dos um uma e em no na nos nas para por com que qual quais foi era eu voce você me meu minha nesta neste essa esse aquele anteriormente antes depois informei disse falei mensagem mensagens conversa conversas sessao sessão historico histórico recuperar recupera exatamente exato resposta responda codigo código teste memoria memória'.split())
_MEMORIA = re.compile(r'\b(antes|anterior|anteriormente|lembra|lembrar|lembranca|lembrança|recorda|historico|histórico|disse|falei|informei|enviei|mencionei|guardei|registrado|codigo|código|qual era|qual foi)\b', re.I)


def _tokens(texto):
    normal = unicodedata.normalize('NFKD', texto.lower())
    normal = ''.join(c for c in normal if not unicodedata.combining(c))
    return [t for t in re.findall(r'[a-z0-9]{3,}', normal) if t not in _STOP]



def recuperar_declaracoes(mensagem, historico, limite=2):
    """Recupera declaracoes anteriores relevantes da sessao atual."""
    if not _MEMORIA.search(mensagem):
        return []

    termos = set(_tokens(mensagem))
    if not termos:
        return []

    usuarios = [
        str(item.get("content", ""))
        for item in historico
        if isinstance(item, dict)
        and item.get("role") == "user"
        and isinstance(item.get("content"), str)
    ]

    if not usuarios:
        return []

    docs = [set(_tokens(texto)) for texto in usuarios]
    frequencia = Counter(token for doc in docs for token in doc)
    total = len(docs)

    candidatos = []

    for indice, (texto, palavras) in enumerate(zip(usuarios, docs)):
        comuns = termos & palavras
        if not comuns:
            continue

        pontuacao = sum(
            math.log(1 + (total + 1) / (frequencia[t] + 1))
            for t in comuns
        )

        # Prioriza declaracoes contendo dados concretos.
        if re.search(
            r"\b(?:codigo|c?digo)\s+de\s+verificacao\b",
            mensagem,
            re.I
        ):
            if re.search(
                r"\b[A-Z]{2,}(?:-[A-Z0-9]+){2,}\b",
                texto
            ):
                pontuacao += 10

        # Reduz a prioridade de perguntas antigas.
        if "?" in texto:
            pontuacao -= 3

        # Favorece declaracoes explicitas sem regex sensivel a acentos.
        texto_normalizado = unicodedata.normalize("NFKD", texto.lower())
        texto_normalizado = "".join(
            c for c in texto_normalizado
            if not unicodedata.combining(c)
        )

        if any(expressao in texto_normalizado for expressao in (
            "guarde", "registre", "informacao",
            "o codigo", "codigo de verificacao"
        )):
            pontuacao += 1

        if pontuacao >= 0.8:
            candidatos.append((pontuacao, indice, texto))

    candidatos.sort(key=lambda item: (-item[0], -item[1]))

    return [
        texto[:900]
        for _, _, texto in candidatos[:max(0, min(limite, 3))]
    ]
