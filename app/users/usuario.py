import sqlite3
import hashlib
import secrets
from datetime import datetime, timezone
from pathlib import Path


class GerenciadorUsuarios:
    """
    Gerencia os usuários da ASHLEY 1.0.

    Responsabilidades:
    - criar a tabela de usuários
    - cadastrar novos usuários
    - impedir e-mails duplicados
    - armazenar senha de forma protegida
    - localizar usuários
    - autenticar login
    - registrar último acesso
    """

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )
        self._criar_tabela()

    def conectar(self):
        return sqlite3.connect(self.db_path)

    def _criar_tabela(self):
        with self.conectar() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    preferred_name TEXT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    active INTEGER NOT NULL DEFAULT 1
                )
            """)

            db.commit()

    def _normalizar_email(self, email):
        return (email or "").strip().lower()

    def _gerar_hash_senha(
        self,
        senha,
        salt=None
    ):
        """
        Gera hash da senha utilizando PBKDF2-HMAC-SHA256.
        A senha original não é armazenada.
        """

        if salt is None:
            salt = secrets.token_hex(32)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode("utf-8"),
            salt.encode("utf-8"),
            600000
        ).hex()

        return password_hash, salt

    def cadastrar_usuario(
        self,
        nome,
        email,
        senha,
        nome_preferido=None
    ):
        nome = (nome or "").strip()
        email = self._normalizar_email(email)
        nome_preferido = (
            nome_preferido or nome
        ).strip()

        if not nome:
            return {
                "sucesso": False,
                "erro": "O nome é obrigatório."
            }

        if not email:
            return {
                "sucesso": False,
                "erro": "O e-mail é obrigatório."
            }

        if not senha or len(senha) < 8:
            return {
                "sucesso": False,
                "erro": (
                    "A senha deve possuir "
                    "pelo menos 8 caracteres."
                )
            }

        with self.conectar() as db:
            existente = db.execute("""
                SELECT id
                FROM users
                WHERE email = ?
            """, (email,)).fetchone()

            if existente:
                return {
                    "sucesso": False,
                    "erro": (
                        "Já existe um usuário "
                        "cadastrado com este e-mail."
                    )
                }

        password_hash, salt = (
            self._gerar_hash_senha(senha)
        )

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        with self.conectar() as db:
            cursor = db.execute("""
                INSERT INTO users (
                    name,
                    preferred_name,
                    email,
                    password_hash,
                    password_salt,
                    created_at,
                    last_login,
                    active
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, 1)
            """, (
                nome,
                nome_preferido,
                email,
                password_hash,
                salt,
                agora
            ))

            db.commit()

            user_id = cursor.lastrowid

        return {
            "sucesso": True,
            "usuario": {
                "id": user_id,
                "nome": nome,
                "nome_preferido": nome_preferido,
                "email": email
            }
        }

    def buscar_usuario_por_email(
        self,
        email
    ):
        email = self._normalizar_email(email)

        with self.conectar() as db:
            usuario = db.execute("""
                SELECT
                    id,
                    name,
                    preferred_name,
                    email,
                    created_at,
                    last_login,
                    active
                FROM users
                WHERE email = ?
            """, (email,)).fetchone()

        if not usuario:
            return None

        return {
            "id": usuario[0],
            "nome": usuario[1],
            "nome_preferido": usuario[2],
            "email": usuario[3],
            "criado_em": usuario[4],
            "ultimo_login": usuario[5],
            "ativo": bool(usuario[6])
        }

    def autenticar(
        self,
        email,
        senha
    ):
        email = self._normalizar_email(email)

        with self.conectar() as db:
            usuario = db.execute("""
                SELECT
                    id,
                    name,
                    preferred_name,
                    email,
                    password_hash,
                    password_salt,
                    active
                FROM users
                WHERE email = ?
            """, (email,)).fetchone()

        if not usuario:
            return {
                "sucesso": False,
                "erro": "E-mail ou senha inválidos."
            }

        if not usuario[6]:
            return {
                "sucesso": False,
                "erro": "Usuário desativado."
            }

        hash_informado, _ = (
            self._gerar_hash_senha(
                senha,
                usuario[5]
            )
        )

        if not secrets.compare_digest(
            hash_informado,
            usuario[4]
        ):
            return {
                "sucesso": False,
                "erro": "E-mail ou senha inválidos."
            }

        agora = datetime.now(
            timezone.utc
        ).isoformat()

        with self.conectar() as db:
            db.execute("""
                UPDATE users
                SET last_login = ?
                WHERE id = ?
            """, (
                agora,
                usuario[0]
            ))

            db.commit()

        return {
            "sucesso": True,
            "usuario": {
                "id": usuario[0],
                "nome": usuario[1],
                "nome_preferido": usuario[2],
                "email": usuario[3]
            }
        }