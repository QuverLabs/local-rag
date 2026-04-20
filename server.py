"""FastMCP server exposing local_rag_search + local_rag_fetch_document over a sqlite-memory database."""

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
    PASSAGE_PREFIX,
    QUERY_PREFIX,
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


# Lazy singleton so importing this module (e.g. from tests) does not open the DB.
_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = _open_connection()
    return _conn


mcp = FastMCP(SERVER_NAME)


def _search(
    conn: sqlite3.Connection,
    query: str,
    limit: int,
    path_filter: str | None,
) -> tuple[list[dict], int]:
    # Pure-vector hits (no FTS5 match) come back with an empty snippet. Fall
    # back to the raw chunk text sliced out of dbmem_content.value via the
    # offset/length stored in dbmem_vault. Offsets are in UTF-8 *bytes*, so
    # we cast to BLOB before substr — TEXT substr would index by codepoint
    # and return garbage for non-ASCII spans.
    sql = """
        SELECT
            s.path,
            s.ranking,
            COALESCE(
                NULLIF(s.snippet, ''),
                CAST(substr(CAST(c.value AS BLOB), v.offset + 1, v.length) AS TEXT)
            ) AS text,
            (s.snippet IS NULL OR s.snippet = '') AS reconstructed,
            s.seq,
            v.offset,
            v.length,
            (SELECT COUNT(*) FROM dbmem_vault WHERE hash = s.hash) AS total_chunks
        FROM memory_search s
        JOIN dbmem_vault   v ON v.hash = s.hash AND v.seq = s.seq
        JOIN dbmem_content c ON c.hash = s.hash
        WHERE s.query = ?
    """
    params: list[object] = [QUERY_PREFIX + query]
    if path_filter:
        sql += " AND s.path LIKE ?"
        params.append(path_filter)
    sql += " LIMIT ?"
    # Negative LIMIT in SQLite disables limiting and returns the entire result
    # set; clamp at zero so a hostile or careless caller can't accidentally
    # ask for "everything".
    params.append(max(0, int(limit)))

    rows = conn.execute(sql, params).fetchall()
    # Vault offsets/lengths are coordinates inside the *prefixed* dbmem_content
    # value, but the snippet and fetch_document content have ``passage: `` stripped
    # before reaching the caller. Translate offsets into the stripped coordinate
    # system so they actually point at the chunk in the text the caller sees.
    prefix_bytes = len(PASSAGE_PREFIX.encode("utf-8"))
    results = []
    for r in rows:
        raw_offset = r[5]
        raw_length = r[6]
        if raw_offset >= prefix_bytes:
            char_offset = raw_offset - prefix_bytes
            char_length = raw_length
        else:
            # First chunk includes the prefix bytes; trim them off the front.
            char_offset = 0
            char_length = max(0, raw_length - (prefix_bytes - raw_offset))
        results.append(
            {
                "path": r[0],
                "snippet": (r[2] or "").removeprefix(PASSAGE_PREFIX).strip(),
                "ranking": r[1],
                "chunk_index": r[4],
                "total_chunks": r[7],
                "char_offset": char_offset,
                "char_length": char_length,
            }
        )
    reconstructed = sum(1 for r in rows if r[3])
    return results, reconstructed


def _fetch_document(conn: sqlite3.Connection, path: str) -> dict:
    row = conn.execute(
        "SELECT path, value FROM dbmem_content WHERE path = ?",
        [path],
    ).fetchone()
    if row is None:
        raise ValueError(f"Document not indexed: {path!r}")

    total_chunks = conn.execute(
        "SELECT COUNT(*) FROM dbmem_vault WHERE hash = (SELECT hash FROM dbmem_content WHERE path = ?)",
        [path],
    ).fetchone()[0]

    content = (row[1] or "").removeprefix(PASSAGE_PREFIX)
    return {
        "path": row[0],
        "content": content,
        "length": len(content),
        "total_chunks": total_chunks,
    }


@mcp.tool
def local_rag_search(
    query: str,
    limit: int = 5,
    path_filter: str | None = None,
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
    log.info(
        "local_rag_search <- query=%r limit=%d path_filter=%r",
        query,
        int(limit),
        path_filter,
    )
    results, reconstructed = _search(_get_conn(), query, int(limit), path_filter)

    log.info(
        "local_rag_search -> %d hits (%d reconstructed from vault)",
        len(results),
        reconstructed,
    )
    for i, hit in enumerate(results, 1):
        snippet = (hit["snippet"] or "").replace("\n", " ")
        if len(snippet) > 120:
            snippet = f"{snippet[:117]}..."
        log.info(
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
def local_rag_fetch_document(path: str) -> dict:
    """Return the full indexed text of a single document, keyed by exact path.

    Use this after ``local_rag_search`` when a snippet is truncated, when a chunk
    boundary cuts mid-sentence, or when you need to verify the surrounding context
    around a hit. ``path`` must match a value from ``local_rag_search``'s ``path``
    field exactly.

    Returns ``{path, content, length, total_chunks}``. Raises ``ValueError`` if the
    path is not in the index.
    """
    log.info("local_rag_fetch_document <- path=%r", path)
    result = _fetch_document(_get_conn(), path)
    log.info(
        "local_rag_fetch_document -> %d chars, %d chunks",
        len(result["content"]),
        result["total_chunks"],
    )
    return result


def main() -> None:
    """Start the FastMCP server loop over stdio for Claude Desktop."""
    _get_conn()  # eager open so connection errors surface at startup, not first tool call
    mcp.run()


if __name__ == "__main__":
    main()
