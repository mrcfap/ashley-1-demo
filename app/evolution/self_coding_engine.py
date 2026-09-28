from __future__ import annotations
import ast, difflib, hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

PROTECTED_PARTS = {".git", ".env", ".venv", "venv", "__pycache__", "data", ".ashley_backups"}
PROTECTED_FILES = {".env", "ashley.db"}
HIGH_RISK_HINTS = ("auth","login","senha","password","secret","token","permission","permiss",
                   "security","segur","database","banco","migration","migracao",
                   "evolution","autoevol","self_coding","motor_autoevolucao")

class SelfCodingEngine:
    def __init__(self, project_root, workspace_root=None):
        self.project_root = Path(project_root).resolve()
        self.workspace_root = Path(workspace_root or
            (self.project_root / ".ashley_evolution_workspaces")).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def _now(self):
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def _hash(self, path):
        h = hashlib.sha256()
        with Path(path).open("rb") as f:
            for b in iter(lambda: f.read(1048576), b""):
                h.update(b)
        return h.hexdigest()

    def _safe_relative(self, rel):
        rel = Path(rel)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Caminho fora do projeto não permitido.")
        if any(x in PROTECTED_PARTS for x in rel.parts) or rel.name in PROTECTED_FILES:
            raise ValueError("Área protegida.")
        return rel

    def inventario(self, limite=500):
        itens = []
        for p in self.project_root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(self.project_root)
            if any(x in PROTECTED_PARTS for x in rel.parts):
                continue
            if rel.suffix.lower() in {".py",".html",".js",".css",".json",".md",".txt"}:
                itens.append({"arquivo": str(rel).replace(chr(92), "/"),
                              "bytes": p.stat().st_size, "sha256": self._hash(p)})
            if len(itens) >= limite:
                break
        return itens

    def criar_workspace(self, proposta_id):
        destino = self.workspace_root / f"{proposta_id}_{self._now()}"
        ignore = shutil.ignore_patterns(".git",".venv","venv","__pycache__",
                                         ".ashley_evolution_workspaces","*.db",".env",
                                         ".ashley_backups")
        shutil.copytree(self.project_root, destino, ignore=ignore)
        (destino/".ashley_workspace.json").write_text(json.dumps({
            "proposta_id": proposta_id, "origem": str(self.project_root),
            "criado_em": datetime.now(timezone.utc).isoformat(), "estado":"SANDBOX"
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        return destino

    def avaliar_risco(self, arquivos, descricao=""):
        texto = (" ".join(arquivos) + " " + descricao).lower()
        if any(h in texto for h in HIGH_RISK_HINTS):
            return "ALTO"
        if any(str(a).replace(chr(92),"/").startswith(("app/API/","app/core/")) for a in arquivos):
            return "MEDIO"
        return "BAIXO"

    def aplicar_conteudo_candidato(self, workspace, rel, novo_conteudo):
        workspace = Path(workspace).resolve()
        if not str(workspace).startswith(str(self.workspace_root)):
            raise ValueError("Alterações automáticas só em workspace V9.")
        rel = self._safe_relative(rel)
        alvo = (workspace/rel).resolve()
        if not str(alvo).startswith(str(workspace)):
            raise ValueError("Caminho inválido.")
        alvo.parent.mkdir(parents=True, exist_ok=True)
        if alvo.suffix == ".py":
            ast.parse(novo_conteudo)
        alvo.write_text(novo_conteudo, encoding="utf-8")
        return {"ok":True, "arquivo":str(rel).replace(chr(92),"/"),
                "sha256":self._hash(alvo)}

    def diff(self, workspace, rel):
        rel = self._safe_relative(rel)
        original, candidato = self.project_root/rel, Path(workspace).resolve()/rel
        a = original.read_text(encoding="utf-8").splitlines(True) if original.exists() else []
        b = candidato.read_text(encoding="utf-8").splitlines(True) if candidato.exists() else []
        return "".join(difflib.unified_diff(a,b,fromfile=f"producao/{rel}",
                                             tofile=f"sandbox/{rel}"))

    def validar_python(self, workspace):
        erros, n = [], 0
        for p in Path(workspace).resolve().rglob("*.py"):
            if "__pycache__" in p.parts: continue
            try:
                ast.parse(p.read_text(encoding="utf-8")); n += 1
            except Exception as e:
                erros.append({"arquivo":str(p), "erro":str(e)})
        return {"ok":not erros, "arquivos_verificados":n, "erros":erros}

    def executar_testes(self, workspace, comandos=None, timeout=90):
        comandos = comandos or [[sys.executable,"-m","compileall","-q","app"]]
        resultados, ok_total = [], True
        for cmd in comandos:
            if not isinstance(cmd,list) or not cmd:
                raise ValueError("Comando deve ser lista de argumentos.")
            try:
                p = subprocess.run(cmd,cwd=str(Path(workspace).resolve()),
                    capture_output=True,text=True,timeout=min(int(timeout),180),
                    env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
                ok = p.returncode == 0; ok_total = ok_total and ok
                resultados.append({"comando":cmd,"ok":ok,"returncode":p.returncode,
                    "stdout":p.stdout[-6000:],"stderr":p.stderr[-6000:]})
            except subprocess.TimeoutExpired:
                ok_total=False; resultados.append({"comando":cmd,"ok":False,"erro":"timeout"})
        return {"ok":ok_total,"resultados":resultados}

    def promover(self, workspace, arquivos, autorizado=False, risco="MEDIO"):
        if not autorizado:
            raise PermissionError("Promoção exige autorização explícita.")
        if str(risco).upper() in {"ALTO","CRITICO"}:
            raise PermissionError("Risco ALTO/CRITICO não é promovido pela V9.")
        workspace=Path(workspace).resolve()
        if not str(workspace).startswith(str(self.workspace_root)):
            raise ValueError("Workspace inválido.")
        backup_root=self.project_root/".ashley_backups"/self._now()
        feitos=[]
        for rel in arquivos:
            rel=self._safe_relative(rel); src=workspace/rel; dst=self.project_root/rel
            if not src.exists(): raise FileNotFoundError(src)
            backup=None
            if dst.exists():
                backup=backup_root/rel; backup.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(dst,backup)
            dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
            feitos.append({"target":str(rel).replace(chr(92),"/"),
                           "backup":str(backup) if backup else None})
        return {"ok":True,"backup_root":str(backup_root),"arquivos":feitos}

    def rollback(self, backup_root):
        backup_root=Path(backup_root).resolve()
        base=(self.project_root/".ashley_backups").resolve()
        if not str(backup_root).startswith(str(base)): raise ValueError("Backup inválido.")
        restaurados=[]
        for src in backup_root.rglob("*"):
            if src.is_file():
                rel=src.relative_to(backup_root); dst=self.project_root/rel
                dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
                restaurados.append(str(rel).replace(chr(92),"/"))
        return {"ok":True,"restaurados":restaurados}
