"""Respostas de pesquisa explícita ancoradas no retorno da ferramenta."""
import asyncio
import re
from urllib.parse import urlsplit


PEDIDO_WEB = re.compile(
    r'\b(?:pesquise|procure|busque)\b.{0,80}\b(?:web|internet|site|agora)\b'
    r'|\b(?:use|acione|faça|execute)\s+(?:(?:uma|a)\s+)?pesquisa web\b|\bconsulte\s+(?:o|a)\s+site\b', re.I | re.S,
)


async def pesquisar_no_chat(ferramentas, mensagem):
    """Mostra trechos recuperados e seus links sem síntese pelo modelo."""
    dominio = "bcb.gov.br" if re.search(r"\bbanco central do brasil\b", mensagem, re.I) else None
    consulta = f"site:{dominio} {mensagem}" if dominio else mensagem
    if dominio and re.search(r"\bselic\b", mensagem, re.I):
        consulta = "site:bcb.gov.br meta Selic vigente última decisão Copom histórico taxas juros"
    dados = []
    try:
        resultado = await asyncio.wait_for(ferramentas.pesquisar_web(consulta), timeout=20)
    except asyncio.TimeoutError:
        causa = "A pesquisa excedeu o tempo de espera."
    else:
        causa = ("A ferramenta não retornou resultados utilizáveis."
                 if not resultado.sucesso else "Não encontrei trechos com link na fonte solicitada." if dominio
                 else "A busca não retornou trechos com link.")
        for item in resultado.dados if resultado.sucesso else ():
            url = str(item.get("url") or "").strip()
            trecho = " ".join(str(item.get("conteudo") or "").split())
            try:
                parsed = urlsplit(url)
                host = parsed.hostname or ""
            except ValueError:
                continue
            if parsed.scheme not in ("http", "https") or not host or parsed.username or parsed.password:
                continue
            if dominio and (parsed.scheme != "https" or not (host == dominio or host.endswith("." + dominio))):
                continue
            if not trecho or any(entry["url"] == url for entry in dados):
                continue
            dados.append({"url": url, "trecho": trecho, "titulo": str(item.get("titulo") or host)})
    if dados:
        answer = "Encontrei estes resultados na pesquisa. Os trechos abaixo são do índice da busca:\n\n" + "\n\n".join(
            f'{item["titulo"]}\n{item["trecho"]}\n{item["url"]}' for item in dados[:3]
        )
    else:
        answer = causa
    return {"answer": answer, "web_used": True, "web_success": bool(dados),
            "web_results": len(dados), "web_sources": dados[:3]}
