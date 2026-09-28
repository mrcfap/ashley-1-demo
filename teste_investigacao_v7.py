import asyncio
from pathlib import Path
from app.core.orquestrador import OrquestradorAshley

DB = Path("data/ashley_investigacao_v7_teste.db")
if DB.exists():
    DB.unlink()

async def main():
    ashley = OrquestradorAshley(db_path=str(DB), user_id=999999)

    abertura = (
        "Minha empresa está perdendo clientes e eu preciso resolver isso. "
        "As vendas caíram nos últimos meses e eu ainda não sei a causa."
    )
    r1 = await ashley.preparar_contexto(abertura)
    caso_id = r1["conducao_caso"]["caso_id"]

    print("1. ABERTURA:", r1["conducao_caso"])
    print("1. V6:", r1["estruturacao_v6"])
    print("1. V7:", r1["investigacao_v7"])

    resposta = (
        "Começou há três meses, depois que aumentamos os preços em 15%."
    )
    # O classificador V2 atual pode considerar a frase conversa normal.
    # A V7 deve ainda assim associá-la ao caso ativo existente.
    r2 = await ashley.preparar_contexto(resposta)

    print("\\n2. RESPOSTA:", resposta)
    print("2. V7:", r2["investigacao_v7"])

    ctx = ashley.contexto_investigacao_caso(caso_id)
    print("\\n3. CONTEXTO INVESTIGATIVO:")
    print(ctx)

    assert "inicio_problema" in ctx["respondidos"]
    assert "mudanca_anterior" in ctx["respondidos"]
    assert ctx["proxima_pergunta"] is not None

    print("\\n4. RESOLUCAO:")
    print(ashley.contexto_resolucao_caso(caso_id))

    print("\\n5. DIAGNOSTICO:")
    print(ashley.diagnostico())

    print("\\nV7 TESTE: PASSOU")
    print("BANCO:", DB)

asyncio.run(main())
