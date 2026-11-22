"""Seleção conservadora de identidades faciais previamente autorizadas.

Não captura imagens, não cria cadastros e não concede autenticação.
A lista de candidatos deve ser filtrada por consentimento e escopo antes da chamada.
"""
from typing import Iterable, Mapping, Any
import math


def selecionar_identidade(
    candidatos: Iterable[Mapping[str, Any]],
    *,
    limiar: float = 0.65,
    margem: float = 0.08,
) -> dict:
    """Recebe {user_id, nome, similaridade, consentimento} por candidato.

    Recusa identidade quando a diferença entre as duas melhores pontuações
    é insuficiente. Nunca revela nomes ou pontuações dos demais candidatos.
    """
    if not 0 <= limiar <= 1 or not 0 <= margem <= 1:
        raise ValueError("Limiares inválidos")
    elegiveis = []
    for candidato in candidatos:
        if candidato.get("consentimento") is not True:
            continue
        score = candidato.get("similaridade")
        uid = candidato.get("user_id")
        nome = candidato.get("nome")
        if (isinstance(score, (float, int)) and not isinstance(score, bool)
                and math.isfinite(score) and -1 <= score <= 1
                and isinstance(uid, int) and uid > 0
                and isinstance(nome, str) and nome.strip()):
            elegiveis.append((float(score), uid, nome.strip()))
    elegiveis.sort(reverse=True)
    if not elegiveis or elegiveis[0][0] < limiar:
        return {"classificacao": "desconhecido", "identidade": None, "user_id": None}
    if len(elegiveis) > 1 and elegiveis[0][0] - elegiveis[1][0] < margem:
        return {"classificacao": "incerto", "identidade": None, "user_id": None}
    score, uid, nome = elegiveis[0]
    return {"classificacao": "conhecido", "identidade": nome, "user_id": uid,
            "similaridade": round(score, 4)}
