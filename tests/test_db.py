from __future__ import annotations

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
    monkeypatch.setenv("EMPTY_VAR", "")
    with pytest.raises(SystemExit, match="EMPTY_VAR"):
        _db.require_env("EMPTY_VAR")
