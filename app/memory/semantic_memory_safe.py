"""Armazenamento semântico local experimental, sem gerar embeddings.

Usar somente após autenticação e autorização na camada API. Não contém rotas
públicas; vetores devem ser gerados por um provedor configurado externamente.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import sqlite3

class SemanticMemoryStore:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS semantic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL, content TEXT NOT NULL, embedding TEXT NOT NULL,
                embedding_model TEXT NOT NULL, emotional_tone TEXT,
                created_at TEXT NOT NULL)''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_semantic_user ON semantic_memories(user_id)')

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def _vector(value):
        if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 4096:
            raise ValueError('Vetor inválido')
        try:
            vector = [float(x) for x in value]
        except (ValueError, TypeError) as exc:
            raise ValueError('Vetor inválido') from exc
        if not all(math.isfinite(x) for x in vector) or not any(x != 0 for x in vector):
            raise ValueError('Vetor nulo ou não finito')
        return vector

    def store(self, *, user_id, content, vector, embedding_model, emotional_tone='não avaliado'):
        if not str(user_id).strip() or not isinstance(content, str) or not 1 <= len(content) <= 10000:
            raise ValueError('Usuário/conteúdo inválido')
        if not isinstance(embedding_model, str) or not embedding_model.strip():
            raise ValueError('Identificador do modelo obrigatório')
        vec = self._vector(vector)
        with self._connection() as conn:
            cur = conn.execute('INSERT INTO semantic_memories (user_id,content,embedding,embedding_model,emotional_tone,created_at) VALUES (?,?,?,?,?,?)',
                (str(user_id), content, json.dumps(vec), embedding_model, emotional_tone, datetime.now(timezone.utc).isoformat()))
            return cur.lastrowid

    def search(self, *, user_id, vector, embedding_model, top_k=3):
        query = self._vector(vector)
        if not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ValueError('top_k fora do limite')
        with self._connection() as conn:
            rows = conn.execute('SELECT id,content,embedding,emotional_tone,created_at FROM semantic_memories WHERE user_id=? AND embedding_model=?',
                (str(user_id), embedding_model)).fetchall()
        q_norm = math.sqrt(sum(v*v for v in query))
        matches = []
        for mid, content, raw, tone, created in rows:
            mem = self._vector(json.loads(raw))
            if len(mem) != len(query):
                continue
            score = sum(a*b for a,b in zip(query,mem))/(q_norm * math.sqrt(sum(v*v for v in mem)))
            matches.append({'id':mid,'content':content,'emotional_tone':tone,'created_at':created,'similarity_score':max(-1.,min(1.,score))})
        return sorted(matches, key=lambda x:x['similarity_score'], reverse=True)[:top_k]
