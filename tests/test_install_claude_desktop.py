from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from setup import install_claude_desktop


def test_config_path_macos():
    path = install_claude_desktop._config_path("macos")
    assert path == Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"


def test_config_path_windows():
    path = install_claude_desktop._config_path("windows")
    assert path == Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"


def test_config_path_unknown_os():
    with pytest.raises(SystemExit, match="Claude Desktop config path unknown"):
        install_claude_desktop._config_path("linux")


def test_docker_entry_uses_stdio_and_expected_mounts():
    entry = install_claude_desktop._docker_entry(
        "/usr/local/bin/docker",
        "/Users/test/notes",
        "local-rag",
    )

    assert entry["command"] == "/usr/local/bin/docker"
    assert entry["args"] == [
        "run",
        "--rm",
        "-i",
        "--platform",
        "linux/amd64",
        "-e",
        "MCP_SERVER_NAME=local-rag",
        "-v",
        "local-rag-data:/data",
        "-v",
        "/Users/test/notes:/notes:ro",
        "local-rag:dev",
    ]


def test_docker_entry_preserves_windows_host_paths():
    entry = install_claude_desktop._docker_entry(
        r"C:\Program Files\Docker\docker.exe",
        r"C:\Users\test\notes",
        "local-rag",
    )

    assert entry["command"] == r"C:\Program Files\Docker\docker.exe"
    assert r"C:\Users\test\notes:/notes:ro" in entry["args"]


def test_native_install_preserves_config_and_existing_servers(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "server.py").touch()
    uv = tmp_path / "uv"
    uv.touch()
    config_path = tmp_path / "claude.json"
    original = {"mcpServers": {"existing": {"command": "other"}}}
    raw = f"{json.dumps(original, indent=2)}\n".encode()
    config_path.write_bytes(raw)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "install_claude_desktop",
            "--uv",
            str(uv),
            "--project-dir",
            str(project),
            "--name",
            "local-rag",
            "--config-path",
            str(config_path),
        ],
    )

    assert install_claude_desktop.main() == 0
    assert config_path.with_suffix(".json.bak").read_bytes() == raw
    assert json.loads(config_path.read_text()) == {
        "mcpServers": {
            "existing": {"command": "other"},
            "local-rag": {
                "command": str(uv.resolve()),
                "args": ["run", "--directory", str(project.resolve()), "server.py"],
            },
        }
    }


def test_native_validates_project_before_loading_env(tmp_path, monkeypatch):
    uv = tmp_path / "uv"
    uv.touch()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "install_claude_desktop",
            "--uv",
            str(uv),
            "--project-dir",
            str(tmp_path / "missing"),
            "--config-path",
            str(tmp_path / "claude.json"),
        ],
    )
    monkeypatch.setattr(
        install_claude_desktop,
        "load_env",
        lambda *_: pytest.fail("must validate project before loading .env"),
    )

    with pytest.raises(SystemExit, match="server.py not found"):
        install_claude_desktop.main()
