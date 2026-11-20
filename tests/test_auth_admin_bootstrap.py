import os
from unittest.mock import patch

from app.security import auth


def test_sqlite_bootstrap_creates_admin_and_regular_users_are_not_admin(tmp_path):
    db = tmp_path / "auth.sqlite3"
    with patch.object(auth, "DB", db), patch.dict(os.environ, {"DATABASE_URL": ""}):
        admin_id = auth.create(
            "admin@example.test",
            "SenhaSegura123!",
            "Administrador Teste",
            "1980-01-01",
        )
        admin = auth.profile(admin_id)
        assert admin["is_admin"] is True

        regular = auth.register_user(
            "user@example.test",
            "SenhaSegura123!",
            "Usuário Teste",
            "1990-01-01",
        )
        profile = auth.profile(regular["user_id"])
        assert profile["is_admin"] is False
