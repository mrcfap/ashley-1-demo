"""Camada conservadora de segurança: nunca executa uploads."""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

MAX_BYTES = 50 * 1024 * 1024
DANGEROUS = {'.exe','.dll','.com','.scr','.msi','.msp','.ps1','.bat','.cmd','.vbs','.vbe','.js','.jse','.wsf','.hta','.jar','.apk','.app','.sh','.elf','.so','.dylib'}
MAGICS = (b'MZ', b'\x7fELF', b'\xfe\xed\xfa\xce', b'\xcf\xfa\xed\xfe')

def inspect_file(path, original_name=None, *, require_av=False):
    path=Path(path)
    size=path.stat().st_size
    if size > MAX_BYTES: raise ValueError('Arquivo acima do limite de 50 MB.')
    with path.open('rb') as f: head=f.read(8192)
    name=Path(original_name or path.name).name
    suffix=Path(name).suffix.lower()
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    risky=suffix in DANGEROUS or any(head.startswith(x) for x in MAGICS)
    report={'nome':name,'bytes':size,'sha256':digest.hexdigest(),'executavel_ou_script':risky,'antivirus':'nao_executado','permitido_para_analise':not risky}
    if risky:
        report['motivo']='Arquivo executável/script bloqueado preventivamente; nenhuma execução permitida.'
        return report
    # Defender: somente quando disponível no Windows. Não declara limpo sem scanner.
    if sys.platform == 'win32':
        defender=shutil.which('MpCmdRun.exe')
        if not defender:
            for candidate in (Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Windows Defender/MpCmdRun.exe',):
                if candidate.is_file():defender=str(candidate);break
        if defender:
            try:
                r=subprocess.run([str(defender),'-Scan','-ScanType','3','-File',str(path),'-DisableRemediation'],capture_output=True,text=True,timeout=90,check=False)
                report['antivirus']='sem_deteccao_reportada' if r.returncode==0 else 'deteccao_ou_erro'
                if r.returncode!=0:report['permitido_para_analise']=False
            except (OSError,subprocess.TimeoutExpired):report['antivirus']='falha_na_verificacao'
    if require_av and report['antivirus']!='sem_deteccao_reportada':report['permitido_para_analise']=False
    return report
