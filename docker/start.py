"""Prepare local-rag data and start the stdio MCP server."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from setup.download_extensions import MEMORY_VERSION, VECTOR_VERSION
from setup.download_model import MODEL_FILE, MODEL_REVISION, MODEL_SHA256

NOTES_DIR = Path("/notes")
DATA_DIR = Path("/data")
MEMORY_DB = DATA_DIR / "memory.db"
EXTENSIONS_DIR = DATA_DIR / "extensions"
MODEL_PATH = DATA_DIR / "models" / MODEL_FILE
INDEX_FINGERPRINT = DATA_DIR / "memory.db.index.sha256"
STARTUP_LOCK = DATA_DIR / "memory.db.startup.lock"

ARTIFACT_SHA256 = {
    "vector": "2fea30220396573f7aaafa23a8675addd0e4a1bc0dce8f31fef6d9c32a4f030e",
    "memory": "cf3f297108ba9197a719a226a9e0cffd4619701eb08879ab13b09fcc1fc0afd4",
    "model": MODEL_SHA256,
}
ARTIFACT_VERSIONS = {
    "vector": VECTOR_VERSION,
    "memory": MEMORY_VERSION,
    "model": MODEL_REVISION,
}

Runner = Callable[..., None]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest() -> tuple[str, int]:
    """Hash Markdown paths and contents below /notes."""
    if not NOTES_DIR.is_dir():
        raise SystemExit(f"Markdown directory does not exist: {NOTES_DIR}")

    digest = hashlib.sha256()
    files = sorted(NOTES_DIR.rglob("*.md"), key=lambda path: path.relative_to(NOTES_DIR).as_posix())
    for path in files:
        relative = path.relative_to(NOTES_DIR).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(path.stat().st_size.to_bytes(8, "big"))
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
    return digest.hexdigest(), len(files)


def index_fingerprint(source_sha256: str) -> str:
    """Fingerprint everything that affects generated embeddings and chunks."""
    payload = {
        "source": source_sha256,
        "versions": ARTIFACT_VERSIONS,
        "sha256": ARTIFACT_SHA256,
        "max_tokens": int(os.environ.get("MEMORY_MAX_TOKENS") or 256),
        "overlap_tokens": int(os.environ.get("MEMORY_OVERLAP_TOKENS") or 50),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def run(*args: str, env: dict[str, str] | None = None) -> None:
    """Run preparation without writing non-JSON data to MCP stdout."""
    subprocess.run(  # noqa: S603
        [sys.executable, *args], check=True, env=env, stdout=sys.stderr
    )


def extensions_valid() -> bool:
    return all(
        path.is_file() and file_sha256(path) == ARTIFACT_SHA256[name]
        for name, path in {
            "vector": EXTENSIONS_DIR / "vector.so",
            "memory": EXTENSIONS_DIR / "memory.so",
        }.items()
    )


def model_valid() -> bool:
    return MODEL_PATH.is_file() and file_sha256(MODEL_PATH) == ARTIFACT_SHA256["model"]


def ensure_artifacts(runner: Runner = run) -> None:
    """Download and verify only an invalid artifact group."""
    if not extensions_valid():
        runner(
            "-m",
            "setup.download_extensions",
            "--extensions-dir",
            str(EXTENSIONS_DIR),
            "--force",
        )
        if not extensions_valid():
            raise SystemExit("SQLite extensions failed SHA256 verification.")

    if not model_valid():
        runner("-m", "setup.download_model", "--model-dir", str(MODEL_PATH.parent), "--force")
        if not model_valid():
            raise SystemExit("Embedding model failed SHA256 verification.")


def remove_database(path: Path) -> None:
    for suffix in ("", "-wal", "-shm", "-journal"):
        path.with_name(f"{path.name}{suffix}").unlink(missing_ok=True)


def rebuild_index(source_sha256: str, runner: Runner = run) -> None:
    """Replace the live database only after a complete, consistent ingest."""
    staging_db = DATA_DIR / ".memory.db.next"
    remove_database(staging_db)
    environment = os.environ | {"MEMORY_DB": str(staging_db)}

    try:
        runner("/app/ingest.py", env=environment)
        verified_source, _ = source_manifest()
        if verified_source != source_sha256:
            raise RuntimeError("Markdown sources changed during ingest; start again.")
        if not staging_db.is_file():
            raise RuntimeError("Ingest did not create a database.")

        os.replace(staging_db, MEMORY_DB)
        temporary = INDEX_FINGERPRINT.with_suffix(".sha256.tmp")
        temporary.write_text(f"{index_fingerprint(verified_source)}\n", encoding="utf-8")
        os.replace(temporary, INDEX_FINGERPRINT)
    finally:
        remove_database(staging_db)


def main() -> None:
    os.environ.update(
        NOTES_DIR=str(NOTES_DIR),
        MEMORY_DB=str(MEMORY_DB),
        EXTENSIONS_DIR=str(EXTENSIONS_DIR),
        MODEL_PATH=str(MODEL_PATH),
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with STARTUP_LOCK.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        source_sha256, file_count = source_manifest()
        if file_count == 0:
            raise SystemExit(f"No Markdown files found below {NOTES_DIR}")

        ensure_artifacts()
        current = index_fingerprint(source_sha256)
        saved = INDEX_FINGERPRINT.read_text(encoding="utf-8").strip() if INDEX_FINGERPRINT.exists() else None

        if not MEMORY_DB.exists() or saved != current:
            reason = "missing index" if not MEMORY_DB.exists() else "inputs changed"
            print(f"Rebuilding index: {reason} ({file_count} files)", file=sys.stderr, flush=True)
            rebuild_index(source_sha256)
        else:
            print(f"Index is current ({file_count} Markdown files)", file=sys.stderr, flush=True)

    os.execv(sys.executable, [sys.executable, "/app/server.py"])


if __name__ == "__main__":
    main()
