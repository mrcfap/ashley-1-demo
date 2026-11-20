"""Cliente Ollama somente loopback, sem fallback para serviços externos."""

import asyncio
import base64
import json
import os
import urllib.request

import httpx
from app.services.texto_voz import limpar_resposta_modelo
from urllib.parse import urlsplit


def _endpoint(caminho="/api/chat"):
    base = os.getenv(
        "ASHLEY_OLLAMA_URL",
        "http://127.0.0.1:11434"
    ).rstrip("/")

    parsed = urlsplit(base)

    if (
        parsed.scheme != "http"
        or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path
    ):
        raise ValueError(
            "ASHLEY_OLLAMA_URL deve ser HTTP local (loopback), sem caminho."
        )

    return base + caminho


def _sync_chat(system, message, history):

    # Instrução prioritária para continuidade das conversas.
    memory_rules = """
REGRAS DE MEMÓRIA E CONTINUIDADE:
1. Ao responder perguntas sobre conversas anteriores,
   procure primeiro as declarações do usuário no histórico.
2. Diferencie informações fornecidas pelo usuário
   das respostas anteriores da Ashley.
3. Respostas anteriores da Ashley podem conter erros.
4. Nunca invente lembranças, nomes, palavras ou acontecimentos.
5. Quando encontrar a informação solicitada, responda diretamente.
6. Se a informação não estiver disponível, reconheça essa limitação.
7. Evite relatórios extensos para perguntas simples.
"""

    # Evita enviar contexto excessivo a um modelo local pequeno.
    # A truncagem é configurável e afeta somente o fallback local.
    max_system = max(2000, min(60000, int(os.getenv("ASHLEY_OLLAMA_MAX_SYSTEM_CHARS", "4500"))))
    if len(system) > max_system:
        import logging
        logging.getLogger("ashley.ollama").warning(
            "OLLAMA contexto do sistema reduzido de %s para %s caracteres",
            len(system), max_system
        )
        system = system[-max_system:]
    messages = [
        {
            "role": "system",
            "content": memory_rules + "\n" + system
        }
    ]

    # Histórico enviado pela interface, quando disponível.
    for item in (history or [])[-12:]:

        if not isinstance(item, dict):
            continue

        role = str(item.get("role", "")).lower()
        content = item.get("content", "")

        if role in ("user", "assistant"):
            if isinstance(content, str) and content.strip():
                messages.append({
                    "role": role,
                    "content": content[:max(500, min(12000, int(os.getenv("ASHLEY_OLLAMA_MAX_HISTORY_ITEM_CHARS", "1500"))))]
                })

    messages[0]["content"] += "\nResponda somente com o conteúdo final para o usuário, nunca com raciocínio, planejamento ou blocos <think>. Respeite o idioma solicitado explicitamente, inclusive mandarim. Não traduza nem explique se não for pedido."

    messages.append({
        "role": "user",
        "content": message
    })

    model = os.getenv(
        "ASHLEY_OLLAMA_MODEL",
        "qwen3:1.7b"
    )

    num_ctx = int(os.getenv("ASHLEY_OLLAMA_NUM_CTX", "2048"))
    num_ctx = max(2048, min(num_ctx, 8192))

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "keep_alive": "10m",
        "options": {
            "num_ctx": num_ctx, "num_predict": max(64, min(1024, int(os.getenv("ASHLEY_OLLAMA_NUM_PREDICT", "220"))))
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        _endpoint(),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=100) as response:
        data = json.load(response)

    answer = (
        (data.get("message") or {})
        .get("content", "")
        .strip()
    )

    answer = limpar_resposta_modelo(answer)
    if not answer:
        raise RuntimeError("Ollama retornou resposta vazia.")

    return answer, model


async def chat_local(system, message, history):
    return await asyncio.to_thread(
        _sync_chat,
        system,
        message,
        history
    )


def descrever_imagem_local(imagem: bytes, pergunta: str, instrucoes: str) -> dict:
    modelo = os.getenv("ASHLEY_OLLAMA_VISION_MODEL", "qwen3-vl:2b").strip()

    def falha(status: str) -> dict:
        return {"sucesso": False, "status": status}

    if not modelo or "cloud" in modelo.casefold().replace("-cloud", ":cloud").split(":"):
        return falha("modelo_local_inadequado")

    try:
        with httpx.Client(trust_env=False, follow_redirects=False) as cliente:
            info = cliente.post(_endpoint("/api/show"), json={"model": modelo}, timeout=3)
            if info.status_code == 404:
                return falha("modelo_local_ausente")
            info.raise_for_status()
            metadados = info.json()
            if metadados.get("remote_model") or metadados.get("remote_host") or "vision" not in metadados.get("capabilities", []):
                return falha("modelo_local_inadequado")
            resposta = cliente.post(
                _endpoint(),
                json={
                    "model": modelo,
                    "messages": [
                        {"role": "system", "content": instrucoes},
                        {"role": "user", "content": pergunta,
                         "images": [base64.b64encode(imagem).decode("ascii")]},
                    ],
                    "stream": False,
                    "think": False,
                    "keep_alive": "2m",
                    "options": {"num_ctx": 4096, "num_predict": 240, "temperature": 0.2},
                },
                timeout=45,
            )
            if resposta.status_code == 404:
                return falha("modelo_local_ausente")
            resposta.raise_for_status()
            mensagem = (resposta.json().get("message") or {}).get("content") or ""
            descricao = limpar_resposta_modelo(mensagem).strip()
    except httpx.TimeoutException:
        return falha("tempo_esgotado")
    except (ValueError, httpx.HTTPError):
        return falha("servico_indisponivel")
    if not descricao:
        return falha("sem_descricao")
    return {"sucesso": True, "status": "analise_visual_concluida",
            "descricao": descricao, "modelo": modelo}
