from __future__ import annotations

import hashlib
from contextlib import nullcontext

import pytest

from setup import _http


class _Response:
    headers = {"Content-Length": "7"}

    def raise_for_status(self):
        return None

    def iter_bytes(self, chunk_size):
        assert chunk_size > 0
        yield b"payload"


def test_stream_download_accepts_matching_sha256(tmp_path, monkeypatch):
    monkeypatch.setattr(_http.httpx, "stream", lambda *args, **kwargs: nullcontext(_Response()))
    destination = tmp_path / "artifact.bin"
    expected = hashlib.sha256(b"payload").hexdigest()

    _http.stream_download("https://example.invalid/artifact", destination, expected_sha256=expected)

    assert destination.read_bytes() == b"payload"


def test_stream_download_rejects_wrong_sha256(tmp_path, monkeypatch):
    monkeypatch.setattr(_http.httpx, "stream", lambda *args, **kwargs: nullcontext(_Response()))
    destination = tmp_path / "artifact.bin"

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        _http.stream_download("https://example.invalid/artifact", destination, expected_sha256="0" * 64)

    assert not destination.exists()
    assert not (tmp_path / "artifact.bin.part").exists()
