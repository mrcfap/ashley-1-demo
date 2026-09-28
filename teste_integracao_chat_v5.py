import asyncio
from pathlib import Path
from app.core.orquestrador import OrquestradorAshley

DB = Path("data/ashley_chat_integracao_teste.db")
if DB.exists():
    DB.unlink()

async def main():
    oq = OrquestradorAshley(db_path=str(DB), user_id=999999)

    mensagem = (
        "Minha empresa está perdendo clientes e eu preciso resolver isso. "
        "As vendas caíram nos últimos meses e não sei o que fazer."
    )

    preparacao = await oq.preparar_contexto(mensagem)

    print("DECISAO:", preparacao["analise_caso"]["decisao"])
    print("CONDUCAO:", preparacao["conducao_caso"])

    caso_id = preparacao["conducao_caso"].get("caso_id")
    print("CASO_ID:", caso_id)
    print("RESOLUCAO:", oq.contexto_resolucao_caso(caso_id))
    print("CICLO:", oq.contexto_ciclo_adaptativo(caso_id))
    print("DIAGNOSTICO:", oq.diagnostico())
    print("BANCO:", DB)

asyncio.run(main())
