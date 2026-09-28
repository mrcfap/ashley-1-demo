from pathlib import Path
from app.core.orquestrador import OrquestradorAshley

DB = Path("data/ashley_resolucao_v4_teste.db")
if DB.exists():
    DB.unlink()

ashley = OrquestradorAshley(db_path=str(DB), user_id=999999)

mensagem = (
    "Minha empresa está perdendo clientes e eu preciso resolver isso. "
    "As vendas caíram nos últimos meses e não sei o que fazer."
)

analise = ashley.analisar_intencao_caso(mensagem)
conducao = ashley.conduzir_caso_automaticamente(mensagem, analise)
caso_id = conducao["caso_id"]

print("1. CONDUCAO:", conducao)

diag_id = ashley.registrar_diagnostico_caso(
    caso_id,
    resumo="Queda de clientes e vendas; causa ainda não comprovada.",
    fatos=["Clientes diminuíram", "Vendas caíram nos últimos meses"],
    informacoes_faltantes=[
        "Taxa de perda de clientes",
        "Motivos de cancelamento",
        "Mudanças recentes em preço, produto ou atendimento"
    ]
)
print("2. DIAGNOSTICO_ID:", diag_id)

hip_id = ashley.adicionar_hipotese_caso(
    caso_id,
    hipotese="A queda pode estar relacionada à retenção de clientes.",
    evidencia="Relato de perda de clientes; ainda sem métricas de churn.",
    confianca=0.45
)
print("3. HIPOTESE_ID:", hip_id)

plano_id = ashley.criar_plano_resolucao_caso(
    caso_id,
    objetivo="Identificar a principal causa da perda de clientes.",
    estrategia="Levantar cancelamentos, entrevistar clientes perdidos e comparar os últimos 90 dias.",
    criterio_sucesso="Ter evidência suficiente para priorizar uma causa e uma intervenção."
)
print("4. PLANO_ID:", plano_id)

acao_id = ashley.definir_proxima_acao_caso(
    caso_id,
    descricao="Levantar os clientes perdidos nos últimos 90 dias e registrar o motivo conhecido de saída.",
    responsavel="usuario"
)
print("5. PROXIMA_ACAO_ID:", acao_id)

print("\\nCONTEXTO V4:")
print(ashley.contexto_resolucao_caso(caso_id))

print("\\nDIAGNOSTICO DO ORQUESTRADOR:")
print(ashley.diagnostico())

print("\\nBanco de teste:", DB)
