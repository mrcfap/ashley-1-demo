from pathlib import Path
from app.core.orquestrador import OrquestradorAshley

DB = Path("data/ashley_ciclo_v5_teste.db")
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

ashley.registrar_diagnostico_caso(
    caso_id,
    "Queda de clientes e vendas; causa ainda não comprovada.",
    fatos=["Clientes diminuíram", "Vendas caíram"],
    informacoes_faltantes=["Motivos de cancelamento"]
)
hip_id = ashley.adicionar_hipotese_caso(
    caso_id,
    "Problema de retenção pode estar contribuindo para a queda.",
    "Ainda sem métricas suficientes.",
    0.50
)
ashley.criar_plano_resolucao_caso(
    caso_id,
    "Identificar a principal causa da perda.",
    "Analisar clientes perdidos e motivos de saída.",
    "Identificar uma causa prioritária sustentada por evidências."
)
acao1 = ashley.definir_proxima_acao_caso(
    caso_id,
    "Levantar clientes perdidos e motivos de saída.",
    "usuario"
)

print("CASO:", caso_id)
print("HIPOTESE:", hip_id)
print("ACAO 1:", acao1)

falha = ashley.avaliar_resultado_caso(
    caso_id=caso_id,
    acao_id=acao1,
    resultado_observado=(
        "O levantamento foi feito, mas os dados ainda não explicam a queda."
    ),
    classificacao="FALHA",
    criterio_atendido=False,
    justificativa="Não foi possível sustentar a hipótese com os dados atuais.",
    proxima_acao="Entrevistar 10 clientes perdidos para coletar motivos qualitativos."
)
print("\\nAVALIACAO 1 - FALHA:")
print(falha)

ctx1 = ashley.contexto_resolucao_caso(caso_id)
print("\\nCONTEXTO APOS FALHA:")
print(ctx1)

acao2 = ctx1["proxima_acao"]["id"]

sucesso = ashley.avaliar_resultado_caso(
    caso_id=caso_id,
    acao_id=acao2,
    resultado_observado=(
        "As entrevistas identificaram uma causa prioritária recorrente "
        "e o critério definido para o teste foi atendido."
    ),
    classificacao="SUCESSO",
    criterio_atendido=True,
    justificativa="Há evidência observável suficiente para encerrar esta iteração."
)
print("\\nAVALIACAO 2 - SUCESSO:")
print(sucesso)

print("\\nHISTORICO ADAPTATIVO:")
print(ashley.contexto_ciclo_adaptativo(caso_id))

print("\\nCASOS:")
print(ashley.contexto_casos())

print("\\nDIAGNOSTICO:")
print(ashley.diagnostico())

print("\\nBanco de teste:", DB)
