import pytest
from app.evolution.continuous_agent_architecture import ContinuousEvolution, ROLES


def test_observe_persists_and_is_idempotent(tmp_path):
    engine = ContinuousEvolution(tmp_path)
    args = ("vision_latency", "Respostas lentas", "Fila excessiva", "Menor latência", "Medir p95 em ambiente de testes")
    first = engine.observe(*args)
    second = engine.observe(*args)
    assert first["identifier"] == second["identifier"]
    assert first["status"] == "pending_human_review"
    assert len(engine.list_pending()) == 1
    assert "etica_privacidade" in ROLES


def test_protected_targets(tmp_path):
    engine = ContinuousEvolution(tmp_path)
    with pytest.raises(PermissionError):
        engine.observe("security_auth", "a", "b", "c", "d")
    with pytest.raises(PermissionError):
        engine.prepare_code_proposal("app/security/auth.py", "melhorar", "codigo")


def test_no_automatic_patch_application(tmp_path):
    engine = ContinuousEvolution(tmp_path)
    candidate = engine.prepare_code_proposal("app/vision/latency.py", "melhorar", "# candidato")
    assert candidate["status"] == "pending_review"
    assert not (tmp_path / "app/vision/latency.py").exists()
