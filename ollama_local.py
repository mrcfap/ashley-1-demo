"""Cliente Ollama somente loopback, sem fallback para serviços externos."""
import asyncio
import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def _endpoint():
    base = os.getenv('ASHLEY_OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1') or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path:
        raise ValueError('ASHLEY_OLLAMA_URL deve ser HTTP local (loopback), sem caminho.')
    return base + '/api/chat'


def _sync_chat(system, message, history):
    messages = [{'role': 'system', 'content': system}]
    for item in (history or [])[-12:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get('role', '')).lower()
        if role in ('user', 'assistant'):
            content = item.get('content', '')
            if isinstance(content, str) and content.strip():
                messages.append({'role': role, 'content': content[:12000]})
    messages.append({'role': 'user', 'content': message})
    model = os.getenv('ASHLEY_OLLAMA_MODEL', 'qwen3:1.7b')
    payload = json.dumps({'model': model, 'messages': messages, 'stream': False, 'think': False, 'options': {'num_ctx': 2048}}).encode('utf-8')
    req = urllib.request.Request(_endpoint(), data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=100) as response:
        data = json.load(response)
    answer = (data.get('message') or {}).get('content', '').strip()
    if not answer:
        raise RuntimeError('Ollama retornou resposta vazia.')
    return answer, model


async def chat_local(system, message, history):
    return await asyncio.to_thread(_sync_chat, system, message, history)
