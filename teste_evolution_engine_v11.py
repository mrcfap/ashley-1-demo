from pathlib import Path
from app.core.orquestrador import OrquestradorAshley

DB=Path("data/ashley_evolution_v11_teste.db")
if DB.exists(): DB.unlink()
a=OrquestradorAshley(db_path=str(DB),user_id=999999)

print("POLITICA:",a.painel_evolucao_v11()["politica"])
for i in range(3):
    a.observar_desempenho_v11(
        "Não funcionou, continua errado.",
        resposta="Vamos revisar a solução."
    )

criadas=a.detectar_e_criar_propostas_v11()
print("PROPOSTAS_AUTOMATICAS:",criadas)
assert len(criadas)>=1
painel=a.painel_evolucao_v11()
print("PAINEL:",painel)
assert painel["ciclos"][0]["estado"]=="PROPOSTA_CRIADA"

bloqueou=False
try:
    a.politica_evolucao_v11(auto_promover_producao=True)
except (PermissionError,ValueError):
    bloqueou=True
assert bloqueou
print("AUTO_PROMOCAO_PRODUCAO: BLOQUEADA")

d=a.diagnostico()
print("DIAGNOSTICO:",d)
assert d["definitive_evolution_engine_v11"] is True
print("\nV11 TESTE: PASSOU")
print("BANCO:",DB)
