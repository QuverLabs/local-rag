"""Search and document-fetch logic over a sqlite-memory connection.

Shared between the MCP server (server.py) and the benchmark runner so neither
needs to import the other as a side-effect-laden module.
"""

from __future__ import annotations

import sqlite3

from setup._text import PASSAGE_PREFIX, normalize

_PASSAGE_PREFIX_BYTES = len(PASSAGE_PREFIX.encode())


def search(
    conn: sqlite3.Connection,
    query: str,
    limit: int,
    path_filter: str | None,
) -> tuple[list[dict], int]:
    """Hybrid (semantic + keyword) search. Returns (results, n_reconstructed).

    Vault offsets/lengths index the *prefixed* dbmem_content.value; the returned
    ``char_offset``/``char_length`` are translated into the stripped coordinate
    system so they align with what ``fetch_document`` returns.
    """
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
    # Must match the ingest-side normalization; see setup._text.
    params: list[object] = [normalize(query)]
    if path_filter:
        sql += " AND s.path LIKE ?"
        params.append(path_filter)
    sql += " LIMIT ?"
    # Negative LIMIT in SQLite disables limiting and returns the entire result
    # set; clamp at zero so a hostile or careless caller can't accidentally
    # ask for "everything".
    params.append(max(0, int(limit)))

    rows = conn.execute(sql, params).fetchall()
    results = []
    for r in rows:
        raw_offset = r[5]
        raw_length = r[6]
        if raw_offset >= _PASSAGE_PREFIX_BYTES:
            char_offset = raw_offset - _PASSAGE_PREFIX_BYTES
            char_length = raw_length
        else:
            # First chunk straddles the prefix; trim what overlaps.
            char_offset = 0
            char_length = max(0, raw_length - (_PASSAGE_PREFIX_BYTES - raw_offset))
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


def fetch_document(conn: sqlite3.Connection, path: str) -> dict:
    """Return the full indexed text of a single document keyed by exact path.

    Raises ``ValueError`` if ``path`` is not in the index.
    """
    row = conn.execute(
        """
        SELECT c.path, c.value, COUNT(v.seq) AS total_chunks
        FROM dbmem_content c
        LEFT JOIN dbmem_vault v ON v.hash = c.hash
        WHERE c.path = ?
        GROUP BY c.hash
        """,
        [path],
    ).fetchone()
    if row is None:
        raise ValueError(f"Document not indexed: {path!r}")
    content = (row[1] or "").removeprefix(PASSAGE_PREFIX)
    return {
        "path": row[0],
        "content": content,
        "length": len(content),
        "total_chunks": row[2],
    }
