# Executar no PowerShell, na raiz do projeto, após fazer backup.
$ErrorActionPreference = 'Stop'
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest tests -q 2>&1 | Tee-Object -FilePath resultado_testes.txt
Write-Host 'Resultado salvo em resultado_testes.txt'
