import re
import html

def limpar_resposta_modelo(texto: str) -> str:
    """Remove blocos de pensamento marcados sem expor conteúdo interno."""
    if not isinstance(texto, str):
        return ""
    texto = re.sub(r"<think\b[^>]*>[\s\S]*?</think\s*>", "", texto, flags=re.I)
    texto = re.sub(r"<analysis\b[^>]*>[\s\S]*?</analysis\s*>", "", texto, flags=re.I)
    # Se a geração parou dentro de um bloco de raciocínio, não exibir nada dele.
    texto = re.sub(r"<(?:think|analysis)\b[^>]*>[\s\S]*$", "", texto, flags=re.I)
    texto = re.sub(r"</?(?:think|analysis|final)\b[^>]*>", "", texto, flags=re.I)
    texto = texto.strip()
    if re.match(
        r"^(?:(?:okay|alright|well|hmm)[,.!:\s]+)?"
        r"(?:i need to |i should |let me )(?:respond|answer|make sure|think|check)\b",
        texto, flags=re.I,
    ):
        return ""
    return texto


def preparar_texto_voz(texto: str) -> str:
    """Prepara texto para sintese de voz sem alterar seu significado."""
    if not isinstance(texto, str):
        return ""

    texto = limpar_resposta_modelo(texto)
    texto = html.unescape(texto)
    texto = re.sub(r"```[\s\S]*?```", " trecho de codigo omitido ", texto)
    texto = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    texto = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", texto)
    texto = re.sub(r"(?m)^\s*[-*]\s+", "", texto)
    texto = re.sub(r"[*_`~]", "", texto)
    texto = re.sub(r"(?im)^\s*(?:Ashley|Ashen)\s*:\s*", "", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()[:5000]
