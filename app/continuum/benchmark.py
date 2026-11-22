"""Axyntora Continuum: benchmark determinístico, sem ações externas.

Mede resultados; NÃO afirma aprendizado autônomo ou desempenho de LLM.
"""
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path


def task_id(task):
    return hashlib.sha256(json.dumps(task, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def executar(task):
    """Tarefas offline permitidas; sem eval, rede ou código arbitrário."""
    kind = task['tipo']
    if kind == 'normalizar':
        return ' '.join(str(task['entrada']).split()).casefold()
    if kind == 'somar':
        values = task['entrada']
        if not isinstance(values, list) or len(values) > 100 or any(type(x) not in (int, float) for x in values):
            raise ValueError('Entrada numérica inválida')
        return sum(values)
    if kind == 'extrair_campos':
        return {key: task['entrada'].get(key) for key in task['campos']}
    raise ValueError('Tipo de tarefa não autorizado')


def registrar(db_path, task, obtido, sucesso, duracao_ms, usuario=1):
    """Métricas persistentes no PostgreSQL configurado; SQLite apenas offline."""
    if os.getenv('DATABASE_URL'):
        import psycopg
        with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=10) as conn:
            conn.execute('''INSERT INTO public.continuum_resultados
                (user_id, tarefa_hash, grupo, sucesso, duracao_ms)
                VALUES (%s, %s, %s, %s, %s)''',
                (int(usuario), task_id(task), task['grupo'], bool(sucesso), float(duracao_ms)))
        return
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS continuum_resultados (
          id INTEGER PRIMARY KEY AUTOINCREMENT, tarefa TEXT NOT NULL, grupo TEXT NOT NULL,
          sucesso INTEGER NOT NULL, duracao_ms REAL NOT NULL, criado_em REAL NOT NULL)''')
        db.execute('INSERT INTO continuum_resultados(tarefa,grupo,sucesso,duracao_ms,criado_em) VALUES (?,?,?,?,?)',
                   (task_id(task),task['grupo'],int(sucesso),duracao_ms,time.time()))


def avaliar(tarefas, db_path):
    if not tarefas:
        raise ValueError('Nenhuma tarefa fornecida')
    resultados=[]
    for task in tarefas:
        if task.get('grupo') not in ('treino','inedito'):
            raise ValueError('Grupo deve ser treino ou inedito')
        inicio=time.perf_counter()
        try:
            obtido=executar(task)
            ok=obtido==task['esperado']
            erro=None
        except (ValueError, KeyError, TypeError) as exc:
            obtido=None;ok=False;erro=type(exc).__name__
        ms=round((time.perf_counter()-inicio)*1000,3)
        registrar(db_path,task,obtido,ok,ms)
        resultados.append({'id':task_id(task),'grupo':task['grupo'],'sucesso':ok,'duracao_ms':ms,'erro':erro})
    resumo={}
    for grupo in ('treino','inedito'):
        rows=[r for r in resultados if r['grupo']==grupo]
        resumo[grupo]={'total':len(rows),'acertos':sum(r['sucesso'] for r in rows),
                       'taxa':round(sum(r['sucesso'] for r in rows)/len(rows),4) if rows else None}
    return {'resumo':resumo,'resultados':resultados,'metodologia':'Tarefas sintéticas offline; sem aprendizado; não é avaliação de agentes web.'}


def tarefas_exemplo():
    return [
      {'tipo':'normalizar','entrada':'  Bom   DIA ','esperado':'bom dia','grupo':'treino'},
      {'tipo':'somar','entrada':[3,4,5],'esperado':12,'grupo':'treino'},
      {'tipo':'extrair_campos','entrada':{'nome':'Ana','idade':29},'campos':['nome'],'esperado':{'nome':'Ana'},'grupo':'inedito'},
      {'tipo':'normalizar','entrada':'  Olá  MUNDO  ','esperado':'olá mundo','grupo':'inedito'}]

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',default='data/continuum_benchmark.sqlite3')
    parser.add_argument('--tarefas',help='JSON de tarefas; omitir para tarefas sintéticas de demonstração')
    args=parser.parse_args()
    tarefas=json.loads(Path(args.tarefas).read_text(encoding='utf-8')) if args.tarefas else tarefas_exemplo()
    print(json.dumps(avaliar(tarefas,args.db),ensure_ascii=False,indent=2))
