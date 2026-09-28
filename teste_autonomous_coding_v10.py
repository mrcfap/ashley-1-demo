from pathlib import Path
import sys, json
from app.core.orquestrador import OrquestradorAshley

DB=Path("data/ashley_autonomous_coding_v10_teste.db")
if DB.exists(): DB.unlink()

ashley=OrquestradorAshley(db_path=str(DB), user_id=999999)

propostas=ashley.registrar_sinal_evolucao(
    categoria="qualidade_codigo",
    descricao="Criar uma função pequena e testável para remover espaços duplicados.",
    severidade=3,
    componente="modulo_experimental",
    sugestao="Gerar módulo experimental de normalização.",
    risco="BAIXO",
    titulo="Normalização experimental V10"
)
p=propostas[0]
print("PROPOSTA:", p["id"])

prompt=ashley.prompt_autoprogramacao(p["id"])
assert "arquivos_relevantes" in prompt
print("INSPECAO_AUTONOMA: OK")

resposta_modelo=json.dumps({
    "arquivo":"app/helpers_v10.py",
    "explicacao":"Adicionar função pequena e reversível para normalizar espaços.",
    "codigo_completo":"def normalizar_espacos(texto: str) -> str:\n    return \" \".join((texto or \"\").split())\n",
    "teste_sugerido":"Compilar o projeto e importar a função."
}, ensure_ascii=False)

resultado=ashley.aplicar_autoprogramacao(
    p["id"], resposta_modelo,
    comandos=[[sys.executable, "-c",
      "from app.helpers_v10 import normalizar_espacos; assert normalizar_espacos('a   b') == 'a b'; print('V10_CODIGO_OK')"]]
)
print("ARQUIVO:", resultado["arquivo"])
print("RISCO:", resultado["risco"])
print("TESTES:", resultado["testes"])
assert resultado["ok"] is True
assert resultado["promovido"] is False
assert not Path("app/helpers_v10.py").exists()
print("PRODUCAO_INTACTA: OK")

diag=ashley.diagnostico()
print("DIAGNOSTICO:",diag)
assert diag["autonomous_coding_loop_v10"] is True
print("\nV10 TESTE: PASSOU")
print("BANCO:",DB)
