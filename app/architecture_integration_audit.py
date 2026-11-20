"""Auditoria de ligação dos agentes e motores sem executar código não confiável.

Presença, importação, instanciação e uso em runtime são estados diferentes.
A auditoria é de somente leitura e nunca inicia agentes nem chama provedores.
"""
import ast
from pathlib import Path
from app.architecture_diagnostics import diagnostico, ROOT


def _arvore(rel):
    path = ROOT / rel
    try:
        return ast.parse(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, SyntaxError):
        return None


def _imports(tree):
    modulos = set()
    if tree is None:
        return modulos
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modulos.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modulos.add(node.module)
    return modulos


def auditar_integracoes():
    inventario = diagnostico()
    orq = _arvore("app/core/orquestrador.py")
    api = _arvore("app/API/app.py")
    imports_orq = _imports(orq)
    imports_api = _imports(api)
    # Instanciação estática do orquestrador: comprova ligação no código, não execução.
    instanciados = set()
    if orq is not None:
        for node in ast.walk(orq):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    instanciados.add(node.value.func.id)
    resultados = []
    for item in inventario["componentes"]:
        rel = item["arquivo"]
        if not (rel.startswith("app/agents/") or
                any(k in rel.lower() for k in ("motor", "engine", "orquestr", "integracao", "integration"))):
            continue
        modulo = rel[:-3].replace("/", ".")
        nomes = set(item.get("simbolos", []))
        no_orquestrador = modulo in imports_orq
        na_api = modulo in imports_api
        instancia_estatica = bool(nomes & instanciados) if no_orquestrador else False
        if item["estado"] != "encontrado":
            status = "falha_estatica"
        elif instancia_estatica:
            status = "instanciacao_referenciada"
        elif no_orquestrador or na_api:
            status = "importacao_referenciada"
        else:
            status = "sem_ligacao_direta_identificada"
        resultados.append({
            "componente": rel,
            "estado": status,
            "importado_orquestrador": no_orquestrador,
            "importado_api": na_api,
            "instanciacao_referenciada": instancia_estatica,
            "funcionamento_comprovado": False,
        })
    return {
        "modo": "auditoria_estatica_sem_efeitos_colaterais",
        "total": len(resultados),
        "instanciacao_referenciada": sum(x["instanciacao_referenciada"] for x in resultados),
        "importacao_referenciada": sum(x["estado"] == "importacao_referenciada" for x in resultados),
        "sem_ligacao_direta_identificada": sum(x["estado"] == "sem_ligacao_direta_identificada" for x in resultados),
        "funcionamento_comprovado": 0,
        "componentes": resultados,
        "limites": "A análise estática não comprova execução, inicialização bem-sucedida, comunicação entre agentes ou segurança de uma integração automática.",
    }
