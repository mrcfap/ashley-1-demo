# Axyntora — pacote consolidado para verificação

Base: Ashley Oficial final (20261030-134621).zip. O segundo ZIP (140259) estava vazio.

**Não é homologação total.** Foram preservados módulos da aplicação original, acrescentados um ponto de entrada único e inventário estático. A funcionalidade de todos os motores V1–V100 e dos 11 agentes ainda requer testes operacionais, serviços externos e credenciais configuradas.

## PowerShell (na pasta descompactada)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests/test_master_integracao.py -q
$env:AXYNTORA_MASTER_ADMIN_KEY='chave-local-de-teste'
python -m uvicorn app_orquestrador_master:app --host 127.0.0.1 --port 8000
```
Em outra janela:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/master/status -Headers @{'x-master-admin-key'='chave-local-de-teste'}
```

Não envie `.env` nem bancos de dados ao Git. Faça backup dos dados originais. O deploy na Render só deve ocorrer após validação local, autenticação, consentimento e testes dos fluxos reais.
