import os
import base64
import asyncio
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import types
import wave
import io

load_dotenv()


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
        self.tts_models = self._lista("GEMINI_TTS_MODELS", "gemini-2.5-flash-preview-tts")
        self.tts_voices = {"Ashley": os.getenv("ASHLEY_TTS_VOICE", "Kore"), "Ashen": os.getenv("ASHEN_TTS_VOICE", "Charon")}

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
        return any(
            x in s
            for x in (
                "429",
                "503",
                "service_unavailable",
                "high demand",
                "resource_exhausted",
                "rate limit",
                "ratelimit",
                "too_many_requests",
                "timeout",
            )
        )

    async def chat_com_fallback(self, system, message, history):
        """Tenta cada modelo uma vez; reporta limites sem expor credenciais."""
        client = self._client()
        texto_historico = "\n".join(
            f'{x.get("role", "user")}: {x.get("content", "")[:3000]}'
            for x in history[-12:]
            if isinstance(x, dict) and isinstance(x.get("content"), str)
        )
        entrada = f"{system}\n\nHISTÓRICO:\n{texto_historico}\n\nUSUÁRIO:\n{message}"
        timeout_modelo = max(8, min(45, int(os.getenv("ASHLEY_MODEL_TIMEOUT_SECONDS", "25"))))
        falhas = []
        for model in self.chat_models:
            try:
                inter = await asyncio.wait_for(
                    asyncio.to_thread(client.interactions.create, model=model, input=entrada),
                    timeout=timeout_modelo,
                )
                texto = getattr(inter, "output_text", None)
                if texto and texto.strip():
                    return texto.strip(), model
                falhas.append("empty")
            except asyncio.TimeoutError:
                falhas.append("timeout")
            except Exception as exc:
                msg = str(exc).lower()
                if any(x in msg for x in ("429", "resource_exhausted", "rate limit", "too_many_requests", "quota")):
                    falhas.append("quota")
                elif any(x in msg for x in ("404", "not_found", "not found", "unsupported")):
                    falhas.append("model")
                elif self._retryable(exc) or any(x in msg for x in ("502", "504", "bad gateway")):
                    falhas.append("temporary")
                else:
                    raise HTTPException(502, "Falha ao consultar o modelo de IA. Consulte os registros do servidor.") from exc
        if falhas and all(x == "quota" for x in falhas):
            raise HTTPException(429, "Cota dos modelos de IA esgotada. Aguarde a renovação ou configure outra cota.")
        if "timeout" in falhas:
            raise HTTPException(504, "Os modelos de IA não responderam dentro do tempo configurado.")
        if "quota" in falhas:
            raise HTTPException(503, "Alguns modelos atingiram a cota e os demais estão indisponíveis.")
        raise HTTPException(503, "Modelos de IA indisponíveis. Verifique a configuração e tente mais tarde.")

    async def analisar_arquivo_com_fallback(self, path: Path, prompt: str):
        client = self._client()
        ultimo = None
        try:
            remoto = await asyncio.to_thread(client.files.upload, file=str(path))
        except Exception as exc:
            raise HTTPException(502, f"Falha no upload para análise: {type(exc).__name__}: {exc}")

        for model in self.file_models:
            try:
                # Files API: o arquivo enviado é um objeto File aceito em contents.
                # Não usar "type: file" em interactions.create: formato inválido.
                resposta = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=[prompt, remoto],
                )
                texto = getattr(resposta, "text", None)
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

    async def gerar_audio_alternativo(self, texto: str, persona: str = "Ashley"):
        """Segunda voz neural: Microsoft Edge online, independente da cota Gemini."""
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("Dependência edge-tts ausente. Execute: py -m pip install -r requirements.txt") from exc
        voz = os.getenv("ASHLEY_EDGE_VOICE", "pt-BR-FranciscaNeural") if persona == "Ashley" else os.getenv("ASHEN_EDGE_VOICE", "pt-BR-AntonioNeural")
        destino = self.generated_dir / f"ashley_{uuid.uuid4().hex}.mp3"
        try:
            await edge_tts.Communicate(texto, voice=voz).save(str(destino))
            if not destino.exists() or destino.stat().st_size < 100:
                raise RuntimeError("Serviço neural alternativo não retornou áudio.")
            return destino, "edge-neural"
        except Exception:
            destino.unlink(missing_ok=True)
            raise

    async def gerar_audio(self, texto: str, persona="Ashley"):
        """Gera fala neural Gemini com vozes distintas, devolvendo WAV válido."""
        texto = (texto or "").strip()
        if not texto:
            raise HTTPException(422, "Informe o texto a ser falado.")
        if len(texto) > 4000:
            raise HTTPException(422, "Texto de voz muito longo (máximo 4000 caracteres).")
        persona = persona if persona in self.tts_voices else "Ashley"
        voz = self.tts_voices[persona]
        estilo = ("Fale em português brasileiro com voz feminina, acolhedora, "
                  "natural e expressiva, com pausas suaves." if persona == "Ashley" else
                  "Fale em português brasileiro com voz masculina, calma, "
                  "natural e expressiva, com pausas suaves.")
        client = self._client()
        ultimo = None
        for model in self.tts_models:
            try:
                resposta = await asyncio.wait_for(asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=f"{estilo}\n\nTexto para falar exatamente:\n{texto}",
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voz)
                            )
                        ),
                    ),
                ), timeout=max(3, int(os.getenv("ASHLEY_GEMINI_TTS_ATTEMPT_TIMEOUT", "9"))))
                partes = getattr(getattr(resposta, "candidates", [None])[0], "content", None)
                partes = getattr(partes, "parts", []) or []
                audio = next((getattr(p, "inline_data", None) for p in partes
                              if getattr(p, "inline_data", None) is not None), None)
                if audio is None or not getattr(audio, "data", None):
                    raise RuntimeError("Modelo TTS não retornou áudio.")
                raw = audio.data
                if isinstance(raw, str):
                    raw = base64.b64decode(raw)
                mime = (getattr(audio, "mime_type", "") or "").lower()
                if raw[:4] == b"RIFF":
                    wav_bytes = raw
                elif "pcm" in mime or not mime or "audio/l16" in mime:
                    # Gemini TTS retorna PCM mono 16 bits, geralmente 24 kHz.
                    sample_rate = 24000
                    match = __import__("re").search(r"rate=(\d+)", mime)
                    if match:
                        sample_rate = int(match.group(1))
                    buffer = io.BytesIO()
                    with wave.open(buffer, "wb") as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(sample_rate)
                        wav.writeframes(raw)
                    wav_bytes = buffer.getvalue()
                else:
                    raise RuntimeError(f"Formato de áudio inesperado: {mime}")
                destino = self.generated_dir / f"ashley_{uuid.uuid4().hex}.wav"
                destino.write_bytes(wav_bytes)
                return destino, model
            except Exception as exc:
                ultimo = exc
                if not self._retryable(exc):
                    break
        raise HTTPException(502, f"Voz neural indisponível: {type(ultimo).__name__}. Verifique modelo, cota e credenciais.")
