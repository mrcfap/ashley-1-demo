"""Validação segura: mudanças ficam em staging; promoção depende de aprovação externa."""
import ast, shutil, subprocess, sys, tempfile, pathlib, hashlib
from .reliability import audit

def validate_patch(workspace, relative_path, source):
    base=pathlib.Path(workspace).resolve()
    target=(base/relative_path).resolve()
    if not target.is_relative_to(base) or target.suffix!='.py':
        raise ValueError('Caminho fora do workspace ou arquivo não Python')
    ast.parse(source)
    digest=hashlib.sha256(source.encode()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='ashley_staging_') as tmp:
        stage=pathlib.Path(tmp)/'candidate.py'
        stage.write_text(source,encoding='utf-8')
        result=subprocess.run([sys.executable,'-I','-m','py_compile',str(stage)],capture_output=True,text=True,timeout=15)
        passed=result.returncode==0
    audit('evolution_validation',file=str(relative_path),sha256=digest,passed=passed)
    return {'passed':passed,'sha256':digest,'requires_approval':True,'error':result.stderr[-1000:] if not passed else None}

def backup_file(target, backup_dir):
    target=pathlib.Path(target)
    backup_dir=pathlib.Path(backup_dir)
    backup_dir.mkdir(parents=True,exist_ok=True)
    dest=backup_dir/(target.name+'.'+hashlib.sha256(target.read_bytes()).hexdigest()[:12]+'.bak')
    shutil.copy2(target,dest)
    audit('backup_created',file=target.name)
    return dest
