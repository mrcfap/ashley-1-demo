"""Diagnóstico local, sem expor credenciais ou dados pessoais."""
from pathlib import Path
import json

def snapshot(root='.'):
    base=Path(root)
    log=base/'logs'/'operations.jsonl'
    recent=[]
    if log.exists():
        recent=[json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()[-20:] if line.strip()]
    return {'operations':recent,'log_available':log.exists(),'database_count':len(list(base.glob('*.db'))),'status':'diagnostics_ready'}
