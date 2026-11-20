from contextlib import closing
"""LEGACY V58 — objetivos e revisões persistentes, sem acompanhamento proativo externo."""
import sqlite3,json
from datetime import datetime,timezone

def now():return datetime.now(timezone.utc).isoformat()
class LegacyTracker:
    def __init__(self,db_path):
        self.db_path=str(db_path)
        with closing(sqlite3.connect(self.db_path)) as connection, connection as db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY,owner TEXT NOT NULL, objective TEXT NOT NULL,metric TEXT NOT NULL,baseline REAL NOT NULL,target REAL NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',consent INTEGER NOT NULL,created_at TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY,goal_id INTEGER NOT NULL,observed REAL NOT NULL,note TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(goal_id) REFERENCES goals(id))")
    def create(self,owner,objective,metric,baseline,target,consent=False):
        if not consent:raise PermissionError('consentimento necessário')
        if not all(isinstance(x,str) and x.strip() for x in (owner,objective,metric)):raise ValueError('dados inválidos')
        if any(type(x) not in (int,float) for x in (baseline,target)):raise ValueError('métricas numéricas necessárias')
        with closing(sqlite3.connect(self.db_path)) as connection, connection as db:
            return db.execute('INSERT INTO goals(owner,objective,metric,baseline,target,consent,created_at) VALUES(?,?,?,?,?,?,?)',
                (owner,objective,metric,baseline,target,1,now())).lastrowid
    def review(self,owner,goal_id,observed,note):
        if type(observed) not in (int,float) or not isinstance(note,str):raise ValueError('revisão inválida')
        with closing(sqlite3.connect(self.db_path)) as connection, connection as db:
            row=db.execute('SELECT status FROM goals WHERE id=? AND owner=?',(goal_id,owner)).fetchone()
            if not row or row[0]!='ACTIVE':raise ValueError('objetivo não encontrado ou pausado')
            db.execute('INSERT INTO reviews(goal_id,observed,note,created_at) VALUES(?,?,?,?)',(goal_id,observed,note,now()))
    def status(self,owner,goal_id):
        with closing(sqlite3.connect(self.db_path)) as connection, connection as db:
            db.row_factory=sqlite3.Row
            goal=db.execute('SELECT id,objective,metric,baseline,target,status FROM goals WHERE id=? AND owner=?',(goal_id,owner)).fetchone()
            if goal is None:return None
            review=db.execute('SELECT observed,note,created_at FROM reviews WHERE goal_id=? ORDER BY id DESC LIMIT 1',(goal_id,)).fetchone()
            return {'goal':dict(goal),'last_review':dict(review) if review else None,'goal_achieved_verified':False,
                    'note':'observações declaradas; resultados externos não verificados'}
    def set_status(self,owner,goal_id,status):
        if status not in ('ACTIVE','PAUSED','CLOSED'):raise ValueError('status inválido')
        with closing(sqlite3.connect(self.db_path)) as connection, connection as db:
            cur=db.execute('UPDATE goals SET status=? WHERE id=? AND owner=?',(status,goal_id,owner))
            if not cur.rowcount:raise ValueError('objetivo não encontrado')
