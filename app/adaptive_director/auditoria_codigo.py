"""Auditoria defensiva estática; não executa o código examinado."""
import ast
from pathlib import Path

ALVOS = {"eval", "exec", "pickle.loads", "os.system", "subprocess.Popen"}

def auditar_codigo(raiz: str, max_arquivos: int = 500) -> list[dict]:
    pasta = Path(raiz).resolve()
    if not pasta.is_dir() or not 1 <= max_arquivos <= 5000:
        raise ValueError("Pasta ou limite inválido")
    achados = []
    for arquivo in list(sorted(pasta.rglob("*.py")))[:max_arquivos]:
        if any(x in arquivo.parts for x in (".venv", "venv", "__pycache__")):
            continue
        try:
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeError, OSError):
            continue
        for no in ast.walk(arvore):
            if isinstance(no, ast.Call):
                try:
                    nome = ast.unparse(no.func)
                except Exception:
                    continue
                if nome in ALVOS:
                    achados.append({"arquivo": str(arquivo.relative_to(pasta)), "linha": no.lineno,
                                    "regra": nome, "revisao_manual": True})
    return achados
