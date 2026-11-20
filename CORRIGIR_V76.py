from pathlib import Path
from datetime import datetime
import ast
import shutil

root = Path(__file__).resolve().parent
app_file = root / 'app' / 'API' / 'app.py'
if not app_file.is_file():
    raise SystemExit('ERRO: execute este script dentro da pasta Ashley Oficial final.')
text = app_file.read_text(encoding='utf-8')
needle = 'make_v76_router(HumanityCoreV76('
if needle in text:
    print('V76 ja registrado. Nenhuma alteracao realizada.')
    raise SystemExit(0)
required = ['from app.integrations.v66_v75_api import router as v66_v75_router', 'app.include_router(v66_v75_router)']
if not all(r in text for r in required):
    raise SystemExit('ERRO: app.py nao corresponde a versao esperada; nenhuma alteracao realizada.')
block = '''\n\n# V76 Humanity Core: rotas protegidas por sessao Ashley e politica adulta.\nfrom app.humanity_v76.api import make_router as make_v76_router\nfrom app.humanity_v76.engine import HumanityCoreV76\nfrom app.integrations.v62_v65_api import identity as v76_authenticated_identity\napp.include_router(make_v76_router(HumanityCoreV76(DATA / "v76_humanity.db"), v76_authenticated_identity))\n'''
updated = text.rstrip() + block
ast.parse(updated, filename=str(app_file))
backup = app_file.with_name('app_backup_antes_reintegracao_v76_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.py')
shutil.copy2(app_file, backup)
app_file.write_text(updated, encoding='utf-8')
print('V76 reintegrado ao app.py. Backup:', backup.name)
print('Execute os testes completos antes de iniciar o servidor.')
