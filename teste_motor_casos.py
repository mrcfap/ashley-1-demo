from app.core.orquestrador import OrquestradorAshley

ashley = OrquestradorAshley(
    db_path="data/ashley_memoria.db",
    user_id=1
)

caso = ashley.criar_caso(
    titulo="Teste de acompanhamento",
    descricao="Cliente relatou um problema que precisa de acompanhamento.",
    objetivo="Encontrar uma solução plausível e acompanhar o resultado."
)

print("CASO CRIADO:")
print(caso)

print("\nCONTEXTO DE CASOS:")
print(ashley.contexto_casos())
