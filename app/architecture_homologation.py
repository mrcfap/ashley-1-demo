"""Homologação local não destrutiva: inventário, sintaxe e teste SQLite isolado.
Não importa motores nem executa provedores externos. Evidências nunca são fabricadas.
"""
from __future__ import annotations
import ast
import hashlib
import sqlite3
import tempfile
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path
from fastapi import APIRouter
from app.architecture_diagnostics import diagnostico, ROOT

router = APIRouter(prefix='/arquitetura', tags=['Homologação local'])

def homologar():
    inventory = diagnostico()
    results = []
    for item in inventory['componentes']:
        path = ROOT / item['arquivo']
        if item['estado'] != 'encontrado':
            results.append({'componente': item['arquivo'], 'estado': 'falhou', 'teste': 'sintaxe', 'evidencia': item.get('erro', 'não localizado'), 'operacional': 'não verificado'})
            continue
        try:
            content = path.read_bytes()
            ast.parse(content.decode('utf-8-sig'), filename=item['arquivo'])
            results.append({'componente': item['arquivo'], 'estado': 'aprovado', 'teste': 'sintaxe', 'sha256': hashlib.sha256(content).hexdigest(), 'operacional': 'não verificado'})
        except (OSError, UnicodeError, SyntaxError) as exc:
            results.append({'componente': item['arquivo'], 'estado': 'falhou', 'teste': 'sintaxe', 'evidencia': str(exc)[:300], 'operacional': 'não verificado'})
    try:
        with tempfile.TemporaryDirectory(prefix='axyntora_homologacao_') as folder:
            db = Path(folder) / 'memoria_teste.db'
            with closing(sqlite3.connect(db)) as conn:
                conn.execute('CREATE TABLE memoria (chave TEXT PRIMARY KEY, valor TEXT)')
                conn.executemany('INSERT INTO memoria VALUES (?,?)', [('palavra', 'valor'), ('expressao', '3+2')])
                rows = dict(conn.execute('SELECT chave, valor FROM memoria'))
                conn.commit()
            passed = rows == {'palavra': 'valor', 'expressao': '3+2'}
        results.append({'componente': 'sqlite_temporario', 'teste': 'gravação e recuperação de registros independentes', 'estado': 'aprovado' if passed else 'falhou', 'evidencia': 'base temporária isolada, sem tocar na memória real', 'operacional': 'teste isolado; integração real não verificada'})
    except Exception as exc:
        results.append({'componente': 'sqlite_temporario', 'teste': 'memória isolada', 'estado': 'falhou', 'evidencia': f'{type(exc).__name__}: {str(exc)[:200]}'})
    passed = sum(r['estado'] == 'aprovado' for r in results)
    failed = len(results) - passed
    return {'executado_em_utc': datetime.now(timezone.utc).isoformat(), 'modo': 'local, sem alterações em serviços externos', 'total_testes': len(results), 'aprovados': passed, 'falharam': failed, 'operacionais_confirmados': 0, 'resultados': results, 'inventario_resumo': inventory['resumo'], 'limites': 'Testes estáticos não comprovam funcionamento dos motores. Testes funcionais por componente, carregamento e integração permanecem não verificados.'}

def resumo_chat():
    report = homologar()
    return (f"Homologação local executada em {report['executado_em_utc']}. "
            f"Testes: {report['total_testes']}; aprovados: {report['aprovados']}; falharam: {report['falharam']}. "
            f"Motores operacionais comprovados: 0 (não testados funcionalmente). "
            "Foram verificadas a sintaxe dos módulos e a gravação/recuperação em SQLite temporário. "
            "Nenhum serviço externo ou memória real foi alterado. "
            "Evidências por arquivo (incluindo SHA-256) disponíveis em /arquitetura/homologacao. "
            "Carregamento, integração e funcionamento real dos motores ainda exigem testes específicos.")

@router.get('/homologacao')
def homologacao_get():
    return homologar()
