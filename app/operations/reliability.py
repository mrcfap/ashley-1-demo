"""Ferramentas de confiabilidade. Sem executar código gerado no processo da API."""
import sqlite3, logging, json, os, time
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logging(folder='logs'):
    Path(folder).mkdir(parents=True, exist_ok=True)
    logger=logging.getLogger('ashley.operations')
    if not logger.handlers:
        handler=RotatingFileHandler(Path(folder)/'operations.jsonl',maxBytes=2_000_000,backupCount=5,encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def audit(event, **fields):
    safe={k:v for k,v in fields.items() if k not in ('password','token','api_key','prompt','message','content')}
    configure_logging().info(json.dumps({'timestamp':time.time(),'event':event,**safe},default=str,ensure_ascii=False))

def connect_db(path):
    db=sqlite3.connect(path,timeout=30,isolation_level='DEFERRED')
    db.execute('PRAGMA busy_timeout=30000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    return db

def execute_write(path, sql, params=()):
    for attempt in range(5):
        try:
            with connect_db(path) as db:
                return db.execute(sql,params).rowcount
        except sqlite3.OperationalError as exc:
            if 'locked' not in str(exc).lower() or attempt==4: raise
            time.sleep(.05*2**attempt)
