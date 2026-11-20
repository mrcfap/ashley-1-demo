from app.services.upload_security import inspect_file

def test_python_source_allowed(tmp_path, monkeypatch):
    # Teste de política de extensão sem depender do Defender do host.
    monkeypatch.setattr("app.services.upload_security.sys.platform", "linux")
    p=tmp_path/'codigo.py';p.write_text('print(1)')
    assert inspect_file(p)['permitido_para_analise']

def test_executable_blocked(tmp_path):
    p=tmp_path/'app.exe';p.write_bytes(b'MZ'+b'0'*32)
    assert not inspect_file(p)['permitido_para_analise']

def test_disguised_executable_blocked(tmp_path):
    p=tmp_path/'foto.txt';p.write_bytes(b'MZ'+b'0'*32)
    assert not inspect_file(p)['permitido_para_analise']

def test_strict_av_fail_closed(tmp_path):
    p=tmp_path/'codigo.txt';p.write_text('hello')
    result=inspect_file(p,require_av=True)
    if result['antivirus']!='sem_deteccao_reportada':assert not result['permitido_para_analise']


def test_python_never_executed(tmp_path, monkeypatch):
    p=tmp_path/'codigo.py'
    p.write_text('raise RuntimeError("não executar")')
    monkeypatch.setattr("app.services.upload_security.sys.platform", "linux")
    assert inspect_file(p)['permitido_para_analise']

def test_defender_error_blocks_analysis(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import app.services.upload_security as sec
    p=tmp_path/'codigo.py';p.write_text('print(1)')
    monkeypatch.setattr(sec.sys,'platform','win32')
    monkeypatch.setattr(sec.shutil,'which',lambda _: 'MpCmdRun.exe')
    monkeypatch.setattr(sec.subprocess,'run',lambda *a, **kw: SimpleNamespace(returncode=2))
    result=inspect_file(p)
    assert result['antivirus']=='deteccao_ou_erro'
    assert not result['permitido_para_analise']
