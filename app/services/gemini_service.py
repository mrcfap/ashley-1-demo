from app.services.idioma import voz_edge
import os
import logging
import base64
import asyncio
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import errors, types
import wave
import io

load_dotenv()

OMNI_VIDEO_MODEL = "gemini-omni-1.2-flash"
RETIRED_VIDEO_MODELS = {
    "veo-3.1-generate-preview",
    "veo-3.1-fast-generate-preview",
    "veo-3.1-lite-generate-preview",
}


class GeminiService:
    def __init__(self, root: Path, generated_dir: Path):
        self.root = root
        self.generated_dir = generated_dir
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.key = os.getenv("GEMINI_API_KEY", "").strip()
        self.chat_models = self._lista("GEMINI_CHAT_MODELS", "gemini-3.8-flash,gemini-2.5-flash")
        self.file_models = self._lista("GEMINI_FILE_MODELS", "gemini-3.8-flash,gemini-2.5-flash")
        self.image_models = self._lista("GEMINI_IMAGE_MODELS", "gemini-3.1-flash-image,gemini-2.5-flash-image")
        video_models = self._lista("GEMINI_VIDEO_MODELS", OMNI_VIDEO_MODEL) or [OMNI_VIDEO_MODEL]
        self.video_models = list(dict.fromkeys(
            OMNI_VIDEO_MODEL if model.removeprefix("models/") in RETIRED_VIDEO_MODELS else model
            for model in video_models
        ))
        self.music_model = os.getenv("GEMINI_MUSIC_MODEL", "lyria-3.5").strip()
        self.tts_models = self._lista("GEMINI_TTS_MODELS", "gemini-2.5-flash-preview-tts")
        self.tts_voices = {"Ashley": os.getenv("ASHLEY_TTS_VOICE", "Kore"), "Ashen": os.getenv("ASHEN_TTS_VOICE", "Charon")}

    def _lista(self, nome, padrao):
        return [x.strip() for x in os.getenv(nome, padrao).split(",") if x.strip()]

    @property
    def configured(self):
        return bool(self.key and self.key != "sua_chave_gemini_aqui")

    def _client(self, *, http_options=None):
        if not self.configured:
            raise HTTPException(503, "Configure GEMINI_API_KEY no servidor.")
        return genai.Client(api_key=self.key, http_options=http_options)

    def modelos_publicos(self):
        return {
            "chat": self.chat_models,
            "files": self.file_models,
            "image": self.image_models,
            "video": self.video_models,
            "music": [self.music_model],
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
        logger = logging.getLogger(__name__)
        for model in self.chat_models:
            try:
                inter = await asyncio.wait_for(
                    asyncio.to_thread(client.models.generate_content, model=model, contents=entrada),
                    timeout=timeout_modelo,
                )
                texto = getattr(inter, "text", None)
                if texto and texto.strip():
                    return texto.strip(), model
                falhas.append("empty")
            except asyncio.TimeoutError:
                logger.warning("GEMINI_CHAT model=%s failure=timeout", model)
                falhas.append("timeout")
            except Exception as exc:
                status = getattr(exc, "code", None)
                logger.warning("GEMINI_CHAT model=%s failure_type=%s status=%s", model, type(exc).__name__, status)
                msg = str(exc).lower()
                if any(x in msg for x in ("429", "resource_exhausted", "rate limit", "too_many_requests", "quota")):
                    falhas.append("quota")
                elif any(x in msg for x in ("404", "not_found", "not found", "unsupported")):
                    falhas.append("model")
                elif self._retryable(exc) or any(x in msg for x in ("502", "504", "bad gateway")):
                    falhas.append("temporary")
                else:
                    raise HTTPException(502, "Falha ao consultar o modelo de IA. Consulte os registros do servidor.") from exc
        if falhas and all(x == "model" for x in falhas):
            try:
                def _discover_models():
                    matches = []
                    for item in client.models.list():
                        actions = getattr(item, "supported_actions", None) or []
                        name = getattr(item, "name", "") or ""
                        if "generateContent" in actions and "gemini" in name.lower():
                            matches.append(name.removeprefix("models/"))
                        if len(matches) >= 30:
                            break
                    return matches
                available = await asyncio.wait_for(asyncio.to_thread(_discover_models), timeout=15)
                logger.warning("GEMINI_CHAT available_generate_content_models=%s", available)
                preferred = [x for x in available if "flash" in x.lower() and not any(t in x.lower() for t in ("image", "nano", "omni", "tts"))] + [x for x in available if not any(t in x.lower() for t in ("image", "nano", "omni", "tts"))]
                for model in preferred[:8]:
                    if model in self.chat_models:
                        continue
                    try:
                        response = await asyncio.wait_for(asyncio.to_thread(client.models.generate_content, model=model, contents=entrada), timeout=timeout_modelo)
                        result = getattr(response, "text", None)
                        if result and result.strip():
                            logger.info("GEMINI_CHAT discovered_model_success=%s", model)
                            return result.strip(), model
                    except Exception as exc:
                        logger.warning("GEMINI_CHAT discovered_model=%s failure_type=%s status=%s", model, type(exc).__name__, getattr(exc, "code", None))
            except Exception as exc:
                logger.warning("GEMINI_CHAT model_discovery_failure_type=%s status=%s", type(exc).__name__, getattr(exc, "code", None))
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

    @staticmethod
    def _media_error(exc, tipo):
        code = getattr(exc, "code", None)
        if isinstance(exc, TimeoutError):
            return HTTPException(504, f"Tempo limite ao gerar {tipo}.")
        if code == 429:
            return HTTPException(429, f"Cota de {tipo} atingida no Google. Verifique o limite da conta.")
        if code in (401, 403) or getattr(exc, "status", "") == "UNAUTHENTICATED":
            return HTTPException(503, f"O Google negou acesso à geração de {tipo}. Verifique a chave e o plano.")
        if code in (400, 404):
            return HTTPException(502, f"O Google rejeitou o pedido de {tipo}. Verifique o modelo e os parâmetros.")
        return HTTPException(502, f"O provedor não retornou {tipo} utilizável.")

    def _save_media(self, raw, suffix):
        destino = self.generated_dir / f"ashley_{uuid.uuid4().hex}.{suffix}"
        try:
            destino.write_bytes(raw)
        except OSError:
            destino.unlink(missing_ok=True)
            raise
        return destino

    async def gerar_imagem(self, prompt: str, aspect_ratio="1:1"):
        client = self._client()
        ultimo = None
        try:
            for model in self.image_models:
                try:
                    async with asyncio.timeout(75):
                        response = await client.aio.models.generate_content(
                            model=model, contents=prompt,
                            config=types.GenerateContentConfig(
                                response_modalities=["TEXT", "IMAGE"],
                                image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                            ),
                        )
                    for candidate in response.candidates or []:
                        for part in getattr(candidate.content, "parts", None) or []:
                            blob = part.inline_data
                            raw = blob.data if blob else None
                            if raw and raw.startswith(b"\x89PNG\r\n\x1a\n"):
                                return self._save_media(raw, "png"), model
                            if raw and raw.startswith(b"\xff\xd8\xff"):
                                return self._save_media(raw, "jpg"), model
                            if raw and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
                                return self._save_media(raw, "webp"), model
                    raise HTTPException(422, "O modelo não retornou uma imagem. Tente reformular o pedido.")
                except errors.APIError as exc:
                    ultimo = exc
                    if exc.code not in (400, 403, 404, 429, 503):
                        break
                except TimeoutError as exc:
                    ultimo = exc
                    break
        finally:
            await client.aio.aclose()
            client.close()
        raise self._media_error(ultimo, "imagem")

    async def gerar_video(self, prompt: str, aspect_ratio="16:9", resolution="720p"):
        timeout = max(15, int(os.getenv("VIDEO_TIMEOUT_SECONDS", "600")))
        client = self._client(http_options=types.HttpOptions(api_version="v1beta", timeout=timeout * 1000))
        formato = {
            "type": "video", "aspect_ratio": aspect_ratio,
            "resolution": resolution, "duration": "8s",
        }
        ultimo = None
        try:
            async with asyncio.timeout(timeout):
                for model in self.video_models:
                    try:
                        interaction = await client.aio.interactions.create(
                            model=model, input=prompt, response_format=formato,
                        )
                    except errors.APIError as exc:
                        ultimo = exc
                        if exc.code in (400, 403, 404, 429):
                            continue
                        raise
                    video = getattr(interaction, "output_video", None)
                    dados = getattr(video, "data", None)
                    if not dados:
                        raise HTTPException(502, "O Gemini Omni não retornou vídeo. Verifique as condições do pedido.")
                    try:
                        raw = base64.b64decode(dados, validate=True)
                    except (ValueError, TypeError):
                        raw = b""
                    if len(raw) < 12 or raw[4:8] != b"ftyp":
                        raise HTTPException(502, "O Gemini Omni não retornou um MP4 válido.")
                    return self._save_media(raw, "mp4"), model
        except (errors.APIError, TimeoutError) as exc:
            ultimo = exc
        finally:
            await client.aio.aclose()
            client.close()
        raise self._media_error(ultimo, "vídeo")

    async def gerar_musica(self, prompt: str):
        client = self._client()
        try:
            async with asyncio.timeout(240):
                interaction = await client.aio.interactions.create(
                    model=self.music_model, input=prompt,
                )
            audio = getattr(interaction, "output_audio", None)
            raw = getattr(audio, "data", None)
            if isinstance(raw, str):
                try:
                    raw = base64.b64decode(raw, validate=True)
                except ValueError:
                    raw = None
            if not raw or not (raw.startswith(b"ID3") or (
                len(raw) > 4 and raw[0] == 0xff and raw[1] & 0xe0 == 0xe0
            )):
                raise HTTPException(502, "O Lyria não retornou áudio MP3 válido.")
            return self._save_media(raw, "mp3"), self.music_model
        except (errors.APIError, TimeoutError) as exc:
            raise self._media_error(exc, "música") from exc
        finally:
            await client.aio.aclose()
            client.close()

    async def gerar_audio_alternativo(self, texto: str, persona: str = "Ashley", idioma: str = "pt-BR"):
        """Segunda voz neural: Microsoft Edge online, independente da cota Gemini."""
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("Dependência edge-tts ausente. Execute: py -m pip install -r requirements.txt") from exc
        voz = os.getenv("ASHLEY_EDGE_VOICE", "pt-BR-FranciscaNeural") if persona == "Ashley" else os.getenv("ASHEN_EDGE_VOICE", "pt-BR-AntonioNeural")
        if idioma != "pt-BR":
            voz = voz_edge(idioma, persona)
        destino = self.generated_dir / f"ashley_{uuid.uuid4().hex}.mp3"
        try:
            await edge_tts.Communicate(texto, voice=voz).save(str(destino))
            if not destino.exists() or destino.stat().st_size < 100:
                raise RuntimeError("Serviço neural alternativo não retornou áudio.")
            return destino, "edge-neural"
        except (Exception, asyncio.CancelledError):
            destino.unlink(missing_ok=True)
            raise

    async def gerar_audio(self, texto: str, persona="Ashley", idioma: str = "pt-BR"):
        """Gera fala neural Gemini com vozes distintas, devolvendo WAV válido."""
        texto = (texto or "").strip()
        if not texto:
            raise HTTPException(422, "Informe o texto a ser falado.")
        if len(texto) > 4000:
            raise HTTPException(422, "Texto de voz muito longo (máximo 4000 caracteres).")
        persona = persona if persona in self.tts_voices else "Ashley"
        voz = self.tts_voices[persona]
        client = self._client()
        ultimo = None
        for model in self.tts_models:
            try:
                resposta = await asyncio.wait_for(asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=texto,
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
