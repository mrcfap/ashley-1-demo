import os
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
app = FastAPI(title="Ashley 1.0 — Gemini")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,https://mrcfap.github.io").split(",") if x.strip()], allow_methods=["POST","GET"], allow_headers=["Content-Type"])
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    persona: str = "Ashley"
    history: list[dict[str,str]] = Field(default_factory=list)

@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/health")
def health():
    return {"status":"ok", "gemini_configured":bool(os.getenv("GEMINI_API_KEY"))}

@app.post("/chat")
async def chat(data: ChatInput):
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise HTTPException(503, "Configure GEMINI_API_KEY no servidor.")
    persona = data.persona if data.persona in ("Ashley", "Ashen") else "Ashley"
    system = f"Você é {persona}, assistente virtual do projeto Ashley 1.0. Responda em português brasileiro com clareza, cordialidade e transparência. Você é uma IA, não uma pessoa. Não afirme ter executado ações externas sem tê-las executado."
    contents = []
    for item in data.history[-12:]:
        if item.get("role") in ("user", "assistant") and isinstance(item.get("content"),str):
            contents.append({"role":"model" if item["role"]=="assistant" else "user", "parts":[{"text":item["content"][:4000]}]})
    contents.append({"role":"user", "parts":[{"text":data.message}]})
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {"systemInstruction":{"parts":[{"text":system}]}, "contents":contents, "generationConfig":{"maxOutputTokens":700}}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, headers={"x-goog-api-key":key,"Content-Type":"application/json"}, json=payload)
        if response.status_code == 429:
            raise HTTPException(429,"Limite temporário de uso do Gemini atingido. Tente novamente mais tarde.")
        if response.status_code in (401,403):
            raise HTTPException(502,"A chave Gemini não foi aceita. Verifique a configuração no servidor.")
        if response.status_code >= 400:
            raise HTTPException(502, f"Gemini retornou HTTP {response.status_code}: {response.json().get('error', {}).get('message', 'Sem detalhes do erro.')}")
        candidates = response.json().get("candidates",[])
        parts = candidates[0].get("content",{}).get("parts",[]) if candidates else []
        answer = "".join(p.get("text","") for p in parts).strip()
        if not answer:
            raise HTTPException(502,"O Gemini não retornou texto para esta solicitação.")
        return {"answer":answer,"persona":persona,"demo":False}
    except httpx.RequestError as exc:
        raise HTTPException(502,"Não foi possível conectar à API Gemini.") from exc
