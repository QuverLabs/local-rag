from __future__ import annotations

import pytest

from setup import _platform


def test_detect_macos(monkeypatch):
    monkeypatch.setattr(_platform.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(_platform.platform, "machine", lambda: "arm64")
    assert _platform.detect() == ("macos", "arm64")


def test_detect_macos_ignores_machine(monkeypatch):
    monkeypatch.setattr(_platform.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(_platform.platform, "machine", lambda: "x86_64")
    assert _platform.detect() == ("macos", "arm64")


@pytest.mark.parametrize("machine", ["AMD64", "x86_64"])
def test_detect_windows_x86_64(monkeypatch, machine):
    monkeypatch.setattr(_platform.platform, "system", lambda: "Windows")
    monkeypatch.setattr(_platform.platform, "machine", lambda: machine)
    assert _platform.detect() == ("windows", "x86_64")


def test_detect_windows_arm_unsupported(monkeypatch):
    monkeypatch.setattr(_platform.platform, "system", lambda: "Windows")
    monkeypatch.setattr(_platform.platform, "machine", lambda: "arm64")
    with pytest.raises(RuntimeError, match="Unsupported Windows architecture"):
        _platform.detect()


@pytest.mark.parametrize("machine", ["x86_64", "amd64"])
def test_detect_linux_x86_64(monkeypatch, machine):
    monkeypatch.setattr(_platform.platform, "system", lambda: "Linux")
    monkeypatch.setattr(_platform.platform, "machine", lambda: machine)
    assert _platform.detect() == ("linux", "x86_64")


def test_detect_linux_arm_unsupported(monkeypatch):
    monkeypatch.setattr(_platform.platform, "system", lambda: "Linux")
    monkeypatch.setattr(_platform.platform, "machine", lambda: "aarch64")
    with pytest.raises(RuntimeError, match="Unsupported Linux architecture"):
        _platform.detect()


def test_detect_unknown_system(monkeypatch):
    monkeypatch.setattr(_platform.platform, "system", lambda: "FreeBSD")
    monkeypatch.setattr(_platform.platform, "machine", lambda: "x86_64")
    with pytest.raises(RuntimeError, match="Unsupported platform"):
        _platform.detect()


@pytest.mark.parametrize(
    "os_tag,expected",
    [("macos", ".dylib"), ("windows", ".dll"), ("linux", ".so")],
)
def test_extension_suffix(monkeypatch, os_tag, expected):
    monkeypatch.setattr(_platform, "detect", lambda: (os_tag, "x86_64"))
    assert _platform.extension_suffix() == expected
