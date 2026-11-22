"""Armazenamento biométrico opt-in no PostgreSQL com criptografia autenticada.

Nunca grava fotos ou vetores em logs; exige DATABASE_URL e ASHLEY_FACE_ENCRYPTION_KEY.
"""
import io
import os
from typing import Optional
import numpy as np


class PerfilFacialPersistente:
    def __init__(self):
        self.ativo = bool(os.getenv("DATABASE_URL") and os.getenv("ASHLEY_FACE_ENCRYPTION_KEY"))
        self._fernet = None
        if self.ativo:
            from cryptography.fernet import Fernet
            self._fernet = Fernet(os.environ["ASHLEY_FACE_ENCRYPTION_KEY"].encode())

    def _conectar(self):
        import psycopg
        return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=10)

    @staticmethod
    def _schema(conn):
        conn.execute("""CREATE TABLE IF NOT EXISTS facial_profiles (
            user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            encrypted_features BYTEA NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")

    def salvar(self, user_id: int, matriz: np.ndarray) -> None:
        if not self.ativo:
            raise RuntimeError("Persistência facial não configurada")
        matriz = np.asarray(matriz, dtype=np.float32)
        if matriz.ndim != 2 or matriz.shape[1] != 128 or not len(matriz) or not np.isfinite(matriz).all():
            raise ValueError("Assinaturas faciais inválidas")
        buffer = io.BytesIO()
        np.save(buffer, matriz, allow_pickle=False)
        cifrado = self._fernet.encrypt(buffer.getvalue())
        with self._conectar() as conn:
            self._schema(conn)
            conn.execute("""INSERT INTO facial_profiles (user_id, encrypted_features) VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING""", (int(user_id), cifrado))

    def carregar(self, user_id: int) -> Optional[np.ndarray]:
        if not self.ativo:
            return None
        with self._conectar() as conn:
            self._schema(conn)
            row = conn.execute("SELECT encrypted_features FROM facial_profiles WHERE user_id = %s", (int(user_id),)).fetchone()
        if row is None:
            return None
        matriz = np.load(io.BytesIO(self._fernet.decrypt(bytes(row[0]))), allow_pickle=False)
        if matriz.ndim != 2 or matriz.shape[1] != 128 or not np.isfinite(matriz).all():
            raise ValueError("Perfil facial persistido inválido")
        return matriz

    def remover(self, user_id: int) -> None:
        if self.ativo:
            with self._conectar() as conn:
                self._schema(conn)
                conn.execute("DELETE FROM facial_profiles WHERE user_id = %s", (int(user_id),))
