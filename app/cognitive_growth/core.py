"""Núcleo experimental: estados afetivos simulados, reflexão e propostas auditáveis.
Não implica consciência, sentimentos reais ou AGI. Não executa nem altera código.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone
import json, math, sqlite3, hashlib

@dataclass
class EmotionalState:
    curiosity: float = .5
    confidence: float = .5
    concern: float = .2
    satisfaction: float = .5
    def update(self, success: bool | None = None, novelty: float = .5, risk: float = 0.0):
        clamp=lambda x:max(0.,min(1.,float(x)))
        novelty, risk=clamp(novelty),clamp(risk)
        self.curiosity=clamp(.8*self.curiosity+.2*novelty)
        self.concern=clamp(.8*self.concern+.2*risk)
        if success is not None:
            self.confidence=clamp(.85*self.confidence+.15*float(success))
            self.satisfaction=clamp(.8*self.satisfaction+.2*float(success))
        return asdict(self)

class CognitiveGrowth:
    """Persistência local; reflexão e propostas, sem autoexecução/autodeploy."""
    def __init__(self, database: str | Path):
        self.database=str(database)
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, ts TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL)')
            db.execute("CREATE TABLE IF NOT EXISTS proposals (id TEXT PRIMARY KEY, ts TEXT NOT NULL, title TEXT NOT NULL, rationale TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending')")
    def _connect(self):
        db=sqlite3.connect(self.database,timeout=10)
        return db
    def record(self,kind: str, payload: dict):
        if kind not in {'observation','feedback','reflection','emotion'}: raise ValueError('tipo não permitido')
        data=json.dumps(payload,ensure_ascii=False,sort_keys=True)
        if len(data)>20000: raise ValueError('evento muito grande')
        with self._connect() as db:
            db.execute('INSERT INTO events(ts,kind,payload) VALUES(?,?,?)',(datetime.now(timezone.utc).isoformat(),kind,data))
    def reflect(self, limit: int=30):
        limit=max(1,min(int(limit),100))
        with self._connect() as db:
            rows=db.execute('SELECT kind,payload FROM events ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        feedback=[json.loads(x) for k,x in rows if k=='feedback']
        good=sum(bool(x.get('success')) for x in feedback)
        summary={'events_reviewed':len(rows),'feedback_count':len(feedback),'success_rate':round(good/len(feedback),3) if feedback else None,'recommendation':'Coletar feedback verificável' if not feedback else ('Revisar falhas antes de expandir' if good<len(feedback) else 'Manter testes de regressão')}
        self.record('reflection',summary)
        return summary
    def propose(self,title:str,rationale:str):
        title=title.strip(); rationale=rationale.strip()
        if not 5<=len(title)<=150 or not 10<=len(rationale)<=4000: raise ValueError('proposta inválida')
        ts=datetime.now(timezone.utc).isoformat()
        pid=hashlib.sha256((ts+title+rationale).encode()).hexdigest()[:16]
        with self._connect() as db:db.execute('INSERT INTO proposals(id,ts,title,rationale,status) VALUES(?,?,?,?,?)',(pid,ts,title,rationale,'pending'))
        return {'id':pid,'status':'pending','requires_human_review':True}
    def list_proposals(self):
        with self._connect() as db:
            return [{'id':a,'title':b,'rationale':c,'status':d} for a,b,c,d in db.execute('SELECT id,title,rationale,status FROM proposals ORDER BY ts DESC').fetchall()]
