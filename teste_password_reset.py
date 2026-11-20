
"""Offline test: isolated database, no SMTP and no user data changed."""
import hashlib
import secrets
import tempfile
import time
from pathlib import Path
from contextlib import closing

from fastapi import HTTPException
from app.security import auth, password_reset

with tempfile.TemporaryDirectory() as directory:
    original = auth.DB
    auth.DB = Path(directory) / 'test_auth.sqlite3'
    try:
        with closing(auth.connect()) as conn, conn:
            salt = secrets.token_bytes(16)
            conn.execute(
                'INSERT INTO users(email,salt,digest) VALUES(?,?,?)',
                ('teste@example.invalid', salt,
                 auth.digest('SenhaOriginalSegura123', salt))
            )
            user_id = conn.execute(
                'SELECT id FROM users WHERE email=?',
                ('teste@example.invalid',)
            ).fetchone()[0]

            session_token = secrets.token_urlsafe(32)
            conn.execute(
                'INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)',
                (
                    hashlib.sha256(session_token.encode()).hexdigest(),
                    user_id,
                    int(time.time()) + 3600
                )
            )

            password_reset._table(conn)
            token = secrets.token_urlsafe(32)
            conn.execute(
                'INSERT INTO password_resets(token_hash,user_id,expires,used) VALUES(?,?,?,0)',
                (
                    hashlib.sha256(token.encode()).hexdigest(),
                    user_id,
                    int(time.time()) + 900
                )
            )

        result = password_reset.confirm_reset(
            token, 'SenhaNovaSegura123'
        )
        assert result['ok'] is True

        assert auth.login(
            'teste@example.invalid',
            'SenhaNovaSegura123'
        )['access_token']

        try:
            password_reset.confirm_reset(
                token, 'OutraSenhaSegura123'
            )
        except HTTPException as exc:
            assert exc.status_code == 400
        else:
            raise AssertionError('Token foi reutilizado')

        try:
            auth.identity(session_token)
        except HTTPException as exc:
            assert exc.status_code == 401
        else:
            raise AssertionError('Sessao antiga permaneceu ativa')

    finally:
        auth.DB = original

print('Recuperacao de senha: testes locais aprovados')
