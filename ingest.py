"""Index a directory of markdown notes into a sqlite-memory database."""

from __future__ import annotations

import os
import sqlite3
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from setup._db import load_extensions, require_env, set_option


def main() -> int:
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)

    notes_dir = Path(require_env("NOTES_DIR")).expanduser().resolve()
    memory_db = Path(require_env("MEMORY_DB")).expanduser().resolve()
    extensions_dir = Path(require_env("EXTENSIONS_DIR")).expanduser().resolve()
    model_path = Path(require_env("MODEL_PATH")).expanduser().resolve()

    if not notes_dir.is_dir():
        raise SystemExit(f"NOTES_DIR does not exist or is not a directory: {notes_dir}")
    if not model_path.is_file():
        raise SystemExit(
            f"Model file not found: {model_path}. "
            f"Run 'uv run python -m setup.download_model' first."
        )

    memory_db.parent.mkdir(parents=True, exist_ok=True)

    vector_weight = float(os.environ.get("MEMORY_VECTOR_WEIGHT", 0.5))
    text_weight = float(os.environ.get("MEMORY_TEXT_WEIGHT", 0.5))

    conn = sqlite3.connect(memory_db)
    try:
        load_extensions(conn, extensions_dir)
        conn.execute("SELECT memory_set_model('local', ?)", [str(model_path)])
        set_option(conn, "max_tokens", 512)
        set_option(conn, "overlap_tokens", 100)
        set_option(conn, "vector_weight", vector_weight)
        set_option(conn, "text_weight", text_weight)

        context_name = notes_dir.name or "notes"
        print(
            f"Indexing {notes_dir} as context {context_name!r} into {memory_db} "
            f"(vector_weight={vector_weight}, text_weight={text_weight})...",
            file=sys.stderr,
        )

        start = time.perf_counter()
        conn.execute("SELECT memory_add_directory(?, ?)", [str(notes_dir), context_name])
        conn.commit()
        elapsed = time.perf_counter() - start

        print(f"Ingest finished in {elapsed:.1f}s", file=sys.stderr)

        sample = conn.execute(
            "SELECT path, length(snippet) FROM memory_search WHERE query = ? LIMIT 3",
            ["test"],
        ).fetchall()
        print(f"Sanity-check search returned {len(sample)} rows. Example rows:")
        for row in sample:
            print(f"  {row}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
