from __future__ import annotations
import ast, difflib, hashlib, json, os, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

PROTECTED_PARTS = {
    ".git", ".env", ".venv", "venv", "__pycache__", "data",
    ".ashley_backups", ".ashley_evolution_workspaces",
    ".ashley_agent_missions", "perfis_faciais", "logs",
}
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

    def _validar_workspace(self, workspace):
        workspace = Path(workspace).resolve()
        base = self.workspace_root.resolve()
        if not workspace.is_relative_to(base) or workspace == base:
            raise ValueError("Workspace fora da área de evolução.")
        marker = workspace / ".ashley_workspace.json"
        if not marker.is_file():
            raise ValueError("Workspace sem marcador de origem válido.")
        try:
            metadata = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError("Marcador do workspace inválido.")
        if metadata.get("estado") != "SANDBOX" or Path(metadata.get("origem", "")).resolve() != self.project_root:
            raise ValueError("Workspace não pertence a este projeto.")
        return workspace

    def _safe_relative(self, rel):
        rel = Path(rel)
        if rel.is_absolute() or ".." in rel.parts or rel.drive:
            raise ValueError("Caminho fora do projeto não permitido.")
        if any(x in PROTECTED_PARTS for x in rel.parts) or rel.name in PROTECTED_FILES or rel.name.lower().startswith(".env"):
            raise ValueError("Área protegida.")
        return rel


    def ler_arquivo(self, rel, max_chars=14000):
        rel = self._safe_relative(rel)

        if rel.suffix.lower() != ".py":
            raise ValueError("Leitura automatica restrita a Python.")

        alvo = (self.project_root / rel).resolve()

        if not alvo.is_relative_to(self.project_root):
            raise ValueError("Caminho fora do projeto.")

        caminho_real = alvo.relative_to(self.project_root)

        if any(p in PROTECTED_PARTS for p in caminho_real.parts):
            raise ValueError("Area protegida.")

        if any(h in str(caminho_real).lower()
               for h in HIGH_RISK_HINTS):
            raise PermissionError("Arquivo de alto risco.")

        limite = min(max(int(max_chars), 1), 14000)

        if not alvo.is_file():
            raise FileNotFoundError(alvo)

        if alvo.stat().st_size > 100000:
            raise ValueError("Arquivo excede o limite permitido.")

        return alvo.read_text(encoding="utf-8")[:limite]

    def inventario(self, limite=500):
        itens = []
        for p in self.project_root.rglob("*"):
            if p.is_symlink() or not p.is_file():
                continue
            rel = p.relative_to(self.project_root)
            if not p.resolve().is_relative_to(self.project_root):
                continue
            if any(x in PROTECTED_PARTS for x in rel.parts):
                continue
            if rel.suffix.lower() in {".py",".html",".js",".css",".json",".md",".txt"}:
                itens.append({"arquivo": str(rel).replace(chr(92), "/"),
                              "bytes": p.stat().st_size, "sha256": self._hash(p)})
            if len(itens) >= limite:
                break
        return itens

    def criar_workspace(self, proposta_id):
        proposta_id = str(proposta_id)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", proposta_id):
            raise ValueError("Identificador de proposta inválido.")
        destino = self.workspace_root / f"{proposta_id}_{self._now()}"
        ignore = shutil.ignore_patterns(
            ".git", ".venv", "venv", "__pycache__",
            ".ashley_evolution_workspaces", ".ashley_backups",
            ".ashley_agent_missions", "perfis_faciais", "logs",
            ".env*", "*.db", "*.sqlite", "*.sqlite3", "*.npz",
            "*.wal", "*.shm"
        )
        shutil.copytree(self.project_root, destino, ignore=ignore, symlinks=True)
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
        workspace = self._validar_workspace(workspace)
        rel = self._safe_relative(rel)
        if rel.suffix.lower() != ".py":
            raise ValueError("Alterações automáticas restritas a arquivos Python.")
        alvo = (workspace / rel).resolve()
        if not alvo.is_relative_to(workspace):
            raise ValueError("Caminho inválido.")
        alvo.parent.mkdir(parents=True, exist_ok=True)
        if alvo.suffix == ".py":
            ast.parse(novo_conteudo)
        alvo.write_text(novo_conteudo, encoding="utf-8")
        return {"ok":True, "arquivo":str(rel).replace(chr(92),"/"),
                "sha256":self._hash(alvo)}

    def diff(self, workspace, rel):
        workspace = self._validar_workspace(workspace)
        rel = self._safe_relative(rel)
        if rel.suffix.lower() != ".py":
            raise ValueError("Diff automático restrito a arquivos Python.")
        original = (self.project_root / rel).resolve()
        if not original.is_relative_to(self.project_root):
            raise ValueError("Arquivo original fora do projeto.")
        candidato = (workspace / rel).resolve()
        if not candidato.is_relative_to(workspace):
            raise ValueError("Candidato fora do workspace.")
        a = original.read_text(encoding="utf-8").splitlines(True) if original.is_file() else []
        b = candidato.read_text(encoding="utf-8").splitlines(True) if candidato.is_file() else []
        return "".join(difflib.unified_diff(a,b,fromfile=f"producao/{rel}",
                                             tofile=f"sandbox/{rel}"))

    def validar_python(self, workspace):
        workspace = self._validar_workspace(workspace)
        erros, n = [], 0
        for p in workspace.rglob("*.py"):
            if "__pycache__" in p.parts or p.is_symlink():
                continue
            if not p.resolve().is_relative_to(workspace):
                continue
            try:
                ast.parse(p.read_text(encoding="utf-8")); n += 1
            except Exception as e:
                erros.append({"arquivo":str(p), "erro":str(e)})
        return {"ok":not erros, "arquivos_verificados":n, "erros":erros}

    def executar_testes(self, workspace, comandos=None, timeout=90):
        workspace = self._validar_workspace(workspace)
        comandos = comandos or [[sys.executable,"-m","compileall","-q","app"]]
        resultados, ok_total = [], True
        # Não repassar chaves, DATABASE_URL ou outros segredos do servidor
        # para processos que executam código candidato.
        env = {
            key: os.environ[key]
            for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATHEXT", "COMSPEC")
            if key in os.environ
        }
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        for cmd in comandos:
            if not isinstance(cmd,list) or not cmd or not all(isinstance(x, str) for x in cmd):
                raise ValueError("Comando deve ser lista de argumentos textuais.")
            if Path(cmd[0]).resolve() != Path(sys.executable).resolve():
                raise ValueError("Somente o interpretador Python configurado pode executar testes.")
            if "-c" in cmd:
                raise ValueError("Execução Python inline não permitida; use arquivo de teste no workspace.")
            for arg in cmd[1:]:
                if arg.endswith(".py"):
                    script = (workspace / arg).resolve()
                    if not script.is_relative_to(workspace) or not script.is_file():
                        raise ValueError("Script de teste fora do workspace.")
            try:
                p = subprocess.run(cmd,cwd=str(workspace),
                    capture_output=True,text=True,timeout=min(int(timeout),180),
                    env=env)
                ok = p.returncode == 0; ok_total = ok_total and ok
                resultados.append({"comando":cmd,"ok":ok,"returncode":p.returncode,
                    "stdout":p.stdout[-6000:],"stderr":p.stderr[-6000:]})
            except subprocess.TimeoutExpired:
                ok_total=False; resultados.append({"comando":cmd,"ok":False,"erro":"timeout"})
        return {
            "ok": ok_total,
            "resultados": resultados,
            "ambiente_filtrado": True,
            "isolamento": "subprocesso_python_sem_sandbox_de_sistema_operacional",
        }

    def promover(self, workspace, arquivos, autorizado=False, risco="MEDIO"):
        if not autorizado:
            raise PermissionError("Promocao exige autorizacao explicita.")

        if str(risco).upper() in {"ALTO", "CRITICO"}:
            raise PermissionError("Risco elevado nao pode ser promovido.")

        workspace = self._validar_workspace(workspace)
        raiz_workspaces = self.workspace_root.resolve()
        raiz_projeto = self.project_root.resolve()

        pendentes = []
        vistos = set()

        for rel in arquivos:
            rel = self._safe_relative(rel)
            if rel.suffix.lower() != ".py":
                raise ValueError("Promoção automática restrita a arquivos Python.")
            src = (workspace / rel).resolve()
            dst = (raiz_projeto / rel).resolve()

            if not src.is_relative_to(workspace):
                raise ValueError("Origem fora do workspace.")

            if not dst.is_relative_to(raiz_projeto):
                raise ValueError("Destino fora do projeto.")

            if not src.is_file():
                raise FileNotFoundError(src)

            if dst.exists() and not dst.is_file():
                raise ValueError("Destino nao e arquivo.")

            if dst in vistos:
                raise ValueError("Arquivo duplicado.")

            vistos.add(dst)
            pendentes.append((rel, src, dst))

        backup_root = raiz_projeto / ".ashley_backups" / self._now()
        backups = []
        modificados = []
        feitos = []

        # Preparar todos os backups antes de alterar o projeto.
        for rel, src, dst in pendentes:
            backup = None
            if dst.exists():
                backup = backup_root / rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup)

            backups.append((rel, src, dst, backup))

        try:
            for rel, src, dst, backup in backups:
                dst.parent.mkdir(parents=True, exist_ok=True)

                # Registrar antes da copia para recuperar tambem
                # arquivos parcialmente escritos.
                modificados.append((dst, backup))
                shutil.copy2(src, dst)

                feitos.append({
                    "target": rel.as_posix(),
                    "backup": str(backup) if backup else None
                })

        except Exception as erro:
            falhas_restauracao = []

            for dst, backup in reversed(modificados):
                try:
                    if backup is not None:
                        shutil.copy2(backup, dst)
                    elif dst.exists():
                        dst.unlink()
                except Exception as erro_rollback:
                    falhas_restauracao.append(
                        f"{dst}: {erro_rollback}"
                    )

            if falhas_restauracao:
                raise RuntimeError(
                    "Publicacao falhou e rollback ficou incompleto. "
                    f"Backups: {backup_root}. "
                    f"Falhas: {falhas_restauracao}"
                ) from erro

            raise

        return {
            "ok": True,
            "backup_root": str(backup_root),
            "arquivos": feitos
        }

    def rollback(self, backup_root):
        backup_root = Path(backup_root).resolve()
        base = (self.project_root / ".ashley_backups").resolve()
        if not backup_root.is_relative_to(base) or backup_root == base:
            raise ValueError("Backup inválido.")
        restaurados = []
        for src in backup_root.rglob("*"):
            if src.is_symlink() or not src.is_file():
                continue
            rel = src.relative_to(backup_root)
            rel = self._safe_relative(rel)
            dst = (self.project_root / rel).resolve()
            if not dst.is_relative_to(self.project_root):
                raise ValueError("Destino de rollback fora do projeto.")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restaurados.append(str(rel).replace(chr(92), "/"))
        return {"ok":True,"restaurados":restaurados}
