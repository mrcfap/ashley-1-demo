from contextlib import closing
"""FORTRESS V57 — infraestrutura experimental; não substitui autenticação ou sandbox de SO."""
import time,sqlite3,json,hashlib,ast,os
from pathlib import Path
from datetime import datetime,timezone

class CircuitBreaker:
    def __init__(self, threshold=3, recovery_seconds=30, clock=None):
        if threshold<1 or recovery_seconds<0: raise ValueError('configuração inválida')
        self.threshold=threshold;self.recovery_seconds=recovery_seconds;self.clock=clock or time.monotonic
        self.failures=0;self.opened_at=None;self.probing=False
    @property
    def state(self):
        if self.opened_at is None:return 'CLOSED'
        return 'HALF_OPEN' if self.clock()-self.opened_at>=self.recovery_seconds else 'OPEN'
    def allow(self):
        s=self.state
        if s=='CLOSED':return True
        if s=='OPEN' or self.probing:return False
        self.probing=True;return True
    def success(self):
        self.failures=0;self.opened_at=None;self.probing=False
    def failure(self):
        self.failures+=1
        if self.probing or self.failures>=self.threshold:self.opened_at=self.clock()
        self.probing=False

class MemoryBudget:
    """Planeja seleção de trechos por orçamento aproximado; nunca exclui originais."""
    def select(self, chunks, max_chars, protected_ids=()):
        if not isinstance(max_chars,int) or max_chars<0:raise ValueError('orçamento inválido')
        protected=set(protected_ids);chosen=[];used=0
        for item in chunks:
            if not isinstance(item,dict) or 'id' not in item or not isinstance(item.get('text'),str):raise ValueError('trecho inválido')
        for item in chunks:
            if item['id'] in protected:
                if used+len(item['text'])>max_chars:raise ValueError('informação crítica excede orçamento: pedir ampliação')
                chosen.append(item);used+=len(item['text'])
        for item in reversed(chunks):
            if item['id'] in protected:continue
            if used+len(item['text'])<=max_chars:
                chosen.append(item);used+=len(item['text'])
        return {'chunks':chosen,'chars':used,'omitted':len(chunks)-len(chosen),'token_count_exact':False}

class Telemetry:
    def __init__(self,db_path):
        self.db_path=str(db_path)
        with closing(sqlite3.connect(self.db_path)) as connection, connection as db:
            db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, ts TEXT, trace_id TEXT, engine TEXT, event TEXT, detail TEXT)')
    def emit(self,trace_id,engine,event,detail=None):
        if not all(isinstance(x,str) and x.strip() for x in (trace_id,engine,event)):raise ValueError('campos inválidos')
        # Nunca armazenar mensagens completas ou tokens de acesso.
        detail=detail or {}
        allowed={k:v for k,v in detail.items() if k in ('duration_ms','status','attempts','error_code') and isinstance(v,(int,float,str,bool))}
        with closing(sqlite3.connect(self.db_path)) as connection, connection as db:
            db.execute('INSERT INTO events(ts,trace_id,engine,event,detail) VALUES (?,?,?,?,?)',
                (datetime.now(timezone.utc).isoformat(),trace_id,engine,event,json.dumps(allowed)))
    def by_trace(self,trace_id):
        with closing(sqlite3.connect(self.db_path)) as connection, connection as db:
            return [dict(ts=r[0],engine=r[1],event=r[2],detail=json.loads(r[3])) for r in db.execute(
                'SELECT ts,engine,event,detail FROM events WHERE trace_id=? ORDER BY id',(trace_id,))]

class SafeRelease:
    """Valida sintaxe e hash de snapshot; NÃO executa código nem faz deploy."""
    def check_python(self,source):
        try:ast.parse(source);return {'syntax_ok':True}
        except SyntaxError as exc:return {'syntax_ok':False,'line':exc.lineno,'error':exc.msg}
    def fingerprint(self,data):
        if not isinstance(data,bytes):raise TypeError('bytes exigidos')
        return hashlib.sha256(data).hexdigest()
    def rollback_plan(self,previous_hash,failed_hash,authorized=False):
        if not authorized:return {'action':'require_authorization'}
        if not all(isinstance(x,str) and len(x)==64 for x in (previous_hash,failed_hash)):
            raise ValueError('hash inválido')
        return {'action':'restore_previous_snapshot','snapshot_sha256':previous_hash,'failed_sha256':failed_hash,
                'executed':False,'requires_external_deployment_manager':True}
