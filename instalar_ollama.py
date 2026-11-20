"""Aplica patch conservador e faz backup do app.py."""
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent
app = root / 'app' / 'API' / 'app.py'
source = root / 'ollama_local.py'
dest = root / 'app' / 'services' / 'ollama_local.py'
if not app.is_file() or not source.is_file():
    sys.exit('ERRO: extraia os arquivos na raiz Ashley Oficial final.')
text = app.read_text(encoding='utf-8-sig')
if 'from app.services.ollama_local import chat_local' in text:
    sys.exit('Integração já instalada. Nenhuma alteração realizada.')
needle = 'from app.services.gemini_service import GeminiService'
old = '''    result_gemini = await oq.nexus_v45.execute_safe_async(
        lambda: gemini.chat_com_fallback(system=system, message=data.message, history=data.history),
        fallback_value=None, timeout=restante, service='gemini_chat', retries=0,
    )'''
new = '''    provedor = os.getenv('ASHLEY_CHAT_PROVIDER', 'gemini').strip().lower()
    if provedor not in ('ollama', 'gemini'):
        raise HTTPException(status_code=503, detail='Provedor de chat inválido.')
    result_gemini = await oq.nexus_v45.execute_safe_async(
        (lambda: chat_local(system=system, message=data.message, history=data.history))
        if provedor == 'ollama' else
        (lambda: gemini.chat_com_fallback(system=system, message=data.message, history=data.history)),
        fallback_value=None, timeout=restante,
        service=('ollama_local_chat' if provedor == 'ollama' else 'gemini_chat'), retries=0,
    )'''
oldmem = '''    try:
        memoria_automatica = await asyncio.wait_for(
            analisador_memoria.analisar(user_id=data.user_id, entrada=data.message, resposta=answer),'''
newmem = '''    if provedor == 'ollama':
        memoria_automatica = {'executado': False, 'motivo': 'analise_automatica_desativada_no_modo_local', 'memorias_salvas': 0}
    else:
        try:
            memoria_automatica = await asyncio.wait_for(
                analisador_memoria.analisar(user_id=data.user_id, entrada=data.message, resposta=answer),'''
oldmemtail = '''        )
    except Exception as exc:
        memoria_automatica = {
            "executado": False,
            "motivo": "falha_memoria_automatica",
            "erro": f"{type(exc).__name__}: {exc}",
            "memorias_salvas": 0
        }'''
newmemtail = '''            )
        except Exception as exc:
            memoria_automatica = {
                "executado": False,
                "motivo": "falha_memoria_automatica",
                "erro": f"{type(exc).__name__}: {exc}",
                "memorias_salvas": 0
            }'''
if any(text.count(x)!=1 for x in (needle,old,oldmem,oldmemtail)):
    sys.exit('ERRO: versão do app.py diferente. Nenhum arquivo alterado.')
text=text.replace(needle,needle+'\nfrom app.services.ollama_local import chat_local',1)
text=text.replace(old,new,1).replace(oldmem,newmem,1).replace(oldmemtail,newmemtail,1)
compile(text,str(app),'exec')
compile(source.read_text(encoding='utf-8'),str(source),'exec')
backup = app.with_name('app.py.backup_antes_ollama')
if backup.exists():
    sys.exit('ERRO: backup já existe. Nenhum arquivo alterado.')
shutil.copy2(app,backup)
shutil.copy2(source,dest)
app.write_text(text,encoding='utf-8')
print('OK: Ollama integrado. Backup:',backup)
print('ATENÇÃO: definir ASHLEY_CHAT_PROVIDER=ollama antes de iniciar o servidor.')
