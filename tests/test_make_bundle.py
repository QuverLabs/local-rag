from __future__ import annotations

import hashlib
import tarfile
import zipfile

import pytest

from scripts import make_bundle
from setup._archive import extract_from_tar_gz as _extract_from_tar_gz


@pytest.mark.parametrize(
    "name",
    [
        "server.py",
        "foo/bar.toml",
        "uv.lock",
        "README.md",
        "manifest.json",
        "install.ps1",
        "install.bat",
        ".env.example",
    ],
)
def test_compression_for_text_files(name):
    assert make_bundle._compression_for(name) == zipfile.ZIP_DEFLATED


@pytest.mark.parametrize(
    "name",
    [
        "data/memory.db",
        "data/models/model.gguf",
        "data/extensions/vector.dll",
        "bin/uv.exe",
        "data/extensions/memory.so",
    ],
)
def test_compression_for_binary_files(name):
    assert make_bundle._compression_for(name) == zipfile.ZIP_STORED


def test_sha256_matches_hashlib(tmp_path):
    payload = b"hello world\n" * 1000
    target = tmp_path / "blob.bin"
    target.write_bytes(payload)
    assert make_bundle._sha256(target) == hashlib.sha256(payload).hexdigest()


def test_sha256_empty_file(tmp_path):
    target = tmp_path / "empty.bin"
    target.write_bytes(b"")
    assert make_bundle._sha256(target) == hashlib.sha256(b"").hexdigest()


def test_extract_from_tar_gz_picks_shortest_path(tmp_path):
    archive = tmp_path / "src.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name, payload in [
            ("nested/deep/vector.dll", b"DEEP"),
            ("vector.dll", b"TOP"),
            ("other.txt", b"skip"),
        ]:
            blob = tmp_path / name.replace("/", "_")
            blob.write_bytes(payload)
            tar.add(blob, arcname=name)

    out = tmp_path / "extracted.dll"
    _extract_from_tar_gz(archive, ".dll", out)
    assert out.read_bytes() == b"TOP"


def test_extract_from_tar_gz_no_match_raises(tmp_path):
    archive = tmp_path / "src.tar.gz"
    blob = tmp_path / "readme.txt"
    blob.write_bytes(b"hi")
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(blob, arcname="readme.txt")

    with pytest.raises(RuntimeError, match=r"No \*\.dll"):
        _extract_from_tar_gz(archive, ".dll", tmp_path / "out.dll")


def test_extract_uv_exe_prefers_top_level(tmp_path):
    archive = tmp_path / "uv.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("uv-x86_64-pc-windows-msvc/uv.exe", b"NESTED")
        zf.writestr("uv.exe", b"TOP")
        zf.writestr("uvx.exe", b"OTHER")

    out = tmp_path / "uv.exe"
    make_bundle._extract_uv_exe(archive, out)
    assert out.read_bytes() == b"TOP"


def test_extract_uv_exe_missing_raises(tmp_path):
    archive = tmp_path / "uv.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("README", b"nope")

    with pytest.raises(RuntimeError, match="uv.exe not found"):
        make_bundle._extract_uv_exe(archive, tmp_path / "uv.exe")
