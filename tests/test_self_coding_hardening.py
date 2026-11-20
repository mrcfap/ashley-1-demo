import os
import sys
import pytest

from app.evolution.self_coding_engine import SelfCodingEngine


def make_engine(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app").mkdir()
    (project / "app" / "sample.py").write_text("VALUE = 1\n", encoding="utf-8")
    return SelfCodingEngine(project), project


def test_workspace_must_be_created_by_engine(tmp_path):
    engine, _ = make_engine(tmp_path)
    with pytest.raises(ValueError):
        engine.validar_python(tmp_path)


def test_proposal_id_cannot_escape_workspace_root(tmp_path):
    engine, _ = make_engine(tmp_path)
    with pytest.raises(ValueError):
        engine.criar_workspace("../outside")


def test_candidate_changes_are_python_only(tmp_path):
    engine, project = make_engine(tmp_path)
    workspace = engine.criar_workspace("proposal_1")
    with pytest.raises(ValueError):
        engine.aplicar_conteudo_candidato(workspace, "README.md", "changed")


def test_test_runner_does_not_inherit_secrets(tmp_path, monkeypatch):
    engine, _ = make_engine(tmp_path)
    workspace = engine.criar_workspace("proposal_2")
    monkeypatch.setenv("ASHLEY_TEST_SECRET", "must-not-leak")
    (workspace / "probe.py").write_text(
        "import os\nprint('SECRET_PRESENT=' + str('ASHLEY_TEST_SECRET' in os.environ))\n",
        encoding="utf-8",
    )
    result = engine.executar_testes(
        workspace, comandos=[[sys.executable, "probe.py"]]
    )
    assert result["ok"] is True
    assert "SECRET_PRESENT=False" in result["resultados"][0]["stdout"]


def test_test_runner_rejects_external_workspace(tmp_path):
    engine, _ = make_engine(tmp_path)
    with pytest.raises(ValueError):
        engine.executar_testes(tmp_path, comandos=[[sys.executable, "-m", "compileall"]])


def test_workspace_excludes_env_backups_and_biometric_profiles(tmp_path):
    engine, project = make_engine(tmp_path)
    (project / ".env.backup-before-sqlite").write_text("SECRET=do-not-copy")
    profiles = project / "app" / "vision" / "perfis_faciais"
    profiles.mkdir(parents=True)
    (profiles / "person.npz").write_bytes(b"biometric-data")

    workspace = engine.criar_workspace("proposal_3")

    assert not (workspace / ".env.backup-before-sqlite").exists()
    assert not (workspace / "app" / "vision" / "perfis_faciais").exists()
