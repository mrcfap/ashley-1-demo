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



class AutoProgramarInput(BaseModel):
    user_id: int = Field(default=1, gt=0)


class EvolucaoV11SinalInput(BaseModel):
    user_id: int = Field(default=1, gt=0)
    mensagem: str
    resposta: str | None = None
    erro: str | None = None

class EvolucaoV11PoliticaInput(BaseModel):
    user_id: int = Field(default=1, gt=0)
    auto_observar: bool | None = None
    auto_propor: bool | None = None
    auto_programar_sandbox: bool | None = None
    auto_testar: bool | None = None
    auto_revisar: bool | None = None
    min_ocorrencias: int | None = None
    janela_observacoes: int | None = None
    max_tentativas_correcao: int | None = None

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
        "case_engine": True,
        "adaptive_resolution": True,
        "automatic_case_structuring": True,
        "conversational_investigation": True,
        "governed_self_evolution": True,
        "autonomous_coding_v10": True,
        "continuous_evolution_v11": True,
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

    # Estado operacional do acompanhamento. O usuário não precisa conhecer
    # os detalhes internos para que a Ashley mantenha continuidade.
    analise_caso = preparacao.get("analise_caso") or {}
    conducao_caso = preparacao.get("conducao_caso") or {}
    caso_id = (
        conducao_caso.get("caso_id")
        or analise_caso.get("caso_id")
    )

    caso_estado = None
    resolucao_estado = None
    ciclo_adaptativo = None

    if caso_id:
        try:
            casos = oq.casos_ativos(limite=20)
            caso_estado = next(
                (c for c in casos if c.get("id") == caso_id),
                None
            )
        except Exception:
            caso_estado = None

        try:
            resolucao_estado = oq.contexto_resolucao_caso(caso_id)
        except Exception:
            resolucao_estado = None

        try:
            ciclo_adaptativo = oq.contexto_ciclo_adaptativo(caso_id)
        except Exception:
            ciclo_adaptativo = None

    return {
        "answer": answer,
        "persona": persona,
        "user_id": data.user_id,
        "model": model,
        "memory_enabled": True,
        "relational_memory_used": preparacao.get("memoria_relacional_usada", False),
        "web_used": preparacao.get("web_usada", False),
        "web_success": resultado_web.get("sucesso", False),
        "web_results": len(resultado_web.get("dados", [])),
        "case_engine": {
            "enabled": True,
            "decision": analise_caso.get("decisao"),
            "confidence": analise_caso.get("confianca"),
            "case_id": caso_id,
            "conduction": conducao_caso.get("acao"),
            "case": caso_estado,
            "resolution": resolucao_estado,
            "adaptive_cycle": ciclo_adaptativo,
            "automatic_structuring": preparacao.get("estruturacao_v6"),
            "conversational_investigation": preparacao.get("investigacao_v7")
        }
    }


@app.get("/casos/{user_id}")
def listar_casos_usuario(user_id: int, incluir_resolvidos: bool = False):
    if user_id <= 0:
        raise HTTPException(422, "user_id deve ser maior que zero.")

    oq = orquestrador(user_id)

    if incluir_resolvidos:
        casos = oq.motor_casos.listar_casos(
            user_id=user_id,
            incluir_resolvidos=True,
            limite=50
        )
    else:
        casos = oq.casos_ativos(limite=50)

    return {
        "user_id": user_id,
        "quantidade": len(casos),
        "casos": casos
    }


@app.get("/casos/{user_id}/{caso_id}")
def detalhe_caso_usuario(user_id: int, caso_id: int):
    if user_id <= 0 or caso_id <= 0:
        raise HTTPException(422, "user_id e caso_id devem ser maiores que zero.")

    oq = orquestrador(user_id)
    caso = oq.motor_casos.obter_caso(caso_id, user_id)

    if not caso:
        raise HTTPException(404, "Caso não encontrado.")

    return {
        "user_id": user_id,
        "caso": caso,
        "resolucao": oq.contexto_resolucao_caso(caso_id),
        "ciclo_adaptativo": oq.contexto_ciclo_adaptativo(caso_id)
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


# ==================================================
# AUTOEVOLUÇÃO GOVERNADA V8
# ==================================================

class EvolucaoSinalInput(BaseModel):
    user_id: int
    categoria: str
    descricao: str
    severidade: int = 1
    componente: str = "orquestrador"
    sugestao: str | None = None
    risco: str = "MEDIO"
    titulo: str | None = None


class EvolucaoTesteInput(BaseModel):
    user_id: int
    resultado: str
    passou: bool = False
    metricas: dict = {}


@app.get("/evolucao/{user_id}")
def evolucao_painel(user_id: int):
    return orquestrador(user_id).painel_autoevolucao()


@app.post("/evolucao/sinal")
def evolucao_sinal(data: EvolucaoSinalInput):
    oq = orquestrador(data.user_id)
    propostas = oq.registrar_sinal_evolucao(
        categoria=data.categoria,
        descricao=data.descricao,
        severidade=data.severidade,
        componente=data.componente,
        sugestao=data.sugestao,
        risco=data.risco,
        titulo=data.titulo
    )
    return {"ok": True, "propostas_criadas": propostas}


@app.post("/evolucao/{proposta_id}/aprovar")
def evolucao_aprovar(proposta_id: str, user_id: int):
    return orquestrador(user_id).aprovar_melhoria(proposta_id)


@app.post("/evolucao/{proposta_id}/teste")
def evolucao_teste(proposta_id: str, data: EvolucaoTesteInput):
    return orquestrador(data.user_id).registrar_teste_melhoria(
        proposta_id=proposta_id,
        resultado=data.resultado,
        metricas=data.metricas,
        passou=data.passou
    )


@app.post("/evolucao/{proposta_id}/autoprogramar")
async def autoprogramar_melhoria(proposta_id: str, data: AutoProgramarInput):
    """
    V10: a própria Ashley lê a proposta e trechos do próprio código,
    pede ao modelo uma alteração candidata e a testa em sandbox.
    Não promove automaticamente para produção.
    """
    oq = orquestrador(data.user_id)
    try:
        prompt = oq.prompt_autoprogramacao(proposta_id)
        system = (
            "Você atua como engenheiro de software interno da Ashley 1.0. "
            "Siga rigorosamente as regras do prompt. Produza somente JSON válido. "
            "Nunca remova controles de segurança, aprovação, sandbox ou rollback."
        )
        resposta, modelo = await gemini.chat_com_fallback(
            system=system,
            message=prompt,
            history=[]
        )
        resultado = oq.aplicar_autoprogramacao(proposta_id, resposta)
        resultado["modelo"] = modelo
        return resultado
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha V10: {e}")


@app.get("/evolucao-v11/{user_id}")
async def painel_evolucao_v11(user_id: int):
    return orquestrador(user_id).painel_evolucao_v11()

@app.post("/evolucao-v11/observar")
async def observar_evolucao_v11(data: EvolucaoV11SinalInput):
    oq=orquestrador(data.user_id)
    sinais=oq.observar_desempenho_v11(
        data.mensagem, resposta=data.resposta, erro=data.erro
    )
    propostas=oq.detectar_e_criar_propostas_v11()
    return {"sinais":sinais,"propostas_criadas":propostas,
            "painel":oq.painel_evolucao_v11()}

@app.post("/evolucao-v11/politica")
async def politica_evolucao_v11(data: EvolucaoV11PoliticaInput):
    oq=orquestrador(data.user_id)
    mudancas=data.model_dump(exclude={"user_id"},exclude_none=True)
    try:
        return oq.politica_evolucao_v11(**mudancas)
    except PermissionError as e:
        raise HTTPException(status_code=403,detail=str(e))
