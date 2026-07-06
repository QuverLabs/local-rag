from __future__ import annotations

from pathlib import Path

import pytest

from setup import _db


def test_server_name_default(monkeypatch):
    monkeypatch.delenv("MCP_SERVER_NAME", raising=False)
    assert _db.server_name() == _db.DEFAULT_SERVER_NAME


def test_server_name_override(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_NAME", "custom-rag")
    assert _db.server_name() == "custom-rag"


def test_server_name_empty_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_NAME", "")
    assert _db.server_name() == _db.DEFAULT_SERVER_NAME


def test_require_env_present(monkeypatch):
    monkeypatch.setenv("SOME_VAR", "value")
    assert _db.require_env("SOME_VAR") == "value"


def test_require_env_missing(monkeypatch):
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(SystemExit, match="MISSING_VAR"):
        _db.require_env("MISSING_VAR")


def test_require_env_empty(monkeypatch):
    # Empty string is a valid env-var value; only a completely absent var raises.
    monkeypatch.setenv("EMPTY_VAR", "")
    assert _db.require_env("EMPTY_VAR") == ""


def test_repo_root_contains_setup_package():
    # The helper resolves relative to setup/_db.py, so the repo root must own
    # the package — not the other way around.
    root = _db.repo_root()
    assert (root / "setup" / "_db.py").is_file()


def test_require_env_path_expands_and_resolves(monkeypatch, tmp_path):
    target = tmp_path / "sub"
    target.mkdir()
    monkeypatch.setenv("SOME_PATH", str(target))
    result = _db.require_env_path("SOME_PATH")
    assert result == target.resolve()
    assert result.is_absolute()


def test_require_env_path_missing(monkeypatch):
    monkeypatch.delenv("MISSING_PATH", raising=False)
    with pytest.raises(SystemExit, match="MISSING_PATH"):
        _db.require_env_path("MISSING_PATH")


def test_load_env_reads_from_project_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("LOCAL_RAG_TEST_KEY", raising=False)
    (tmp_path / ".env").write_text("LOCAL_RAG_TEST_KEY=from_env_file\n")
    _db.load_env(tmp_path)
    import os

    assert os.environ.get("LOCAL_RAG_TEST_KEY") == "from_env_file"


def test_load_env_silent_when_missing(tmp_path: Path):
    # No .env in tmp_path — should not raise.
    _db.load_env(tmp_path)
