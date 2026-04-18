"""FastMCP server exposing local_rag_search over a sqlite-memory database."""

from __future__ import annotations

import logging
import os
import sqlite3
import sys

# Configure logging to stderr BEFORE importing/instantiating FastMCP so stdout
# stays clean for JSON-RPC. Claude Desktop will fail to parse JSON if anything
# leaks onto stdout.
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

from fastmcp import FastMCP  # noqa: E402

from setup._db import (  # noqa: E402
    load_env,
    open_memory_connection,
    require_env_path,
    server_name,
    set_option,
)

load_env()
SERVER_NAME = server_name()
log = logging.getLogger(SERVER_NAME)


def _open_connection() -> sqlite3.Connection:
    memory_db = require_env_path("MEMORY_DB")
    extensions_dir = require_env_path("EXTENSIONS_DIR")
    model_path = require_env_path("MODEL_PATH")

    if not memory_db.exists():
        raise SystemExit(f"Memory database not found: {memory_db}. Run ingest.py first.")
    if not model_path.is_file():
        raise SystemExit(f"Model file not found: {model_path}. Run setup/download_model.py first.")

    connection = open_memory_connection(memory_db, extensions_dir, model_path, check_same_thread=False)

    vector_weight = float(os.environ.get("MEMORY_VECTOR_WEIGHT", 0.5))
    text_weight = float(os.environ.get("MEMORY_TEXT_WEIGHT", 0.5))
    max_results = int(os.environ.get("MEMORY_MAX_RESULTS", 10))
    min_score = float(os.environ.get("MEMORY_MIN_SCORE", 0.6))
    set_option(connection, "vector_weight", vector_weight)
    set_option(connection, "text_weight", text_weight)
    set_option(connection, "max_results", max_results)
    set_option(connection, "min_score", min_score)

    log.info(
        "Connected to %s (vector_weight=%.2f, text_weight=%.2f, max_results=%d, min_score=%.2f)",
        memory_db,
        vector_weight,
        text_weight,
        max_results,
        min_score,
    )
    return connection


conn = _open_connection()
mcp = FastMCP(SERVER_NAME)


@mcp.tool
def local_rag_search(query: str, limit: int = 5) -> list[dict]:
    """Hybrid (semantic + keyword) search over the local notes database.

    Returns up to `limit` hits, each with: path (source file), snippet (matching
    excerpt), ranking (relevance score; higher = better).
    """
    log.info("local_rag_search <- query=%r limit=%d", query, int(limit))
    # Pure-vector hits (no FTS5 match) come back with an empty snippet. Fall
    # back to the raw chunk text sliced out of dbmem_content.value via the
    # offset/length stored in dbmem_vault. Offsets are in UTF-8 *bytes*, so
    # we cast to BLOB before substr — TEXT substr would index by codepoint
    # and return garbage for non-ASCII spans.
    rows = conn.execute(
        """
        SELECT
            s.path,
            s.ranking,
            COALESCE(
                NULLIF(s.snippet, ''),
                CAST(substr(CAST(c.value AS BLOB), v.offset + 1, v.length) AS TEXT)
            ) AS text,
            (s.snippet IS NULL OR s.snippet = '') AS reconstructed
        FROM memory_search s
        JOIN dbmem_vault   v ON v.hash = s.hash AND v.seq = s.seq
        JOIN dbmem_content c ON c.hash = s.hash
        WHERE s.query = ?
        LIMIT ?
        """,
        [query, int(limit)],
    ).fetchall()

    results = [{"path": r[0], "snippet": (r[2] or "").strip(), "ranking": r[1]} for r in rows]
    reconstructed = sum(1 for r in rows if r[3])

    log.info(
        "local_rag_search -> %d hits (%d reconstructed from vault)",
        len(results),
        reconstructed,
    )
    for i, hit in enumerate(results, 1):
        snippet = (hit["snippet"] or "").replace("\n", " ")
        if len(snippet) > 120:
            snippet = f"{snippet[:117]}..."
        log.info("  hit %d ranking=%.4f path=%s snippet=%r", i, hit["ranking"], hit["path"], snippet)
    return results


def main() -> None:
    """Start the FastMCP server loop over stdio for Claude Desktop."""
    mcp.run()


if __name__ == "__main__":
    main()
