from pathlib import Path
from app.core.orquestrador import OrquestradorAshley

DB = Path("data/ashley_autoevolucao_v8_teste.db")
if DB.exists():
    DB.unlink()

ashley = OrquestradorAshley(db_path=str(DB), user_id=999999)

propostas = ashley.registrar_sinal_evolucao(
    categoria="qualidade_resposta",
    descricao="A investigação repete perguntas quando a mesma informação aparece com redação diferente.",
    severidade=3,
    componente="orquestrador",
    sugestao="Adicionar deduplicação semântica antes de selecionar a próxima pergunta.",
    risco="MEDIO",
    titulo="Evitar perguntas repetidas"
)

assert len(propostas) == 1
p = propostas[0]
print("PROPOSTA:", p)

assert p["estado"] == "AGUARDANDO_APROVACAO"
assert p["requer_aprovacao"] == 1

aprovada = ashley.aprovar_melhoria(p["id"])
print("\nAPROVADA:", aprovada)
assert aprovada["estado"] == "APROVADA"

teste = ashley.registrar_teste_melhoria(
    proposta_id=p["id"],
    resultado="Teste em sandbox: 20 cenários, sem regressões e redução de repetição.",
    metricas={"cenarios": 20, "regressoes": 0, "repeticoes_antes": 7, "repeticoes_depois": 1},
    passou=True
)
print("\nTESTE:", teste)

painel = ashley.painel_autoevolucao()
print("\nPAINEL:", painel)
print("\nDIAGNOSTICO:", ashley.diagnostico())

assert ashley.diagnostico()["autoevolucao_governada_v8"] is True
print("\nV8 TESTE: PASSOU")
print("BANCO:", DB)
