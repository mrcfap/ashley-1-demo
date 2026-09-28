from pathlib import Path
import sys
from app.core.orquestrador import OrquestradorAshley

DB=Path("data/ashley_self_coding_v9_teste.db")
if DB.exists(): DB.unlink()
ashley=OrquestradorAshley(db_path=str(DB),user_id=999999)

propostas=ashley.registrar_sinal_evolucao(
    categoria="qualidade_codigo",
    descricao="Provar alteração real em sandbox sem tocar produção.",
    severidade=3, componente="modulo_experimental",
    sugestao="Criar normalizador experimental e validar com teste real.",
    risco="BAIXO", titulo="Experimento real de autoprogramação")
p=propostas[0]
print("PROPOSTA:",p["id"],p["estado"])

workspace=ashley.criar_workspace_evolucao(p["id"])
print("WORKSPACE:",workspace)

codigo='def normalizar_texto(texto: str) -> str:\n    return " ".join((texto or "").strip().lower().split())\n'
print("CODIGO:",ashley.aplicar_codigo_candidato(
    workspace,"app/evolution/experimento_v9.py",codigo))

teste_codigo='from app.evolution.experimento_v9 import normalizar_texto\nassert normalizar_texto("  Olá   ASHLEY  ") == "olá ashley"\nprint("TESTE_CODIGO_V9_OK")\n'
ashley.aplicar_codigo_candidato(workspace,"teste_codigo_gerado_v9.py",teste_codigo)

print("DIFF:")
print(ashley.diff_codigo_candidato(workspace,"app/evolution/experimento_v9.py"))

testes=ashley.testar_codigo_candidato(
    workspace,comandos=[[sys.executable,"teste_codigo_gerado_v9.py"]])
print("TESTES:",testes)
assert testes["ok"] is True

registrado=ashley.registrar_teste_melhoria(
    proposta_id=p["id"],
    resultado="Código candidato criado e executado com sucesso no workspace V9.",
    metricas={"teste_codigo":1,"regressoes_detectadas":0},passou=True)
print("REGISTRO:",registrado["estado"])

assert not Path("app/evolution/experimento_v9.py").exists()

bloqueou=False
try:
    ashley.promover_codigo_candidato(
        workspace,["app/evolution/experimento_v9.py"],risco="BAIXO",autorizado=False)
except PermissionError:
    bloqueou=True
assert bloqueou
print("PROMOCAO_SEM_AUTORIZACAO: BLOQUEADA")
print("DIAGNOSTICO:",ashley.diagnostico())
assert ashley.diagnostico()["self_coding_engine_v9"] is True
print("\nV9 TESTE: PASSOU")
print("BANCO:",DB)
