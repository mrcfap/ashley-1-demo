"""Implementações locais determinísticas. Não executam integrações externas nem alteram agendas reais."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def utcnow(): return datetime.now(timezone.utc).isoformat()

class EngineStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, owner TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, created TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_records_owner_kind ON records(owner,kind);
            CREATE TABLE IF NOT EXISTS permissions(owner TEXT NOT NULL, scope TEXT NOT NULL, granted INTEGER NOT NULL, updated TEXT NOT NULL, PRIMARY KEY(owner,scope));
            CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, owner TEXT NOT NULL, action TEXT NOT NULL, digest TEXT NOT NULL, created TEXT NOT NULL);
            ''')
    @contextmanager
    def db(self):
        conn = sqlite3.connect(str(self.path), timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            with conn: yield conn
        finally: conn.close()
    def add(self, owner, kind, payload):
        rid = str(uuid4())
        with self.db() as c:
            c.execute('INSERT INTO records VALUES(?,?,?,?,?)', (rid,str(owner),kind,json.dumps(payload,ensure_ascii=False),utcnow()))
        return {'id':rid,'kind':kind,**payload}
    def list(self,owner,kind):
        with self.db() as c:
            rows=c.execute('SELECT * FROM records WHERE owner=? AND kind=? ORDER BY created DESC',(str(owner),kind)).fetchall()
        return [{'id':r['id'],'kind':r['kind'],**json.loads(r['payload'])} for r in rows]
    def get(self,owner,kind,rid):
        with self.db() as c:
            r=c.execute('SELECT * FROM records WHERE owner=? AND kind=? AND id=?',(str(owner),kind,rid)).fetchone()
        return None if r is None else {'id':r['id'],'kind':r['kind'],**json.loads(r['payload'])}
    def grant(self,owner,scope,granted):
        with self.db() as c: c.execute('INSERT INTO permissions VALUES(?,?,?,?) ON CONFLICT(owner,scope) DO UPDATE SET granted=excluded.granted,updated=excluded.updated',(str(owner),scope,int(granted),utcnow()))
        self.audit(owner,'permission_change',{'scope':scope,'granted':bool(granted)})
        return {'scope':scope,'granted':bool(granted)}
    def allowed(self,owner,scope):
        with self.db() as c: r=c.execute('SELECT granted FROM permissions WHERE owner=? AND scope=?',(str(owner),scope)).fetchone()
        return bool(r and r['granted'])
    def audit(self,owner,action,data):
        # Somente resumo criptográfico; não grava o conteúdo potencialmente sensível.
        digest=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        eid=str(uuid4())
        with self.db() as c: c.execute('INSERT INTO events VALUES(?,?,?,?,?)',(eid,str(owner),action,digest,utcnow()))
        return {'event_id':eid,'action':action,'digest':digest}
    def events(self,owner):
        with self.db() as c: rows=c.execute('SELECT * FROM events WHERE owner=? ORDER BY created DESC',(str(owner),)).fetchall()
        return [dict(r) for r in rows]

# V66 - evidência explícita, sem alegar verificação automática.
def aletheia(claim, sources):
    valid=[s for s in sources if s.get('reference') and s.get('excerpt') and s.get('trusted') is True]
    return {'claim':claim,'status':'EVIDENCIA_DECLARADA_REQUER_REVISAO' if valid else 'NAO_VERIFICADO',
            'usable_for_official_report':False,'sources_considered':len(sources),'qualified_sources':len(valid),
            'warning':'Fontes declaradas não foram conferidas independentemente. Revisão humana obrigatória.'}

# V67 - plano de reorganização proposto, jamais executado sem aprovação.
def chronos(tasks, energy, consent):
    if not consent: return {'status':'CONSENTIMENTO_NECESSARIO','proposals':[],'executed':0}
    if not 0 <= energy <= 10: raise ValueError('Energia fora da faixa 0-10')
    proposals=[{'task_id':t['id'],'suggestion':'REVISAR_PRAZO_COM_RESPONSAVEL','reason':'Energia autodeclarada baixa'}
               for t in tasks if energy <= 3 and t.get('critical') is False]
    return {'status':'SUGESTOES_PENDENTES_DE_APROVACAO','proposals':proposals,'executed':0}

# V68 - catálogo MCP controlado; nenhuma execução remota.
def omni_catalog(tools):
    return {'tools':[{'name':t['name'],'scope':t['scope'],'mode':'CATALOGO_APENAS'} for t in tools],
            'remote_calls':0,'note':'Integração real exige conector configurado, autenticação e testes.'}

# V69 - autorização por escopo e bloqueio padrão.
def ethos(store, owner, scope, critical=False, confirmed=False):
    authorized=store.allowed(owner,scope) and (not critical or confirmed)
    audit=store.audit(owner,'authorization_check',{'scope':scope,'critical':critical,'authorized':authorized})
    return {'allowed':authorized,'reason':'AUTORIZADO' if authorized else 'BLOQUEADO_SEM_PERMISSAO_OU_CONFIRMACAO',**audit}

# V70 - projeto de impacto: planejamento sem alegar resultado social comprovado.
def impact(store, owner, title, milestones):
    return store.add(owner,'impact',{'title':title,'milestones':[{'description':x,'status':'PLANEJADO'} for x in milestones],
                                     'measured_impact':None,'status':'PLANEJADO'})

# V73 - trilha auditável de operações, sem armazenar payload.
def provenance(store, owner): return {'events':store.events(owner),'integrity_scope':'DIGEST_POR_EVENTO_SEM_ENCADEAMENTO'}

# V74 - circuito de segurança para tarefas potencialmente irreversíveis.
def circuit_breaker(risk, approved, dry_run=True):
    if risk not in ('low','medium','high'): raise ValueError('Risco inválido')
    allowed=risk=='low' or (approved and risk=='medium')
    return {'allowed_to_plan':allowed,'allowed_to_execute':False,'dry_run':True,
            'reason':'ALTO_RISCO_EXIGE_FLUXO_SEPARADO' if risk=='high' else ('APROVACAO_PENDENTE' if not allowed else 'SOMENTE_SIMULACAO')}

# V75 - painel de prontidão, sem prometer certificação de produção.
def readiness(checks):
    required=('authentication','tenant_isolation','consent','tests','observability','rollback')
    missing=[k for k in required if checks.get(k) is not True]
    return {'ready_for_production':not missing,'missing':missing,
            'note':'Autoavaliação declarativa; requer validação externa antes de produção.'}
