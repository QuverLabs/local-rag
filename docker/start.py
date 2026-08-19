"""Prepare artifacts, refresh a stale index, and start the stdio MCP server."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


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


def run(*args: str) -> None:
    """Run a required preparation step and stop immediately on failure."""
    subprocess.run([sys.executable, *args], check=True)  # noqa: S603


def write_manifest(path: Path, value: str) -> None:
    """Atomically store the manifest only after a successful ingest."""
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(f"{value}\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    notes_dir = Path(os.environ["NOTES_DIR"])
    memory_db = Path(os.environ["MEMORY_DB"])
    extensions_dir = Path(os.environ["EXTENSIONS_DIR"])
    model_path = Path(os.environ["MODEL_PATH"])
    manifest_path = memory_db.with_name(f"{memory_db.name}.sources.sha256")

    run("-m", "setup.download_extensions", "--extensions-dir", str(extensions_dir))
    run("-m", "setup.download_model", "--model-dir", str(model_path.parent))

    current_manifest, file_count = source_manifest(notes_dir)
    saved_manifest = manifest_path.read_text(encoding="utf-8").strip() if manifest_path.exists() else None

    if not memory_db.exists() or saved_manifest != current_manifest:
        reason = "missing index" if not memory_db.exists() else "Markdown sources changed"
        print(f"Rebuilding index: {reason} ({file_count} files)", file=sys.stderr, flush=True)
        run("/app/ingest.py")

        verified_manifest, _ = source_manifest(notes_dir)
        if verified_manifest != current_manifest:
            raise SystemExit("Markdown sources changed during ingest; run the container again.")
        write_manifest(manifest_path, verified_manifest)
    else:
        print(f"Index is current ({file_count} Markdown files)", file=sys.stderr, flush=True)

    os.execv(sys.executable, [sys.executable, "/app/server.py"])


if __name__ == "__main__":
    main()
