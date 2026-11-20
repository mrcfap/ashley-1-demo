$p = Join-Path $PSScriptRoot 'app\memory\memoria_longa_com_erro.py'
if (Test-Path $p) { Rename-Item -LiteralPath $p -NewName 'memoria_longa_com_erro.py.quarantined' }
