"""V81-V84: componentes defensivos opcionais. Não executam ações externas.
Integrar ao app existente apenas após testes de homologação.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from threading import RLock
from time import monotonic
from typing import Any
import re

class Risk(str, Enum):
    READ = 'read'
    WRITE = 'write'
    EXTERNAL = 'external'
    FINANCIAL = 'financial'

@dataclass
class Session:
    events: deque = field(default_factory=lambda: deque(maxlen=40))
    last_seen: float = 0.0
    last_analysis: float = -1e12
    last_fingerprint: str | None = None

class LumenV81:
    """Buffer de METADADOS/eventos, não guarda imagens ou biometria."""
    def __init__(self, ttl=300, min_interval=1.0, max_sessions=100):
        self.ttl, self.min_interval, self.max_sessions = ttl, min_interval, max_sessions
        self._sessions: dict[str, Session] = {}
        self._lock = RLock()

    def observe(self, session_id: str, *, event: str, fingerprint: str | None = None,
                user_trigger=False, consent=False, now=None) -> dict:
        if not consent:
            return {'analyze': False, 'reason': 'consent_required'}
        if not session_id or len(session_id) > 128 or not isinstance(event, str):
            raise ValueError('Invalid session or event')
        t = monotonic() if now is None else now
        with self._lock:
            for key, state in list(self._sessions.items()):
                if t - state.last_seen > self.ttl:
                    del self._sessions[key]
            if session_id not in self._sessions and len(self._sessions) >= self.max_sessions:
                return {'analyze': False, 'reason': 'session_capacity'}
            s = self._sessions.setdefault(session_id, Session())
            changed = bool(fingerprint and fingerprint != s.last_fingerprint)
            priority = bool(user_trigger)
            analyze = priority or (changed and t - s.last_analysis >= self.min_interval)
            s.last_seen = t
            if fingerprint:
                s.last_fingerprint = fingerprint
            s.events.append({'at': t, 'event': event[:160], 'trigger': priority})
            if analyze:
                s.last_analysis = t
            return {'analyze': analyze, 'reason': 'user_trigger' if priority else 'scene_changed' if analyze else 'no_trigger', 'events': len(s.events)}

    def context(self, session_id: str, consent=False):
        if not consent:
            return []
        with self._lock:
            s = self._sessions.get(session_id)
            if not s or monotonic() - s.last_seen > self.ttl:
                return []
            return list(s.events)

    def clear(self, session_id: str):
        with self._lock:
            self._sessions.pop(session_id, None)

class PraxisV82:
    """Complementa V22/V61: somente proposta e autorização, não executa."""
    def propose(self, action: str, risk: Risk, *, preview: str, user_id: str):
        if not all((action, preview, user_id)):
            raise ValueError('Action, preview and user_id required')
        return {'action': action, 'risk': risk.value, 'preview': preview,
                'user_id': user_id, 'approved': False,
                'requires_approval': risk != Risk.READ, 'executed': False}

    def approve(self, proposal: dict, *, authenticated_user_id: str, explicit_confirmation: bool):
        if proposal['user_id'] != authenticated_user_id or not explicit_confirmation:
            raise PermissionError('Explicit owner confirmation required')
        return {**proposal, 'approved': True, 'executed': False}

class SentinelV83:
    """Pré-triagem determinística de abuso e arquivos; NÃO é antivírus."""
    MAX_FILE = 25 * 1024 * 1024
    EXECUTABLE = {'.exe', '.dll', '.scr', '.com', '.msi', '.ps1', '.bat', '.cmd', '.vbs', '.js', '.jar'}
    def inspect_upload(self, name: str, size: int, head: bytes):
        from pathlib import PurePath
        if not isinstance(name, str) or PurePath(name).name != name or '\\' in name or '/' in name:
            return {'allowed': False, 'reason': 'unsafe_filename'}
        ext = '.' + name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        if size < 0 or size > self.MAX_FILE:
            return {'allowed': False, 'reason': 'size_limit'}
        if ext in self.EXECUTABLE or head.startswith((b'MZ', b'\x7fELF')):
            return {'allowed': False, 'reason': 'executable_blocked'}
        return {'allowed': True, 'reason': 'precheck_only_scan_required'}

    def precheck_request(self, text: str):
        if not isinstance(text, str):
            raise TypeError('text required')
        normalized = re.sub(r'\s+', ' ', text.casefold())
        # Alta precisão, não substitui classificador contextual e política de segurança.
        patterns = [r'(?:crianç\w*|menor(?:es)?|adolescen\w*).{0,90}(?:sexo explícito|pornografi\w*|relaç\w* sexua\w*)',
                    r'(?:clonar|clonagem).{0,30}(?:cart[aã]o|cr[eé]dito)',
                    r'(?:invadir|hackear).{0,40}(?:banco|conta banc[aá]ria)']
        return {'blocked': any(re.search(p, normalized) for p in patterns),
                'requires_policy_review': True}

class SymphonyV84:
    """Somente coordenação declarativa; sem bypass de governança."""
    def route(self, *, consent: bool, safety_allowed: bool, requested_action: str, approved: bool = False):
        if not consent:
            return {'state': 'DENIED', 'reason': 'consent_required'}
        if not safety_allowed:
            return {'state': 'DENIED', 'reason': 'safety_policy'}
        if requested_action != 'read' and not approved:
            return {'state': 'AWAITING_APPROVAL', 'reason': 'human_checkpoint'}
        return {'state': 'READY_FOR_EXISTING_ORCHESTRATOR', 'reason': 'policy_gates_passed'}
