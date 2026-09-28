import os
import base64
import asyncio
import uuid
from pathlib import Path

from fastapi import HTTPException
from google import genai


class GeminiService:
    def __init__(self, root: Path, generated_dir: Path):
        self.root = root
        self.generated_dir = generated_dir
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.key = os.getenv("GEMINI_API_KEY", "")
        self.chat_models = self._lista("GEMINI_CHAT_MODELS", "gemini-3.8-flash,gemini-2.5-flash")
        self.file_models = self._lista("GEMINI_FILE_MODELS", "gemini-3.8-flash,gemini-2.5-flash")
        self.image_models = self._lista("GEMINI_IMAGE_MODELS", "gemini-3.1-flash-image,gemini-2.5-flash-image")
        self.video_models = self._lista("GEMINI_VIDEO_MODELS", "veo-3.1-generate-preview")
        self.tts_models = self._lista("GEMINI_TTS_MODELS", "gemini-3.8-flash-tts")

    def _lista(self, nome, padrao):
        return [x.strip() for x in os.getenv(nome, padrao).split(",") if x.strip()]

    def _client(self):
        if not self.key:
            raise HTTPException(503, "Configure GEMINI_API_KEY no servidor.")
        return genai.Client(api_key=self.key)

    def modelos_publicos(self):
        return {
            "chat": self.chat_models,
            "files": self.file_models,
            "image": self.image_models,
            "video": self.video_models,
            "tts": self.tts_models
        }

    @staticmethod
    def _retryable(exc):
        s = str(exc).lower()
        return any(x in s for x in ("429", "503", "service_unavailable", "high demand", "resource_exhausted", "timeout"))

    async def chat_com_fallback(self, system, message, history):
        client = self._client()
        ultimo = None
        texto_historico = "\n".join(
            f'{x.get("role","user")}: {x.get("content","")[:3000]}'
            for x in history[-12:]
            if isinstance(x.get("content"), str)
        )
        entrada = f"{system}\n\nHISTÓRICO:\n{texto_historico}\n\nUSUÁRIO:\n{message}"
        for model in self.chat_models:
            try:
                inter = await asyncio.to_thread(
                    client.interactions.create,
                    model=model,
                    input=entrada
                )
                texto = getattr(inter, "output_text", None)
                if texto:
                    return texto.strip(), model
                raise RuntimeError("Modelo não retornou texto.")
            except Exception as exc:
                ultimo = exc
                if not self._retryable(exc):
                    break
        raise HTTPException(502, f"Falha nos modelos de chat: {type(ultimo).__name__}: {ultimo}")

    async def analisar_arquivo_com_fallback(self, path: Path, prompt: str):
        client = self._client()
        ultimo = None
        try:
            remoto = await asyncio.to_thread(client.files.upload, file=str(path))
        except Exception as exc:
            raise HTTPException(502, f"Falha no upload para análise: {type(exc).__name__}: {exc}")

        for model in self.file_models:
            try:
                inter = await asyncio.to_thread(
                    client.interactions.create,
                    model=model,
                    input=[
                        {"type": "text", "text": prompt},
                        {"type": "file", "uri": remoto.uri}
                    ]
                )
                texto = getattr(inter, "output_text", None)
                if texto:
                    return texto.strip(), model
                raise RuntimeError("Modelo não retornou análise textual.")
            except Exception as exc:
                ultimo = exc
                if not self._retryable(exc):
                    break
        raise HTTPException(502, f"Falha ao analisar arquivo: {type(ultimo).__name__}: {ultimo}")

    async def gerar_imagem(self, prompt: str, aspect_ratio="1:1"):
        client = self._client()
        ultimo = None
        for model in self.image_models:
            try:
                inter = await asyncio.to_thread(
                    client.interactions.create,
                    model=model,
                    input=prompt,
                    response_format={
                        "type": "image",
                        "mime_type": "image/png",
                        "aspect_ratio": aspect_ratio
                    }
                )
                img = getattr(inter, "output_image", None)
                if not img or not getattr(img, "data", None):
                    raise RuntimeError("Modelo não retornou imagem.")
                destino = self.generated_dir / f"ashley_{uuid.uuid4().hex}.png"
                destino.write_bytes(base64.b64decode(img.data))
                return destino, model
            except Exception as exc:
                ultimo = exc
                if not self._retryable(exc):
                    break
        raise HTTPException(502, f"Falha na geração de imagem: {type(ultimo).__name__}: {ultimo}")

    async def gerar_video(self, prompt: str, aspect_ratio="16:9", resolution="720p"):
        client = self._client()
        ultimo = None
        for model in self.video_models:
            try:
                op = await asyncio.to_thread(
                    client.models.generate_videos,
                    model=model,
                    prompt=prompt,
                    config={
                        "aspect_ratio": aspect_ratio,
                        "resolution": resolution
                    }
                )
                timeout = int(os.getenv("VIDEO_TIMEOUT_SECONDS", "600"))
                passou = 0
                while not op.done and passou < timeout:
                    await asyncio.sleep(10)
                    passou += 10
                    op = await asyncio.to_thread(client.operations.get, op)
                if not op.done:
                    raise TimeoutError("Tempo máximo de geração de vídeo excedido.")

                videos = getattr(getattr(op, "response", None), "generated_videos", None) or []
                if not videos:
                    raise RuntimeError("Veo não retornou vídeo.")
                video = videos[0].video
                destino = self.generated_dir / f"ashley_{uuid.uuid4().hex}.mp4"
                await asyncio.to_thread(client.files.download, file=video)
                # SDK pode retornar bytes no objeto após download.
                if hasattr(video, "video_bytes") and video.video_bytes:
                    destino.write_bytes(video.video_bytes)
                elif hasattr(video, "save"):
                    await asyncio.to_thread(video.save, str(destino))
                else:
                    raise RuntimeError("SDK não disponibilizou bytes do vídeo.")
                return destino, model
            except Exception as exc:
                ultimo = exc
                if not self._retryable(exc):
                    break
        raise HTTPException(502, f"Falha na geração de vídeo: {type(ultimo).__name__}: {ultimo}")

    async def gerar_audio(self, texto: str, persona="Ashley"):
        client = self._client()
        ultimo = None
        for model in self.tts_models:
            try:
                inter = await asyncio.to_thread(
                    client.interactions.create,
                    model=model,
                    input=texto,
                    response_format={"type": "audio", "mime_type": "audio/wav"}
                )
                audio = getattr(inter, "output_audio", None)
                if not audio or not getattr(audio, "data", None):
                    raise RuntimeError("Modelo TTS não retornou áudio.")
                destino = self.generated_dir / f"ashley_{uuid.uuid4().hex}.wav"
                destino.write_bytes(base64.b64decode(audio.data))
                return destino, model
            except Exception as exc:
                ultimo = exc
                if not self._retryable(exc):
                    break
        raise HTTPException(502, f"Falha no TTS: {type(ultimo).__name__}: {ultimo}")
