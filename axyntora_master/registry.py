"""Inventário estático e seguro; não executa módulos nem alega homologação."""
from pathlib import Path
import ast,re
ROOT=Path(__file__).resolve().parents[1]
AGENTS=("Planejador","Arquiteto","Programador","Revisor","Testador","Documentador","SENTINELA","SINTONIA","PRAXIS","VIGIA","CRIVO")
def inventario():
    arquivos=list((ROOT/'app').rglob('*.py'))
    classes=[]; erros=[]; versoes=set()
    for f in arquivos:
        try:
            tree=ast.parse(f.read_text(encoding='utf-8-sig'),filename=str(f))
            for node in ast.walk(tree):
                if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                    nome=node.name
                    classes.append({'arquivo':str(f.relative_to(ROOT)),'simbolo':nome})
                    for match in re.findall(r'(?i)(?:motor|engine|v)[_ -]?(\d{1,3})',nome):
                        if 1<=int(match)<=100:versoes.add(int(match))
        except (SyntaxError,UnicodeError) as exc:erros.append({'arquivo':str(f.relative_to(ROOT)),'erro':str(exc)})
    return {'arquivos_python':len(arquivos),'simbolos':len(classes),'versoes_identificadas_por_nome':sorted(versoes),'agentes_previstos':list(AGENTS),'erros_sintaxe':erros,'aviso':'Descoberta estática; não implica execução, integração funcional ou homologação.'}
