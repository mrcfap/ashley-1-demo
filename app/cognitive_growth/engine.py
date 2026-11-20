"""Ashley: autonomous deliberation simulation with bounded, auditable self-improvement.
No claim of consciousness, subjective feeling, or AGI. No unreviewed code execution.
"""
from __future__ import annotations
import json, sqlite3, time, uuid, hashlib
from pathlib import Path

EMOTIONS = ('curiosidade','satisfacao','preocupacao','frustracao','empatia')

class CognitiveGrowthEngine:
    def __init__(self, database='data/cognitive_growth.sqlite3'):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, created REAL NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, created REAL NOT NULL, target TEXT NOT NULL, diff TEXT NOT NULL, rationale TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', reviewed REAL);
            CREATE TABLE IF NOT EXISTS goals(id TEXT PRIMARY KEY, created REAL NOT NULL, description TEXT NOT NULL, priority INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'open');""")
    def _db(self):
        return sqlite3.connect(self.database,timeout=10)
    def record(self, kind, payload):
        if not isinstance(payload,dict): raise TypeError('payload must be dict')
        event={'id':str(uuid.uuid4()),'created':time.time(),'kind':str(kind)[:64],'payload':payload}
        with self._db() as db: db.execute('INSERT INTO events VALUES(?,?,?,?)',(event['id'],event['created'],event['kind'],json.dumps(payload,ensure_ascii=False)))
        return event['id']
    def experience(self, text, feedback=0, context=None):
        feedback=max(-1.0,min(1.0,float(feedback)))
        return self.record('experience',{'text':str(text)[:4000],'feedback':feedback,'context':context or {}})
    def emotion_state(self, limit=100):
        with self._db() as db: rows=db.execute("SELECT payload FROM events WHERE kind='experience' ORDER BY created DESC LIMIT ?",(max(1,min(int(limit),500)),)).fetchall()
        feedback=[json.loads(x[0]).get('feedback',0) for x in rows]
        avg=sum(feedback)/len(feedback) if feedback else 0
        # Functional affective signals, not conscious experiences.
        return {'curiosidade':round(0.5+0.3/(1+len(rows)),3),'satisfacao':round(max(0,min(1,0.5+avg/2)),3),'preocupacao':round(max(0,-avg),3),'frustracao':round(max(0,-avg*0.7),3),'empatia':0.7,'samples':len(rows),'nature':'simulated'}
    def add_goal(self, description, priority=5):
        if not 1<=int(priority)<=10:raise ValueError('priority 1..10')
        id=str(uuid.uuid4())
        with self._db() as db:db.execute('INSERT INTO goals(id,created,description,priority) VALUES(?,?,?,?)',(id,time.time(),str(description)[:1000],int(priority)))
        self.record('goal_added',{'id':id})
        return id
    def deliberate(self):
        with self._db() as db:
            goals=db.execute("SELECT id,description,priority FROM goals WHERE status='open' ORDER BY priority DESC,created ASC LIMIT 5").fetchall()
            events=db.execute('SELECT kind FROM events ORDER BY created DESC LIMIT 10').fetchall()
        state=self.emotion_state()
        return {'goals':[{'id':i,'description':d,'priority':p} for i,d,p in goals], 'affective_state':state,'recent_activity':[e[0] for e in events], 'next_step':'review_highest_priority_goal' if goals else 'request_authorized_goal','autonomy':'bounded, no independent external action'}
    def propose_change(self, target, unified_diff, rationale):
        # Store proposal only; never apply/execute code here.
        target=Path(target)
        if target.is_absolute() or '..' in target.parts or target.suffix!='.py' or not str(target).startswith('app/'):
            raise ValueError('Only relative app/*.py targets allowed')
        if len(unified_diff)>100_000:raise ValueError('diff too large')
        id=str(uuid.uuid4())
        with self._db() as db:db.execute('INSERT INTO proposals VALUES(?,?,?,?,?, ?,NULL)',(id,time.time(),str(target),str(unified_diff),str(rationale)[:3000],'pending'))
        self.record('proposal_created',{'id':id,'target':str(target),'sha256':hashlib.sha256(unified_diff.encode()).hexdigest()})
        return id
    def review_proposal(self, proposal_id, approved=False):
        # Approval is a review record, NOT automatic application.
        with self._db() as db:
            cur=db.execute("UPDATE proposals SET status=?,reviewed=? WHERE id=? AND status='pending'",('approved_for_manual_testing' if approved else 'rejected',time.time(),proposal_id))
            if not cur.rowcount:raise ValueError('proposal not found or already reviewed')
        self.record('proposal_reviewed',{'id':proposal_id,'approved':bool(approved)})
    def proposals(self):
        with self._db() as db:rows=db.execute('SELECT id,target,rationale,status FROM proposals ORDER BY created DESC LIMIT 50').fetchall()
        return [dict(zip(('id','target','rationale','status'),r)) for r in rows]
