"""Extensões V52 isoladas: grounding, memória contextual e políticas.
Não registra rotas, não acessa a rede sem provedor explícito e não executa código.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import re
import sqlite3
from pathlib import Path
from typing import Callable


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Evidence:
    title: str
    url: str
    snippet: str
    published_at: str | None = None


class GroundingService:
    """Provedor injetável deve devolver uma lista de Evidence; não valida verdade por si."""
    def __init__(self, database: str, provider: Callable[[str], list[Evidence]], ttl_seconds: int = 900):
        if ttl_seconds < 1:
            raise ValueError('TTL deve ser positivo')
        self.database = database
        self.provider = provider
        self.ttl = ttl_seconds
        with sqlite3.connect(database) as db:
            db.execute('CREATE TABLE IF NOT EXISTS grounding_cache (query TEXT PRIMARY KEY, fetched_at TEXT NOT NULL, evidence TEXT NOT NULL)')

    def search(self, query: str) -> dict:
        query = query.strip()
        if not query or len(query) > 500:
            raise ValueError('Consulta inválida')
        with sqlite3.connect(self.database) as db:
            row = db.execute('SELECT fetched_at, evidence FROM grounding_cache WHERE query=?', (query,)).fetchone()
        if row:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(row[0])
            if timedelta(0) <= age < timedelta(seconds=self.ttl):
                return {'query': query, 'source': 'cache', 'fetched_at': row[0], 'evidence': json.loads(row[1])}
        evidence = self.provider(query)
        if not isinstance(evidence, list) or any(not isinstance(e, Evidence) for e in evidence):
            raise ValueError('Provedor retornou evidências inválidas')
        from urllib.parse import urlsplit
        results = []
        for e in evidence[:20]:
            parsed = urlsplit(e.url)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                continue
            results.append({'title': e.title[:300], 'url': e.url, 'snippet': e.snippet[:1500], 'published_at': e.published_at})
        fetched = utcnow()
        with sqlite3.connect(self.database) as db:
            db.execute('INSERT OR REPLACE INTO grounding_cache VALUES (?, ?, ?)', (query, fetched, json.dumps(results, ensure_ascii=False)))
        return {'query': query, 'source': 'provider', 'fetched_at': fetched, 'evidence': results}


class ContextStore:
    """Memória por usuário e sessão, com checkpoints e recuperação textual.
    Não é janela nativa ultra-longa nem busca vetorial; integrar embeddings depois.
    """
    def __init__(self, database: str):
        self.database = database
        with sqlite3.connect(database) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS context_chunks (
                id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, session_id TEXT NOT NULL,
                content TEXT NOT NULL, metadata TEXT NOT NULL, created_at TEXT NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS checkpoints (
                user_id TEXT NOT NULL, session_id TEXT NOT NULL, state TEXT NOT NULL,
                updated_at TEXT NOT NULL, PRIMARY KEY(user_id,session_id))''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_context_scope ON context_chunks(user_id,session_id,id)')

    @staticmethod
    def _scope(user_id: str, session_id: str):
        if not user_id.strip() or not session_id.strip():
            raise ValueError('Usuário e sessão obrigatórios')

    def ingest(self, user_id: str, session_id: str, content: str, metadata: dict | None = None) -> int:
        self._scope(user_id, session_id)
        if not content.strip() or len(content) > 100_000:
            raise ValueError('Conteúdo vazio ou excessivo; divida em blocos')
        with sqlite3.connect(self.database) as db:
            cur = db.execute('INSERT INTO context_chunks(user_id,session_id,content,metadata,created_at) VALUES (?,?,?,?,?)',
                             (user_id, session_id, content, json.dumps(metadata or {}, ensure_ascii=False), utcnow()))
            return cur.lastrowid

    def search(self, user_id: str, session_id: str, keyword: str, limit: int = 5) -> list[dict]:
        self._scope(user_id, session_id)
        if not keyword.strip() or not 1 <= limit <= 30:
            raise ValueError('Termo ou limite inválido')
        # LIKE parametrizado; escapar curingas para busca literal.
        escaped = keyword.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        with sqlite3.connect(self.database) as db:
            rows = db.execute('''SELECT id,content,metadata,created_at FROM context_chunks
                WHERE user_id=? AND session_id=? AND content LIKE ? ESCAPE '\\'
                ORDER BY id DESC LIMIT ?''', (user_id, session_id, '%' + escaped + '%', limit)).fetchall()
        return [{'id': r[0], 'content': r[1], 'metadata': json.loads(r[2]), 'created_at': r[3]} for r in rows]

    def save_checkpoint(self, user_id: str, session_id: str, state: dict) -> None:
        self._scope(user_id, session_id)
        payload = json.dumps(state, ensure_ascii=False)
        if len(payload) > 200_000:
            raise ValueError('Checkpoint excessivo')
        with sqlite3.connect(self.database) as db:
            db.execute('INSERT OR REPLACE INTO checkpoints VALUES (?,?,?,?)', (user_id, session_id, payload, utcnow()))

    def load_checkpoint(self, user_id: str, session_id: str) -> dict | None:
        self._scope(user_id, session_id)
        with sqlite3.connect(self.database) as db:
            row = db.execute('SELECT state FROM checkpoints WHERE user_id=? AND session_id=?', (user_id, session_id)).fetchone()
        return json.loads(row[0]) if row else None


class ExecutionGate:
    """Camada de política preventiva, não substitui sandbox real ou autenticação."""
    def __init__(self, allowed_actions: set[str] | None = None):
        self.allowed_actions = allowed_actions or {'read_memory', 'search_web', 'draft_document'}
        self.sensitive = {'execute_code', 'modify_files', 'send_email', 'deploy', 'delete_data', 'financial_transaction'}

    def evaluate(self, action: str, *, authenticated: bool, approved: bool = False) -> dict:
        reasons = []
        if not authenticated:
            reasons.append('autenticacao_obrigatoria')
        if action not in self.allowed_actions:
            reasons.append('acao_nao_autorizada_na_politica')
        if action in self.sensitive and not approved:
            reasons.append('aprovacao_explicita_obrigatoria')
        return {'allowed': not reasons, 'action': action, 'reasons': reasons}
