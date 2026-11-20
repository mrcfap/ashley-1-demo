$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv')) { py -m venv .venv }
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -m pip install -U pip
& $python -m pip install -r requirements.txt pytest
& $python -m compileall -q app
& $python -m pytest -q tests --junitxml=resultado_testes.xml
Write-Host 'Confira resultado_testes.xml. Testes de hardware e provedores externos exigem validacao separada.'
