"""Instalação conservadora. Execute na raiz de Ashley Oficial final."""
from pathlib import Path
from datetime import datetime
import shutil
root=Path.cwd()
app=root/'app/API/app.py'
module=root/'app/integrations/v66_v75_api.py'
if not app.exists() or not module.exists():
    raise SystemExit('ERRO: execute na raiz do projeto, após extrair o pacote mantendo as pastas.')
text=app.read_text(encoding='utf-8-sig')
needle='from app.integrations.v66_v75_api import router as v66_v75_router'
if needle in text:
    print('Rotas já registradas; nenhuma alteração.');raise SystemExit(0)
backup=app.with_name('app_backup_antes_v66_v75_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.py')
shutil.copy2(app,backup)
app.write_text(text.rstrip()+'\n\n'+needle+'\napp.include_router(v66_v75_router)\n',encoding='utf-8')
print('Rotas registradas em:',app)
print('Backup:',backup)
