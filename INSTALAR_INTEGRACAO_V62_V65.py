"""Executar na raiz Ashley Oficial final: python INSTALAR_INTEGRACAO_V62_V65.py"""
from pathlib import Path
from datetime import datetime
import shutil

root=Path(__file__).resolve().parent
main=root/'app'/'API'/'app.py'
if not main.is_file():
    raise SystemExit('ERRO: app/API/app.py nao encontrado. Execute na raiz Ashley Oficial final.')
marker='# Ashley V62-V65: rotas supervisionadas (integracao incremental)'
text=main.read_text(encoding='utf-8-sig')
if marker in text:
    print('Integracao ja registrada. Nenhuma alteracao realizada.')
else:
    backup=main.with_name('app_backup_antes_v62_v65_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.py')
    shutil.copy2(main,backup)
    block='\n\n'+marker+'\nfrom app.integrations.v62_v65_api import router as v62_v65_router\napp.include_router(v62_v65_router)\n'
    main.write_text(text+block,encoding='utf-8')
    print('Rotas registradas em:',main)
    print('Backup preservado em:',backup)
print('Agora execute: python -m unittest discover -s tests -p "test_v62_v65_integration.py" -v')
