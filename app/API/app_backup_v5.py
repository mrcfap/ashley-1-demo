import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.orquestrador import OrquestradorAshley
from app.services.gemini_service import GeminiService
from app.memory.memoria_longa import MemoriaLongoPrazo

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
DATA = ROOT / "data"
UPLOADS = DATA / "uploads"
GENERATED = DATA / "generated"
DB = DATA / "ashley.db"

for pasta in (DATA, UPLOADS, GENERATED):
    pasta.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")

app = FastAPI(
    title="Ashley 1.0 — Núcleo Multimodal",
    version="1.0.0"
)

origens = [x.strip() for x in os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000,https://mrcfap.github.io"
).split(",") if x.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

if (FRONTEND / "static").exists():
    app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")

gemini = GeminiService(root=ROOT, generated_dir=GENERATED)
memoria_longa = MemoriaLongoPrazo(DB)


class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    persona: str = "Ashley"
    user_id: int = Field(default=1, gt=0)
    history: list[dict[str, str]] = Field(default_factory=list)


class WebInput(BaseModel):
    consulta: str = Field(min_length=2, max_length=1000)
    user_id: int = Field(default=1, gt=0)


class ImagemInput(BaseModel):
    prompt: str = Field(min_length=2, max_length=4000)
    user_id: int = Field(default=1, gt=0)
    aspect_ratio: str = "1:1"


class VideoInput(BaseModel):
    prompt: str = Field(min_length=2, max_length=4000)
    user_id: int = Field(default=1, gt=0)
    aspect_ratio: str = "16:9"
    resolution: str = "720p"


class MemoriaInput(BaseModel):
    categoria: str = Field(min_length=1, max_length=80)
    chave: str = Field(min_length=1, max_length=120)
    conteudo: str = Field(min_length=1, max_length=12000)
    importancia: float = Field(default=0.7, ge=0, le=1)
    permanencia: float = Field(default=0.8, ge=0, le=1)


def orquestrador(user_id: int) -> OrquestradorAshley:
    return OrquestradorAshley(db_path=DB, user_id=user_id)


@app.get("/")
def home():
    index = FRONTEND / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"status": "ok", "produto": "Ashley 1.0"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "chat": True,
        "web": True,
        "long_term_memory": True,
        "file_analysis": True,
        "image_generation": True,
        "video_generation": True,
        "generated_files": True,
        "tts": True,
        "models": gemini.modelos_publicos()
    }


@app.get("/diagnostico/usuario/{user_id}")
def diagnostico_usuario(user_id: int):
    if user_id <= 0:
        raise HTTPException(422, "user_id deve ser maior que zero.")
    oq = orquestrador(user_id)
    return {
        "status": "ok",
        "user_id": user_id,
        "orquestrador": oq.diagnostico(),
        "memoria_longa": memoria_longa.estatisticas(user_id),
        "contexto_relacional": oq.contexto_relacional("diagnóstico", limite=5)
    }


@app.post("/memoria/guardar")
def guardar_memoria(data: MemoriaInput, user_id: int = 1):
    if user_id <= 0:
        raise HTTPException(422, "user_id deve ser maior que zero.")
    return memoria_longa.guardar(
        user_id=user_id,
        categoria=data.categoria,
        chave=data.chave,
        conteudo=data.conteudo,
        importancia=data.importancia,
        permanencia=data.permanencia
    )


@app.get("/memoria/buscar/{user_id}")
def buscar_memoria(user_id: int, q: str = ""):
    if user_id <= 0:
        raise HTTPException(422, "user_id deve ser maior que zero.")
    return {"user_id": user_id, "memorias": memoria_longa.buscar(user_id, q, limite=20)}


@app.post("/web/pesquisar")
async def pesquisar_web(data: WebInput):
    oq = orquestrador(data.user_id)
    return await oq.executar_busca_web(data.consulta)


@app.post("/chat")
async def chat(data: ChatInput):
    persona = data.persona if data.persona in ("Ashley", "Ashen") else "Ashley"
    oq = orquestrador(data.user_id)
    preparacao = await oq.preparar_contexto(data.message)
    mem = memoria_longa.contexto(data.user_id, data.message, limite=8)

    system = f"""
Você é {persona}, IA conversacional do projeto Ashley 1.0.
Responda prioritariamente em português brasileiro.
Seja natural, clara, cordial e direta. Não finja ser humana.
Não invente memórias, pesquisas, arquivos, imagens, vídeos ou ações.
Use resultados reais de ferramentas quando existirem.
A mensagem atual do usuário prevalece sobre memória antiga conflitante.

MEMÓRIA PERSISTENTE DE LONGO PRAZO:
{mem}

CONTEXTO DO ORQUESTRADOR:
{preparacao["contexto"]}
"""

    answer, model = await gemini.chat_com_fallback(
        system=system,
        message=data.message,
        history=data.history
    )

    memoria_longa.registrar_interacao(
        user_id=data.user_id,
        entrada=data.message,
        resposta=answer
    )

    resultado_web = preparacao.get("resultado_web") or {}
    return {
        "answer": answer,
        "persona": persona,
        "user_id": data.user_id,
        "model": model,
        "memory_enabled": True,
        "relational_memory_used": preparacao.get("memoria_relacional_usada", False),
        "web_used": preparacao.get("web_usada", False),
        "web_success": resultado_web.get("sucesso", False),
        "web_results": len(resultado_web.get("dados", []))
    }


@app.post("/arquivo/analisar")
async def analisar_arquivo(
    arquivo: UploadFile = File(...),
    prompt: str = Form("Analise este arquivo e apresente os pontos principais."),
    user_id: int = Form(1)
):
    if user_id <= 0:
        raise HTTPException(422, "user_id deve ser maior que zero.")

    nome = Path(arquivo.filename or "arquivo").name
    destino = UPLOADS / f"{uuid.uuid4().hex}_{nome}"
    limite = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

    total = 0
    with destino.open("wb") as f:
        while chunk := await arquivo.read(1024 * 1024):
            total += len(chunk)
            if total > limite:
                f.close()
                destino.unlink(missing_ok=True)
                raise HTTPException(413, f"Arquivo excede {os.getenv('MAX_UPLOAD_MB','50')} MB.")
            f.write(chunk)

    try:
        texto, model = await gemini.analisar_arquivo_com_fallback(destino, prompt)
        memoria_longa.registrar_evento(
            user_id, "arquivo_analisado", nome,
            f"Arquivo analisado: {nome}. Solicitação: {prompt}"
        )
        return {
            "sucesso": True,
            "arquivo": nome,
            "mime_type": arquivo.content_type,
            "bytes": total,
            "model": model,
            "analise": texto
        }
    finally:
        if os.getenv("KEEP_UPLOADS", "0") != "1":
            destino.unlink(missing_ok=True)


@app.post("/imagem/gerar")
async def gerar_imagem(data: ImagemInput):
    arquivo, model = await gemini.gerar_imagem(
        data.prompt, aspect_ratio=data.aspect_ratio
    )
    memoria_longa.registrar_evento(
        data.user_id, "imagem_gerada", arquivo.name, data.prompt
    )
    return {
        "sucesso": True,
        "model": model,
        "arquivo": arquivo.name,
        "url": f"/gerados/{arquivo.name}"
    }


@app.post("/video/gerar")
async def gerar_video(data: VideoInput):
    arquivo, model = await gemini.gerar_video(
        prompt=data.prompt,
        aspect_ratio=data.aspect_ratio,
        resolution=data.resolution
    )
    memoria_longa.registrar_evento(
        data.user_id, "video_gerado", arquivo.name, data.prompt
    )
    return {
        "sucesso": True,
        "model": model,
        "arquivo": arquivo.name,
        "url": f"/gerados/{arquivo.name}"
    }


@app.get("/gerados/{nome}")
def baixar_gerado(nome: str):
    seguro = Path(nome).name
    arquivo = GENERATED / seguro
    if not arquivo.exists() or not arquivo.is_file():
        raise HTTPException(404, "Arquivo gerado não encontrado.")
    return FileResponse(arquivo)


@app.post("/tts")
async def tts(texto: str = Form(...), persona: str = Form("Ashley")):
    arquivo, model = await gemini.gerar_audio(texto, persona)
    return FileResponse(
        arquivo,
        media_type="audio/wav",
        filename=arquivo.name,
        headers={"X-Ashley-Model": model}
    )
