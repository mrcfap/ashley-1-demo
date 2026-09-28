from app.core.orquestrador import OrquestradorAshley

ashley = OrquestradorAshley(
    db_path="data/ashley_memoria.db",
    user_id=1
)

testes = [
    "Bom dia Ashley, tudo bem?",
    "Minha empresa está perdendo clientes e eu preciso resolver isso. As vendas caíram nos últimos meses e não sei o que fazer.",
    "Voltando ao assunto daquele problema, qual o próximo passo?",
    "Eu fiz aquilo que combinamos, mas não funcionou e continua ruim."
]

for mensagem in testes:
    print("\nMENSAGEM:", mensagem)
    print(ashley.analisar_intencao_caso(mensagem))
