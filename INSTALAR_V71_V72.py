"""Idempotent router registration with backup; run from project root."""
from pathlib import Path
from datetime import datetime
import shutil

p = Path('app/API/app.py')
if not p.is_file():
    raise SystemExit('Execute na raiz da Ashley: app/API/app.py nao encontrado')
source = p.read_text(encoding='utf-8')
marker = 'from app.integrations.v71_v72_api import router as v71_v72_router'
if marker in source:
    print('V71/V72 ja registrados; nenhuma alteracao')
else:
    backup = p.with_name('app_backup_antes_v71_v72_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.py')
    shutil.copy2(p, backup)
    p.write_text(source.rstrip() + '\n\n' + marker + '\napp.include_router(v71_v72_router)\n', encoding='utf-8')
    print('Rotas registradas. Backup:', backup)
