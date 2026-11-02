from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

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


# ---------------------------------------------------------------------------
# _find_uv
# ---------------------------------------------------------------------------


def test_find_uv_returns_path_from_which(tmp_path, monkeypatch):
    fake_uv = tmp_path / "bin" / "uv"
    fake_uv.parent.mkdir()
    fake_uv.touch()
    monkeypatch.setattr("shutil.which", lambda _: str(fake_uv))
    result = install_claude_desktop._find_uv()
    assert result == fake_uv


def test_find_uv_raises_when_not_on_path(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(SystemExit, match="Could not find 'uv'"):
        install_claude_desktop._find_uv()


def test_find_uv_does_not_resolve_symlinks(tmp_path, monkeypatch):
    """Regression: resolved path hardcodes the Cellar version and breaks after brew upgrade."""
    real_bin = tmp_path / "Cellar" / "uv" / "1.2.3" / "bin" / "uv"
    real_bin.parent.mkdir(parents=True)
    real_bin.touch()
    symlink = tmp_path / "bin" / "uv"
    symlink.parent.mkdir()
    symlink.symlink_to(real_bin)

    monkeypatch.setattr("shutil.which", lambda _: str(symlink))
    result = install_claude_desktop._find_uv()
    assert result == symlink
    assert result != real_bin


# ---------------------------------------------------------------------------
# main() helpers
# ---------------------------------------------------------------------------


def _run_main(argv: list[str], monkeypatch, tmp_path: Path) -> Path:
    """Invoke main() with patched argv + detect(); returns the config path used."""
    config_path = tmp_path / "claude_desktop_config.json"
    monkeypatch.setattr(sys, "argv", ["install_claude_desktop.py"] + argv)
    monkeypatch.setattr(install_claude_desktop, "_config_path", lambda _: config_path)
    with patch("setup.install_claude_desktop.detect", return_value=("macos", "arm64")):
        install_claude_desktop.main()
    return config_path


def _project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir(exist_ok=True)
    (d / "server.py").touch()
    (d / ".env").write_text("")
    return d


def _fake_uv(tmp_path: Path) -> Path:
    uv = tmp_path / "uv"
    uv.touch()
    return uv


# ---------------------------------------------------------------------------
# main() tests
# ---------------------------------------------------------------------------


def test_main_creates_config_when_missing(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    config_path = _run_main(
        ["--project-dir", str(project), "--uv", str(uv)],
        monkeypatch,
        tmp_path,
    )
    assert config_path.exists()
    data = json.loads(config_path.read_text())
    assert "local-rag" in data["mcpServers"]


def test_main_entry_has_correct_structure(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    config_path = _run_main(
        ["--project-dir", str(project), "--uv", str(uv)],
        monkeypatch,
        tmp_path,
    )
    entry = json.loads(config_path.read_text())["mcpServers"]["local-rag"]
    assert entry["command"] == str(uv)
    assert entry["args"] == ["run", "--directory", str(project.resolve()), "server.py"]


def test_main_uv_arg_is_not_resolved(tmp_path, monkeypatch):
    """--uv symlink must be stored as-is, not resolved to the real target."""
    project = _project_dir(tmp_path)
    real_uv = tmp_path / "real_uv"
    real_uv.touch()
    symlink_uv = tmp_path / "uv"
    symlink_uv.symlink_to(real_uv)

    config_path = _run_main(
        ["--project-dir", str(project), "--uv", str(symlink_uv)],
        monkeypatch,
        tmp_path,
    )
    entry = json.loads(config_path.read_text())["mcpServers"]["local-rag"]
    assert entry["command"] == str(symlink_uv)
    assert entry["command"] != str(real_uv)


def test_main_creates_backup_of_existing_config(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    existing = tmp_path / "claude_desktop_config.json"
    existing.write_text('{"mcpServers":{}}')

    _run_main(["--project-dir", str(project), "--uv", str(uv)], monkeypatch, tmp_path)

    backup = tmp_path / "claude_desktop_config.json.bak"
    assert backup.exists()
    assert backup.read_text() == '{"mcpServers":{}}'


def test_main_preserves_other_mcp_servers(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    existing = tmp_path / "claude_desktop_config.json"
    existing.write_text(json.dumps({"mcpServers": {"other-server": {"command": "npx"}}}))

    config_path = _run_main(["--project-dir", str(project), "--uv", str(uv)], monkeypatch, tmp_path)
    data = json.loads(config_path.read_text())
    assert "other-server" in data["mcpServers"]
    assert "local-rag" in data["mcpServers"]


def test_main_replaces_differing_entry(tmp_path, monkeypatch, capsys):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    old_entry = {"command": "/old/uv", "args": ["run", "--directory", "/old", "server.py"]}
    existing = tmp_path / "claude_desktop_config.json"
    existing.write_text(json.dumps({"mcpServers": {"local-rag": old_entry}}))

    config_path = _run_main(["--project-dir", str(project), "--uv", str(uv)], monkeypatch, tmp_path)
    data = json.loads(config_path.read_text())
    assert data["mcpServers"]["local-rag"]["command"] == str(uv)
    assert "Warning" in capsys.readouterr().err


def test_main_uses_custom_name_from_arg(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    config_path = _run_main(
        ["--project-dir", str(project), "--uv", str(uv), "--name", "my-rag"],
        monkeypatch,
        tmp_path,
    )
    data = json.loads(config_path.read_text())
    assert "my-rag" in data["mcpServers"]
    assert "local-rag" not in data["mcpServers"]


def test_main_uses_server_name_from_env(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    monkeypatch.setenv("MCP_SERVER_NAME", "env-rag")
    config_path = _run_main(["--project-dir", str(project), "--uv", str(uv)], monkeypatch, tmp_path)
    data = json.loads(config_path.read_text())
    assert "env-rag" in data["mcpServers"]


def test_main_raises_when_uv_arg_missing(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    ghost = tmp_path / "nonexistent_uv"
    with pytest.raises(SystemExit, match="uv binary not found"):
        _run_main(["--project-dir", str(project), "--uv", str(ghost)], monkeypatch, tmp_path)


def test_main_raises_when_server_py_missing(tmp_path, monkeypatch):
    project = tmp_path / "empty_project"
    project.mkdir()
    uv = _fake_uv(tmp_path)
    with pytest.raises(SystemExit, match="server.py not found"):
        _run_main(["--project-dir", str(project), "--uv", str(uv)], monkeypatch, tmp_path)


def test_main_raises_on_invalid_existing_json(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    broken = tmp_path / "claude_desktop_config.json"
    broken.write_text("not json {{{")
    with pytest.raises(SystemExit, match="not valid JSON"):
        _run_main(["--project-dir", str(project), "--uv", str(uv)], monkeypatch, tmp_path)


def test_main_creates_parent_dirs_when_config_missing(tmp_path, monkeypatch):
    project = _project_dir(tmp_path)
    uv = _fake_uv(tmp_path)
    deep_config = tmp_path / "deep" / "nested" / "claude_desktop_config.json"
    monkeypatch.setattr(sys, "argv", ["install", "--project-dir", str(project), "--uv", str(uv)])
    monkeypatch.setattr(install_claude_desktop, "_config_path", lambda _: deep_config)
    with patch("setup.install_claude_desktop.detect", return_value=("macos", "arm64")):
        install_claude_desktop.main()
    assert deep_config.exists()
