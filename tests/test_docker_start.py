from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from docker import start


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_source_manifest_tracks_markdown_paths_and_content(tmp_path):
    note = tmp_path / "first.md"
    note.write_text("one", encoding="utf-8")
    initial, count = start.source_manifest(tmp_path)

    note.write_text("two", encoding="utf-8")
    changed_content, _ = start.source_manifest(tmp_path)
    note.rename(tmp_path / "second.md")
    changed_path, _ = start.source_manifest(tmp_path)

    assert count == 1
    assert len({initial, changed_content, changed_path}) == 3


def test_source_manifest_ignores_non_markdown_files(tmp_path):
    (tmp_path / "note.md").write_text("indexed", encoding="utf-8")
    initial, _ = start.source_manifest(tmp_path)
    (tmp_path / "ignored.txt").write_text("ignored", encoding="utf-8")

    assert start.source_manifest(tmp_path) == (initial, 1)


def test_ensure_artifacts_reuses_verified_files(tmp_path, monkeypatch):
    payloads = {
        "extensions/vector.so": b"vector",
        "extensions/memory.so": b"memory",
        "models/model.gguf": b"model",
    }
    monkeypatch.setattr(start, "ARTIFACT_SHA256", {name: _sha(data) for name, data in payloads.items()})
    for relative, payload in payloads.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    calls = []
    start.ensure_artifacts(tmp_path, runner=lambda *args, **kwargs: calls.append((args, kwargs)))

    assert calls == []
    assert (tmp_path / "artifacts.json").is_file()


def test_rebuild_index_replaces_live_database_after_success(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "note.md").write_text("current", encoding="utf-8")
    source_digest, _ = start.source_manifest(notes)
    live = tmp_path / "memory.db"
    live.write_bytes(b"old")
    manifest = tmp_path / "memory.db.sources.sha256"

    def successful_ingest(*args, env=None):
        assert args == ("/app/ingest.py",)
        Path(env["MEMORY_DB"]).write_bytes(b"new")

    start.rebuild_index(notes, live, manifest, source_digest, runner=successful_ingest)

    assert live.read_bytes() == b"new"
    assert manifest.read_text(encoding="utf-8").strip() == source_digest


def test_rebuild_index_preserves_live_database_after_failure(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "note.md").write_text("current", encoding="utf-8")
    source_digest, _ = start.source_manifest(notes)
    live = tmp_path / "memory.db"
    live.write_bytes(b"old")
    manifest = tmp_path / "memory.db.sources.sha256"

    def failed_ingest(*args, env=None):
        Path(env["MEMORY_DB"]).write_bytes(b"partial")
        raise subprocess.CalledProcessError(1, args)

    with pytest.raises(subprocess.CalledProcessError):
        start.rebuild_index(notes, live, manifest, source_digest, runner=failed_ingest)

    assert live.read_bytes() == b"old"
    assert not manifest.exists()
    assert not (tmp_path / ".memory.db.next").exists()


def test_main_rejects_empty_source_before_artifact_setup(tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    monkeypatch.setenv("NOTES_DIR", str(notes))
    monkeypatch.setenv("MEMORY_DB", str(tmp_path / "memory.db"))
    monkeypatch.setattr(
        start,
        "ensure_artifacts",
        lambda data_dir: pytest.fail("artifact setup must not run for an empty source"),
    )

    with pytest.raises(SystemExit, match="No Markdown files"):
        start.main()
