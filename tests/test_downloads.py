from __future__ import annotations

import sys

import pytest

from setup import download_extensions


def test_extension_update_keeps_existing_pair_when_second_download_fails(tmp_path, monkeypatch):
    target = tmp_path / "extensions"
    target.mkdir()
    vector = target / "vector.so"
    memory = target / "memory.so"
    vector.write_bytes(b"old-vector")
    memory.write_bytes(b"old-memory")

    monkeypatch.setattr(download_extensions, "detect", lambda: ("linux", "x86_64"))
    monkeypatch.setattr(download_extensions, "extension_suffix", lambda: ".so")
    downloads = 0

    def download(url, destination, **kwargs):
        nonlocal downloads
        downloads += 1
        if downloads == 2:
            raise RuntimeError("second download failed")
        destination.write_bytes(b"archive")

    def extract(archive, target_dir, suffix, stem):
        output = target_dir / f"{stem}{suffix}"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(f"new-{stem}".encode())
        return output

    monkeypatch.setattr(download_extensions, "stream_download", download)
    monkeypatch.setattr(download_extensions, "_extract_extension", extract)
    monkeypatch.setattr(
        sys,
        "argv",
        ["download_extensions", "--extensions-dir", str(target), "--force"],
    )

    with pytest.raises(RuntimeError, match="second download failed"):
        download_extensions.main()

    assert vector.read_bytes() == b"old-vector"
    assert memory.read_bytes() == b"old-memory"


def test_extension_update_installs_completed_pair(tmp_path, monkeypatch):
    target = tmp_path / "extensions"
    monkeypatch.setattr(download_extensions, "detect", lambda: ("linux", "x86_64"))
    monkeypatch.setattr(download_extensions, "extension_suffix", lambda: ".so")
    monkeypatch.setattr(
        download_extensions,
        "stream_download",
        lambda url, destination, **kwargs: destination.write_bytes(b"archive"),
    )

    def extract(archive, target_dir, suffix, stem):
        output = target_dir / f"{stem}{suffix}"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(f"new-{stem}".encode())
        return output

    monkeypatch.setattr(download_extensions, "_extract_extension", extract)
    monkeypatch.setattr(
        sys,
        "argv",
        ["download_extensions", "--extensions-dir", str(target), "--force"],
    )

    assert download_extensions.main() == 0
    assert (target / "vector.so").read_bytes() == b"new-vector"
    assert (target / "memory.so").read_bytes() == b"new-memory"


def test_extension_staging_uses_target_filesystem(tmp_path, monkeypatch):
    target = tmp_path / "mounted-volume" / "extensions"
    temporary_parents = []

    class TemporaryDirectory:
        def __init__(self, *, prefix, dir):
            temporary_parents.append((prefix, dir))
            self.path = tmp_path / "staging"
            self.path.mkdir()

        def __enter__(self):
            return str(self.path)

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(download_extensions.tempfile, "TemporaryDirectory", TemporaryDirectory)
    monkeypatch.setattr(download_extensions, "detect", lambda: ("linux", "x86_64"))
    monkeypatch.setattr(download_extensions, "extension_suffix", lambda: ".so")
    monkeypatch.setattr(
        download_extensions,
        "stream_download",
        lambda url, destination, **kwargs: destination.write_bytes(b"archive"),
    )

    def extract(archive, target_dir, suffix, stem):
        output = target_dir / f"{stem}{suffix}"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(stem.encode())
        return output

    monkeypatch.setattr(download_extensions, "_extract_extension", extract)
    monkeypatch.setattr(
        sys,
        "argv",
        ["download_extensions", "--extensions-dir", str(target), "--force"],
    )

    assert download_extensions.main() == 0
    assert temporary_parents == [(".local-rag-extensions-", target.parent)]
