"""Index a directory of markdown notes into a sqlite-memory database."""

from __future__ import annotations

import os

# Silence macOS resource_tracker "leaked semaphore" warnings emitted by the
# subprocess llama.cpp spawns. Must be set before multiprocessing imports,
# because the tracker subprocess reads PYTHONWARNINGS at its own startup.
os.environ.setdefault("PYTHONWARNINGS", "ignore::UserWarning:multiprocessing.resource_tracker")

import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

from setup._db import (  # noqa: E402
    PASSAGE_PREFIX,
    load_env,
    open_memory_connection,
    require_env_path,
    set_option,
)

warnings.filterwarnings(
    "ignore",
    message=r"resource_tracker: There appear to be \d+ leaked semaphore objects",
    category=UserWarning,
    module=r"multiprocessing\.resource_tracker",
)


def main() -> int:
    """Index markdown notes from NOTES_DIR into MEMORY_DB. Exit 0 on full success, 1 on partial."""
    load_env()

    notes_dir = require_env_path("NOTES_DIR")
    memory_db = require_env_path("MEMORY_DB")
    extensions_dir = require_env_path("EXTENSIONS_DIR")
    model_path = require_env_path("MODEL_PATH")

    if not notes_dir.is_dir():
        raise SystemExit(f"NOTES_DIR does not exist or is not a directory: {notes_dir}")
    if not model_path.is_file():
        raise SystemExit(
            f"Model file not found: {model_path}. Run 'uv run python -m setup.download_model' first."
        )

    memory_db.parent.mkdir(parents=True, exist_ok=True)

    removed = []
    for suffix in ("", "-wal", "-shm", "-journal"):
        stale = memory_db.with_name(memory_db.name + suffix)
        if stale.exists():
            stale.unlink()
            removed.append(stale.name)
    if removed:
        print(f"Removed existing index: {', '.join(removed)}", file=sys.stderr, flush=True)

    vector_weight = float(os.environ.get("MEMORY_VECTOR_WEIGHT", 0.5))
    text_weight = float(os.environ.get("MEMORY_TEXT_WEIGHT", 0.5))
    # 512/100 tokens hangs the chunker on some Polish markdown files (infinite
    # loop inside llama.cpp, uninterruptible from Python). 256/50 works and is
    # a fine chunk size for retrieval. Override via env if you want to risk it.
    max_tokens = int(os.environ.get("MEMORY_MAX_TOKENS", 256))
    overlap_tokens = int(os.environ.get("MEMORY_OVERLAP_TOKENS", 50))

    conn = open_memory_connection(memory_db, extensions_dir, model_path)
    try:
        set_option(conn, "max_tokens", max_tokens)
        set_option(conn, "overlap_tokens", overlap_tokens)
        set_option(conn, "vector_weight", vector_weight)
        set_option(conn, "text_weight", text_weight)

        context_name = notes_dir.name or "notes"
        files = sorted(notes_dir.rglob("*.md"))

        print(
            f"Indexing {notes_dir}\n"
            f"  context: {context_name!r}\n"
            f"  {len(files)} markdown files\n"
            f"Into     {memory_db}\n"
            f"\n"
            f"Params\n"
            f"  - max_tokens:     {max_tokens}\n"
            f"  - overlap_tokens: {overlap_tokens}\n"
            f"  - vector_weight:  {vector_weight}\n"
            f"  - text_weight:    {text_weight}\n",
            file=sys.stderr,
            flush=True,
        )

        if not files:
            print("No .md files found — nothing to index.", file=sys.stderr)
            return 0

        start = time.perf_counter()
        failed: list[tuple[Path, str]] = []
        total = len(files)
        width = len(str(total))
        for i, path in enumerate(files, 1):
            rel = path.relative_to(notes_dir)
            prefix = f"[{i:>{width}}/{total}]"
            # "-->" line prints before the call so, if the native chunker
            # hangs (uninterruptible from Python), you can see which file
            # it's stuck on.
            print(f"{prefix} -->            {rel}", file=sys.stderr, flush=True)
            t0 = time.perf_counter()
            try:
                # Read + prefix + add_text (instead of memory_add_file) so we can
                # prepend the 'passage: ' prompt the e5-instruct model was trained
                # for. memory_add_text auto-generates a hex path; we UPDATE it to
                # the real file path so fetch_document and path_filter still work.
                text = path.read_text(encoding="utf-8")
                prefixed = f"{PASSAGE_PREFIX}{text}"
                # The extension dedupes by content hash: two files with identical
                # bytes share one dbmem_content row. UPDATE-by-value would then
                # silently overwrite the first file's path. Detect that case up
                # front and surface it as a per-file failure instead of clobbering.
                existing = conn.execute(
                    "SELECT path FROM dbmem_content WHERE value = ?",
                    [prefixed],
                ).fetchone()
                if existing is not None:
                    raise RuntimeError(
                        f"identical content already indexed under {existing[0]!r}; "
                        "deduplicate the source files."
                    )
                conn.execute("SELECT memory_add_text(?, ?)", [prefixed, context_name])
                updated = conn.execute(
                    "UPDATE dbmem_content SET path = ? WHERE value = ?",
                    [str(path), prefixed],
                ).rowcount
                if updated != 1:
                    raise RuntimeError(f"expected 1 dbmem_content row to update, got {updated}")
                conn.commit()
                status = "ok  "
                detail = ""
            except Exception as exc:
                conn.rollback()
                failed.append((rel, f"{type(exc).__name__}: {exc}"))
                status = "FAIL"
                detail = f"  [{type(exc).__name__}: {exc}]"
            dt = time.perf_counter() - t0
            print(
                f"{prefix} {status} ({dt:5.1f}s) {rel}{detail}",
                file=sys.stderr,
                flush=True,
            )
        elapsed = time.perf_counter() - start

        ok = total - len(failed)
        print(
            f"\nIngest finished in {elapsed:.1f}s ({ok}/{total} files, {len(failed)} failed)",
            file=sys.stderr,
        )

        sample = conn.execute(
            "SELECT path, length(snippet) FROM memory_search WHERE query = ? LIMIT 3",
            ["test"],
        ).fetchall()
        print(f"Sanity-check search returned {len(sample)} rows. Example rows:")
        for row in sample:
            print(f"  {row}")
    finally:
        conn.close()

    # Non-zero exit so CI / scripts can detect partial failures.
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
