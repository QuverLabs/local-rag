from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from docker import start


def configure_paths(tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    data = tmp_path / "data"
    notes.mkdir()
    monkeypatch.setattr(start, "NOTES_DIR", notes)
    monkeypatch.setattr(start, "DATA_DIR", data)
    monkeypatch.setattr(start, "MEMORY_DB", data / "memory.db")
    monkeypatch.setattr(start, "EXTENSIONS_DIR", data / "extensions")
    monkeypatch.setattr(start, "MODEL_PATH", data / f"models/{start.MODEL_FILE}")
    monkeypatch.setattr(start, "INDEX_FINGERPRINT", data / "memory.db.index.sha256")
    monkeypatch.setattr(start, "STARTUP_LOCK", data / "memory.db.startup.lock")
    return notes, data


def test_run_redirects_preparation_stdout_to_stderr(monkeypatch):
    calls = []
    monkeypatch.setattr(start.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    start.run("ingest.py")

    assert calls[0][1]["stdout"] is sys.stderr


def test_source_manifest_tracks_markdown_paths_and_content(tmp_path, monkeypatch):
    notes, _ = configure_paths(tmp_path, monkeypatch)
    note = notes / "first.md"
    note.write_text("one", encoding="utf-8")
    initial, count = start.source_manifest()

    note.write_text("two", encoding="utf-8")
    changed_content, _ = start.source_manifest()
    note.rename(notes / "second.md")
    changed_path, _ = start.source_manifest()
    (notes / "ignored.txt").write_text("ignored", encoding="utf-8")

    assert count == 1
    assert len({initial, changed_content, changed_path}) == 3
    assert start.source_manifest() == (changed_path, 1)


@pytest.mark.parametrize("missing", ["extensions", "model"])
def test_ensure_artifacts_downloads_only_invalid_group(monkeypatch, missing):
    extension_states = iter((False, True)) if missing == "extensions" else iter((True,))
    model_states = iter((False, True)) if missing == "model" else iter((True,))
    monkeypatch.setattr(start, "extensions_valid", lambda: next(extension_states))
    monkeypatch.setattr(start, "model_valid", lambda: next(model_states))
    calls = []

    start.ensure_artifacts(runner=lambda *args, **kwargs: calls.append(args))

    expected_module = "setup.download_extensions" if missing == "extensions" else "setup.download_model"
    assert len(calls) == 1
    assert expected_module in calls[0]


def test_ensure_artifacts_reuses_valid_files(monkeypatch):
    monkeypatch.setattr(start, "extensions_valid", lambda: True)
    monkeypatch.setattr(start, "model_valid", lambda: True)
    calls = []

    start.ensure_artifacts(runner=lambda *args, **kwargs: calls.append(args))

    assert calls == []


@pytest.mark.parametrize(
    ("name", "value"),
    [("MEMORY_MAX_TOKENS", "128"), ("MEMORY_OVERLAP_TOKENS", "25")],
)
def test_index_fingerprint_tracks_ingest_settings(monkeypatch, name, value):
    initial = start.index_fingerprint("sources")
    monkeypatch.setenv(name, value)

    assert start.index_fingerprint("sources") != initial


def test_index_fingerprint_tracks_artifacts(monkeypatch):
    initial = start.index_fingerprint("sources")
    monkeypatch.setitem(start.ARTIFACT_SHA256, "model", "new-sha256")

    assert start.index_fingerprint("sources") != initial


def test_rebuild_index_replaces_live_database_after_success(tmp_path, monkeypatch):
    notes, data = configure_paths(tmp_path, monkeypatch)
    (notes / "note.md").write_text("current", encoding="utf-8")
    source_sha256, _ = start.source_manifest()
    data.mkdir()
    start.MEMORY_DB.write_bytes(b"old")

    def successful_ingest(*args, env=None):
        Path(env["MEMORY_DB"]).write_bytes(b"new")

    start.rebuild_index(source_sha256, runner=successful_ingest)

    assert start.MEMORY_DB.read_bytes() == b"new"
    assert start.INDEX_FINGERPRINT.read_text(encoding="utf-8").strip() == start.index_fingerprint(
        source_sha256
    )


def test_rebuild_index_preserves_live_database_after_failure(tmp_path, monkeypatch):
    notes, data = configure_paths(tmp_path, monkeypatch)
    (notes / "note.md").write_text("current", encoding="utf-8")
    source_sha256, _ = start.source_manifest()
    data.mkdir()
    start.MEMORY_DB.write_bytes(b"old")

    def failed_ingest(*args, env=None):
        Path(env["MEMORY_DB"]).write_bytes(b"partial")
        raise subprocess.CalledProcessError(1, args)

    with pytest.raises(subprocess.CalledProcessError):
        start.rebuild_index(source_sha256, runner=failed_ingest)

    assert start.MEMORY_DB.read_bytes() == b"old"
    assert not start.INDEX_FINGERPRINT.exists()
    assert not (data / ".memory.db.next").exists()


def test_main_rejects_empty_source_before_artifact_setup(tmp_path, monkeypatch):
    configure_paths(tmp_path, monkeypatch)
    monkeypatch.setattr(start, "ensure_artifacts", lambda: pytest.fail("must not prepare empty source"))

    with pytest.raises(SystemExit, match="No Markdown files"):
        start.main()
