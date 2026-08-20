"""Prepare verified artifacts, refresh a stale index, and start stdio MCP."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from setup.download_extensions import MEMORY_VERSION, VECTOR_VERSION
from setup.download_model import MODEL_FILE, MODEL_REVISION, MODEL_SHA256

ARTIFACT_SHA256 = {
    "extensions/vector.so": "2fea30220396573f7aaafa23a8675addd0e4a1bc0dce8f31fef6d9c32a4f030e",
    "extensions/memory.so": "cf3f297108ba9197a719a226a9e0cffd4619701eb08879ab13b09fcc1fc0afd4",
    f"models/{MODEL_FILE}": MODEL_SHA256,
}

Runner = Callable[..., None]


def file_sha256(path: Path) -> str:
    """Hash one file without loading it fully into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest(notes_dir: Path) -> tuple[str, int]:
    """Return a stable digest and count for all Markdown paths and contents."""
    if not notes_dir.is_dir():
        raise SystemExit(f"NOTES_DIR does not exist or is not a directory: {notes_dir}")

    digest = hashlib.sha256()
    files = sorted(notes_dir.rglob("*.md"), key=lambda path: path.relative_to(notes_dir).as_posix())
    for path in files:
        relative = path.relative_to(notes_dir).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(path.stat().st_size.to_bytes(8, "big"))
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
    return digest.hexdigest(), len(files)


def run(*args: str, env: dict[str, str] | None = None) -> None:
    """Run a required preparation step and stop immediately on failure."""
    subprocess.run([sys.executable, *args], check=True, env=env)  # noqa: S603


def write_text_atomic(path: Path, value: str) -> None:
    """Atomically replace a small state file."""
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    """Serialize artifact and index updates sharing one Docker volume."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def expected_artifact_manifest() -> dict:
    """Describe the exact artifacts accepted by this image."""
    return {
        "schema": 1,
        "platform": "linux-x86_64",
        "sqlite_vector_version": VECTOR_VERSION,
        "sqlite_memory_version": MEMORY_VERSION,
        "model_revision": MODEL_REVISION,
        "files": ARTIFACT_SHA256,
    }


def artifact_files_valid(data_dir: Path) -> bool:
    """Return true only when every installed artifact matches its pinned hash."""
    for relative, expected in ARTIFACT_SHA256.items():
        path = data_dir / relative
        if not path.is_file() or file_sha256(path) != expected:
            return False
    return True


def ensure_artifacts(data_dir: Path, runner: Runner = run) -> None:
    """Download missing or changed artifacts, verify them, and record versions."""
    extensions_dir = data_dir / "extensions"
    model_dir = data_dir / "models"

    if not artifact_files_valid(data_dir):
        runner(
            "-m",
            "setup.download_extensions",
            "--extensions-dir",
            str(extensions_dir),
            "--force",
        )
        runner("-m", "setup.download_model", "--model-dir", str(model_dir), "--force")

    if not artifact_files_valid(data_dir):
        raise SystemExit("Downloaded artifacts do not match the pinned SHA256 values.")

    manifest = json.dumps(expected_artifact_manifest(), indent=2, sort_keys=True)
    write_text_atomic(data_dir / "artifacts.json", f"{manifest}\n")


def remove_database(path: Path) -> None:
    """Remove only a disposable staging database and its SQLite sidecars."""
    for suffix in ("", "-wal", "-shm", "-journal"):
        path.with_name(f"{path.name}{suffix}").unlink(missing_ok=True)


def rebuild_index(
    notes_dir: Path,
    memory_db: Path,
    manifest_path: Path,
    current_manifest: str,
    runner: Runner = run,
) -> None:
    """Build a new database and atomically replace the live index on success."""
    staging_db = memory_db.with_name(f".{memory_db.name}.next")
    remove_database(staging_db)
    environment = os.environ.copy()
    environment["MEMORY_DB"] = str(staging_db)

    try:
        runner("/app/ingest.py", env=environment)
        verified_manifest, _ = source_manifest(notes_dir)
        if verified_manifest != current_manifest:
            raise RuntimeError("Markdown sources changed during ingest; run the container again.")
        if not staging_db.is_file():
            raise RuntimeError("Ingest completed without creating a staging database.")

        os.replace(staging_db, memory_db)
        write_text_atomic(manifest_path, f"{verified_manifest}\n")
    finally:
        remove_database(staging_db)


def main() -> None:
    notes_dir = Path(os.environ["NOTES_DIR"])
    memory_db = Path(os.environ["MEMORY_DB"])
    data_dir = memory_db.parent
    manifest_path = memory_db.with_name(f"{memory_db.name}.sources.sha256")
    lock_path = memory_db.with_name(f"{memory_db.name}.startup.lock")

    with exclusive_lock(lock_path):
        current_manifest, file_count = source_manifest(notes_dir)
        if file_count == 0:
            raise SystemExit(f"No Markdown files found below NOTES_DIR: {notes_dir}")

        ensure_artifacts(data_dir)
        saved_manifest = manifest_path.read_text(encoding="utf-8").strip() if manifest_path.exists() else None

        if not memory_db.exists() or saved_manifest != current_manifest:
            reason = "missing index" if not memory_db.exists() else "Markdown sources changed"
            print(f"Rebuilding index: {reason} ({file_count} files)", file=sys.stderr, flush=True)
            rebuild_index(notes_dir, memory_db, manifest_path, current_manifest)
        else:
            print(f"Index is current ({file_count} Markdown files)", file=sys.stderr, flush=True)

    os.execv(sys.executable, [sys.executable, "/app/server.py"])


if __name__ == "__main__":
    main()
