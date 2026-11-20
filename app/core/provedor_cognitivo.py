"""Adaptador real para a consolidação: Gemini configurado ou Ollama local.
Não ativa inferência externa automaticamente; escolha explícita por ambiente.
"""
from __future__ import annotations
import os
from pathlib import Path

class ProvedorCognitivo:
    def __init__(self, root: str | Path = '.'):
        self.root = Path(root)

    async def gerar_texto(self, prompt: str) -> str:
        if len(prompt) > 24000:
            raise ValueError('Lote de consolidação excedeu o limite')
        provedor = os.getenv('AXYNTORA_COGNITIVE_PROVIDER', 'disabled').lower()
        if provedor == 'ollama':
            from app.services.ollama_local import chat_local
            resposta = await chat_local('Responda somente JSON válido.', prompt, [])
            if isinstance(resposta, str):
                return resposta
            if isinstance(resposta, tuple):
                return str(resposta[0])
            raise RuntimeError('Resposta inesperada do Ollama')
        if provedor == 'gemini':
            from app.services.gemini_service import GeminiService
            svc = GeminiService(self.root, self.root / 'generated')
            texto, _modelo = await svc.chat_com_fallback('Responda somente JSON válido.', prompt, [])
            return texto
        raise RuntimeError('Configure AXYNTORA_COGNITIVE_PROVIDER=gemini; desativado por padrão')
