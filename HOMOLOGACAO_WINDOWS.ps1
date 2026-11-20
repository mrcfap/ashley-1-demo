$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "Instalando dependencias..."
python -m pip install -r requirements.txt pytest
if ($LASTEXITCODE -ne 0) { throw "Falha na instalacao das dependencias" }
Write-Host "Executando suite de testes..."
python -m pytest -q tests testes 2>&1 | Tee-Object -FilePath homologacao_windows.log
if ($LASTEXITCODE -ne 0) { throw "Suite de testes reprovada. Veja homologacao_windows.log" }
Write-Host "Suite automatizada aprovada. Testes de hardware e servicos externos ainda sao necessarios."
Write-Host "Para iniciar: python -m uvicorn app.API.app:app --host 127.0.0.1 --port 8000"
