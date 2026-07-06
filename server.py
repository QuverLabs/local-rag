"""FastMCP server exposing local_rag_search + local_rag_fetch_document over a sqlite-memory database."""

from __future__ import annotations

import logging
import sys
import threading
from contextlib import asynccontextmanager

# Configure logging to stderr BEFORE importing/instantiating FastMCP so stdout
# stays clean for JSON-RPC. Claude Desktop will fail to parse JSON if anything
# leaks onto stdout.
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

from fastmcp import Context, FastMCP  # noqa: E402
from fastmcp.dependencies import CurrentContext  # noqa: E402

from setup._db import (  # noqa: E402
    env_float,
    env_int,
    load_env,
    open_memory_connection,
    require_env_path,
    server_name,
    set_option,
)
from setup._search import fetch_document, search  # noqa: E402

load_env()
SERVER_NAME = server_name()
log = logging.getLogger(SERVER_NAME)


def _open_connection():
    memory_db = require_env_path("MEMORY_DB")
    extensions_dir = require_env_path("EXTENSIONS_DIR")
    model_path = require_env_path("MODEL_PATH")

    if not memory_db.exists():
        raise SystemExit(f"Memory database not found: {memory_db}. Run ingest.py first.")
    if not model_path.is_file():
        raise SystemExit(f"Model file not found: {model_path}. Run setup/download_model.py first.")

    conn = open_memory_connection(memory_db, extensions_dir, model_path, check_same_thread=False)

    vector_weight = env_float("MEMORY_VECTOR_WEIGHT", 0.5)
    text_weight = env_float("MEMORY_TEXT_WEIGHT", 0.5)
    max_results = env_int("MEMORY_MAX_RESULTS", 10)
    min_score = env_float("MEMORY_MIN_SCORE", 0.6)
    set_option(conn, "vector_weight", vector_weight)
    set_option(conn, "text_weight", text_weight)
    set_option(conn, "max_results", max_results)
    set_option(conn, "min_score", min_score)

    log.info(
        "Connected to %s (vector_weight=%.2f, text_weight=%.2f, max_results=%d, min_score=%.2f)",
        memory_db,
        vector_weight,
        text_weight,
        max_results,
        min_score,
    )
    return conn


@asynccontextmanager
async def _lifespan(server):
    conn = _open_connection()
    lock = threading.Lock()
    try:
        yield {"conn": conn, "lock": lock}
    finally:
        conn.close()


mcp = FastMCP(SERVER_NAME, lifespan=_lifespan)


@mcp.tool
def local_rag_search(
    query: str,
    limit: int = 5,
    path_filter: str | None = None,
    ctx: Context = CurrentContext(),
) -> list[dict]:
    """Hybrid (semantic + keyword) search over the local notes database.

    Returns up to ``limit`` hits. Each hit carries:

    - ``path`` — absolute path of the source file
    - ``snippet`` — matching excerpt (empty FTS snippets are reconstructed from raw chunk bytes)
    - ``ranking`` — relevance score; higher is better
    - ``chunk_index`` — 0-based position of this chunk inside the file
    - ``total_chunks`` — how many chunks the file was split into
    - ``char_offset`` / ``char_length`` — byte-offset and byte-length of the chunk
      inside the returned ``content`` (i.e. with the ``passage: `` indexing prefix
      already stripped, so the offsets line up with what ``local_rag_fetch_document`` returns)

    When ``path_filter`` is provided it is applied as a SQL ``LIKE`` over the source path
    (use ``%`` for wildcards), letting callers scope a query to one document or subtree.
    """
    log.info("local_rag_search <- query=%r limit=%d path_filter=%r", query, limit, path_filter)
    with ctx.lifespan_context["lock"]:
        results, reconstructed = search(ctx.lifespan_context["conn"], query, limit, path_filter)
    log.info(
        "local_rag_search -> %d hits (%d reconstructed from vault)",
        len(results),
        reconstructed,
    )
    if log.isEnabledFor(logging.DEBUG):
        for i, hit in enumerate(results, 1):
            snippet = (hit["snippet"] or "").replace("\n", " ")
            if len(snippet) > 120:
                snippet = f"{snippet[:117]}..."
            log.debug(
                "  hit %d ranking=%.4f chunk=%d/%d path=%s snippet=%r",
                i,
                hit["ranking"],
                hit["chunk_index"],
                hit["total_chunks"],
                hit["path"],
                snippet,
            )
    return results


@mcp.tool
def local_rag_fetch_document(path: str, ctx: Context = CurrentContext()) -> dict:
    """Return the full indexed text of a single document, keyed by exact path.

    Use this after ``local_rag_search`` when a snippet is truncated, when a chunk
    boundary cuts mid-sentence, or when you need to verify the surrounding context
    around a hit. ``path`` must match a value from ``local_rag_search``'s ``path``
    field exactly.

    Returns ``{path, content, length, total_chunks}``. Raises ``ValueError`` if the
    path is not in the index.
    """
    log.info("local_rag_fetch_document <- path=%r", path)
    with ctx.lifespan_context["lock"]:
        result = fetch_document(ctx.lifespan_context["conn"], path)
    log.info(
        "local_rag_fetch_document -> %d chars, %d chunks",
        len(result["content"]),
        result["total_chunks"],
    )
    return result


def main() -> None:
    """Start the FastMCP server loop over stdio for Claude Desktop."""
    mcp.run()


if __name__ == "__main__":
    main()
