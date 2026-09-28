import asyncio
from pathlib import Path
from app.core.orquestrador import OrquestradorAshley

DB = Path("data/ashley_conducao_v6_teste.db")
if DB.exists():
    DB.unlink()

async def main():
    ashley = OrquestradorAshley(db_path=str(DB), user_id=999999)

    mensagem = (
        "Minha empresa está perdendo clientes e eu preciso resolver isso. "
        "As vendas caíram nos últimos meses e eu ainda não sei a causa."
    )

    preparacao = await ashley.preparar_contexto(mensagem)
    caso_id = preparacao["conducao_caso"]["caso_id"]

    print("DECISAO:", preparacao["analise_caso"]["decisao"])
    print("CONDUCAO:", preparacao["conducao_caso"])
    print("ESTRUTURACAO V6:", preparacao["estruturacao_v6"])
    print("\\nRESOLUCAO:")
    print(ashley.contexto_resolucao_caso(caso_id))
    print("\\nDIAGNOSTICO:")
    print(ashley.diagnostico())
    print("\\nBANCO:", DB)

    ctx = ashley.contexto_resolucao_caso(caso_id)
    assert ctx["diagnostico"] is not None
    assert len(ctx["hipoteses"]) >= 1
    assert ctx["plano_ativo"] is not None
    assert ctx["proxima_acao"] is not None
    assert ctx["proxima_acao"]["responsavel"] == "ashley"
    print("\\nV6 TESTE: PASSOU")

asyncio.run(main())
