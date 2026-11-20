"""Continuidade visual e evidências de testes para Ashley 1.0.

Os registros são separados por usuário; testes são evidências, não garantias
universais de funcionamento. Nenhum serviço externo é chamado aqui.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

_ROOT = Path(__file__).resolve().parents[2]
_DB = Path(os.getenv("ASHLEY_CONTINUIDADE_DB", str(_ROOT / "ashley_continuidade_visual.db")))
_LOCK = RLock()


def _conectar():
    _DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB), timeout=10)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("""CREATE TABLE IF NOT EXISTS contexto_visual_usuario (
        user_id TEXT PRIMARY KEY,
        descricao TEXT NOT NULL,
        atualizado_em TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS evidencias_teste (
        capacidade TEXT PRIMARY KEY,
        resultado TEXT NOT NULL,
        detalhe TEXT NOT NULL,
        atualizado_em TEXT NOT NULL
    )""")
    return conn


def registrar_visual(user_id, descricao):
    """Registra a última descrição visual recebida para este usuário."""
    if user_id is None or not isinstance(descricao, str) or not descricao.strip():
        return False
    valor = descricao.strip()[:6000]
    agora = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        with _conectar() as conn:
            conn.execute("""INSERT INTO contexto_visual_usuario(user_id, descricao, atualizado_em)
                VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET
                descricao=excluded.descricao, atualizado_em=excluded.atualizado_em""",
                (str(user_id), valor, agora))
    return True


def contexto_visual(user_id):
    """Recupera somente o contexto visual do usuário informado."""
    if user_id is None:
        return ""
    with _LOCK:
        with _conectar() as conn:
            row = conn.execute("SELECT descricao FROM contexto_visual_usuario WHERE user_id=?",
                               (str(user_id),)).fetchone()
    return row[0] if row else ""


def registrar_teste(capacidade, resultado, detalhe=""):
    """Registra uma evidência observada, sem fabricar aprovações."""
    if not isinstance(capacidade, str) or not capacidade.strip():
        return False
    if not isinstance(resultado, str) or not resultado.strip():
        return False
    agora = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        with _conectar() as conn:
            conn.execute("""INSERT INTO evidencias_teste(capacidade, resultado, detalhe, atualizado_em)
                VALUES (?, ?, ?, ?) ON CONFLICT(capacidade) DO UPDATE SET
                resultado=excluded.resultado, detalhe=excluded.detalhe,
                atualizado_em=excluded.atualizado_em""",
                (capacidade.strip(), resultado.strip(), str(detalhe)[:2000], agora))
    return True


def testes_registrados():
    """Retorna o formato esperado por app.core.capacidades.inventario."""
    with _LOCK:
        with _conectar() as conn:
            rows = conn.execute("SELECT capacidade, resultado, detalhe, atualizado_em FROM evidencias_teste").fetchall()
    return {chave: {"resultado": resultado, "detalhe": detalhe, "atualizado_em": quando}
            for chave, resultado, detalhe, quando in rows}
