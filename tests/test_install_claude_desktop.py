from __future__ import annotations

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
