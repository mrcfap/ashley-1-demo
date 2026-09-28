from pathlib import Path
from app.core.orquestrador import OrquestradorAshley

DB_TESTE = Path("data/ashley_casos_v3_teste.db")
if DB_TESTE.exists():
    DB_TESTE.unlink()

ashley = OrquestradorAshley(
    db_path=str(DB_TESTE),
    user_id=999999
)

testes = [
    "Bom dia Ashley, tudo bem?",
    "Minha empresa está perdendo clientes e eu preciso resolver isso. As vendas caíram nos últimos meses e não sei o que fazer.",
    "Voltando ao assunto daquele problema, qual o próximo passo?",
    "Eu fiz aquilo que combinamos, mas não funcionou e continua ruim."
]

for mensagem in testes:
    analise = ashley.analisar_intencao_caso(mensagem)
    conducao = ashley.conduzir_caso_automaticamente(mensagem, analise)
    print("\\nMENSAGEM:", mensagem)
    print("ANALISE:", analise)
    print("CONDUCAO:", conducao)

print("\\nCASOS FINAIS:")
print(ashley.contexto_casos())
print("\\nBanco de teste:", DB_TESTE)
