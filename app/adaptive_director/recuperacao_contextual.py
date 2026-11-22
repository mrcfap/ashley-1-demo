"""Recuperação textual local por termos, com isolamento de usuários."""
import re
from collections import Counter

def recuperar_contexto(consulta: str, documentos: list[dict], *, usuario_id: int, limite: int = 5) -> list[dict]:
    if usuario_id <= 0 or not 1 <= limite <= 20:
        raise ValueError("Parâmetros inválidos")
    termos = Counter(re.findall(r"\w+", consulta.casefold()))
    candidatos = []
    for doc in documentos:
        if doc.get("usuario_id") != usuario_id or doc.get("consentimento") is not True:
            continue
        conteudo = doc.get("texto", "")
        if not isinstance(conteudo, str):
            continue
        palavras = Counter(re.findall(r"\w+", conteudo.casefold()))
        pontos = sum(min(q, palavras[t]) for t, q in termos.items())
        if pontos:
            candidatos.append((pontos, str(doc.get("id", "")), conteudo[:1200]))
    candidatos.sort(key=lambda x: (-x[0], x[1]))
    return [{"id": ident, "trecho": trecho, "relevancia": pontos} for pontos, ident, trecho in candidatos[:limite]]
