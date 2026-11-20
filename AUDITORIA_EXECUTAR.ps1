$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pip install -r requirements.txt
python -m pytest -q tests testes 2>&1 | Tee-Object -FilePath auditoria_testes_windows.log
python -m uvicorn app.API.app:app --host 127.0.0.1 --port 8000
