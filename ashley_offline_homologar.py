"""Homologação local isolada da Ashley. Não importa serviços de IA nem usa rede."""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = ('app/API/app.py', 'app/services/gemini_service.py', 'app/core/orquestrador.py')


def inspect_source(root: Path) -> dict:
    found = {name: (root / name).is_file() for name in REQUIRED}
    return {'ok': all(found.values()), 'arquivos': found}


def sqlite_roundtrip() -> dict:
    with tempfile.TemporaryDirectory(prefix='ashley_offline_') as tmp:
        db = Path(tmp) / 'homologacao.db'
        conn = sqlite3.connect(db)
        try:
            conn.execute('CREATE TABLE memorias (user_id INTEGER, texto TEXT)')
            conn.executemany('INSERT INTO memorias VALUES (?,?)', [(1, 'teste um'), (2, 'teste dois')])
            own = conn.execute('SELECT texto FROM memorias WHERE user_id=?', (1,)).fetchall()
            other = conn.execute('SELECT texto FROM memorias WHERE user_id=?', (2,)).fetchall()
            conn.commit()
        finally:
            conn.close()
        return {'ok': own == [('teste um',)] and other == [('teste dois',)], 'tipo': 'sqlite_temporario', 'dados_reais': False}


def mock_conversation() -> dict:
    # Simula contrato de resposta; não simula capacidade cognitiva.
    msg = 'Olá, Ashley'
    response = {'answer': '[SIMULAÇÃO OFFLINE] Mensagem recebida: ' + msg,
                'persona': 'Ashley', 'model': 'offline_mock', 'memory_enabled': False}
    return {'ok': response['model'] == 'offline_mock' and msg in response['answer'],
            'tipo': 'contrato_simulado', 'modelo_real': False}


def source_checks(root: Path) -> dict:
    p = root / 'app/API/app.py'
    if not p.exists():
        return {'ok': False, 'motivo': 'app.py ausente'}
    src = p.read_text(encoding='utf-8')
    checks = {'chat': '@app.post("/chat")' in src or "@app.post('/chat')" in src,
              'health': '@app.get("/health")' in src or "@app.get('/health')" in src,
              'v76': 'make_v76_router(HumanityCoreV76(' in src,
              'auth_guard': 'async def auth_guard(' in src}
    return {'ok': all(checks.values()), 'verificacoes_estaticas': checks,
            'nota': 'Presença no código não comprova operação real'}


def run_unittests(root: Path) -> dict:
    env = os.environ.copy()
    env.pop('GEMINI_API_KEY', None)
    env.pop('GOOGLE_API_KEY', None)
    env['ASHLEY_OFFLINE_HOMOLOGACAO'] = '1'
    proc = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v'],
                          cwd=root, env=env, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=180)
    (root / 'relatorio_testes_offline.txt').write_text(proc.stdout, encoding='utf-8')
    return {'ok': proc.returncode == 0, 'codigo_saida': proc.returncode,
            'arquivo': 'relatorio_testes_offline.txt',
            'observacao': 'Chaves removidas do ambiente do subprocesso; um .env local ainda pode ser carregado pela aplicação. Não é isolamento de rede.'}


def main() -> int:
    parser = argparse.ArgumentParser(description='Homologação offline isolada da Ashley 1.0')
    parser.add_argument('--com-testes', action='store_true', help='Executa também testes existentes (pode carregar .env)')
    args = parser.parse_args()
    checks = {'estrutura': inspect_source(ROOT), 'sqlite_local': sqlite_roundtrip(),
              'contrato_chat_mock': mock_conversation(), 'integracao_estatica': source_checks(ROOT)}
    if args.com_testes:
        checks['unittest_existentes'] = run_unittests(ROOT)
    report = {'produto': 'Ashley 1.0', 'modo': 'homologacao_local_sem_chamadas_de_ia',
              'data_utc': datetime.now(timezone.utc).isoformat(), 'resultados': checks,
              'aprovado': all(x['ok'] for x in checks.values()),
              'limites': ['Não inicia o servidor FastAPI', 'Não faz chamadas de rede neste script',
                         'Não valida inferência real, voz neural, imagens, vídeos ou câmera',
                         'Não comprova segurança em produção nem funcionamento dos 76 motores']}
    target = ROOT / 'relatorio_homologacao_offline.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print('\nRelatório:', target)
    return 0 if report['aprovado'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
