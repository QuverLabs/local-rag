from __future__ import annotations

import sqlite3

import pytest

from server import _fetch_document, _search


def _fixture_conn() -> sqlite3.Connection:
    """In-memory mirror of the dbmem_content / dbmem_vault / memory_search
    schema the server SQL joins over. memory_search is a virtual table in
    production; a plain table with the same columns reproduces the shape."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE dbmem_content (
            hash   INTEGER PRIMARY KEY,
            path   TEXT UNIQUE,
            value  TEXT,
            length INTEGER
        );
        CREATE TABLE dbmem_vault (
            hash   INTEGER,
            seq    INTEGER,
            offset INTEGER,
            length INTEGER,
            PRIMARY KEY (hash, seq)
        );
        CREATE TABLE memory_search (
            hash    INTEGER,
            seq     INTEGER,
            ranking REAL,
            path    TEXT,
            snippet TEXT,
            query   TEXT
        );
        """
    )
    # File A: stored value 36 bytes (prefix + "Hello world. Goodbye world."),
    # chunk 0 straddles the prefix so offset math has to reconcile it.
    conn.execute(
        "INSERT INTO dbmem_content VALUES (1, '/notes/a.md', 'passage: Hello world. Goodbye world.', 36)"
    )
    conn.execute("INSERT INTO dbmem_vault VALUES (1, 0, 0, 22)")  # "passage: Hello world. "
    conn.execute("INSERT INTO dbmem_vault VALUES (1, 1, 22, 14)")  # "Goodbye world."

    # File B: single-chunk, also prefix-padded.
    conn.execute("INSERT INTO dbmem_content VALUES (2, '/notes/b.md', 'passage: Another doc.', 21)")
    conn.execute("INSERT INTO dbmem_vault VALUES (2, 0, 0, 21)")

    # Rows keyed by the normalized query — no ``query:`` prefix (see
    # setup/_db.py for why).
    conn.execute("INSERT INTO memory_search VALUES (1, 0, 0.91, '/notes/a.md', 'Hello world', 'hello')")
    conn.execute("INSERT INTO memory_search VALUES (1, 1, 0.55, '/notes/a.md', '', 'hello')")
    conn.execute("INSERT INTO memory_search VALUES (2, 0, 0.40, '/notes/b.md', 'Another doc.', 'hello')")
    conn.commit()
    return conn


def test_fetch_document_strips_passage_prefix_and_reports_stripped_length():
    conn = _fixture_conn()
    assert _fetch_document(conn, "/notes/a.md") == {
        "path": "/notes/a.md",
        "content": "Hello world. Goodbye world.",
        "length": 27,
        "total_chunks": 2,
    }


def test_fetch_document_missing_path_raises_value_error():
    conn = _fixture_conn()
    with pytest.raises(ValueError, match="not indexed"):
        _fetch_document(conn, "/notes/missing.md")


def test_search_normalizes_query_before_lookup():
    # Fullwidth input only matches the `hello`-keyed fixture rows *after*
    # NFKC folds it to ASCII. If `_search` stops calling normalize(), this
    # test starts seeing 0 rows — which is the whole point of the guard.
    conn = _fixture_conn()
    results, _ = _search(conn, "ｈｅｌｌｏ", limit=5, path_filter=None)
    assert len(results) == 3


def test_search_does_not_prepend_query_prefix():
    # Regression guard: the ``query:`` prefix AND-s an unindexed token into
    # every FTS5 match. If re-added, rows keyed by the prefixed form would
    # match and the assert would fail.
    conn = _fixture_conn()
    conn.execute("INSERT INTO dbmem_content VALUES (9, '/notes/c.md', 'passage: decoy', 14)")
    conn.execute("INSERT INTO dbmem_vault VALUES (9, 0, 0, 14)")
    conn.execute("INSERT INTO memory_search VALUES (9, 0, 0.10, '/notes/c.md', 'decoy', 'query: marker')")
    results, _ = _search(conn, "marker", limit=5, path_filter=None)
    assert results == []


def test_search_hit_includes_chunk_metadata():
    """Chunk metadata is reported in the coordinate system the caller sees,
    i.e. the ``passage: `` (9 byte) prefix is removed: chunk 0 spans the
    first 13 bytes ("Hello world. ") of the stripped content; chunk 1
    starts at byte 13 and runs 14 bytes ("Goodbye world.")."""
    conn = _fixture_conn()
    results, _ = _search(conn, "hello", limit=5, path_filter=None)
    # Pick by stable identity (path + chunk_index) — _search has no ORDER BY.
    first = next(r for r in results if r["path"] == "/notes/a.md" and r["chunk_index"] == 0)
    second = next(r for r in results if r["path"] == "/notes/a.md" and r["chunk_index"] == 1)
    assert first["total_chunks"] == 2
    assert first["char_offset"] == 0
    assert first["char_length"] == 13  # 22 raw bytes - 9 prefix bytes
    assert second["char_offset"] == 13  # 22 raw bytes - 9 prefix bytes
    assert second["char_length"] == 14  # unchanged — chunk past the prefix


def test_search_reconstructs_snippet_from_vault_when_empty():
    """Second row in the fixture has an empty FTS snippet → reconstructed
    from ``dbmem_content.value`` via vault offset; the 'passage: ' prefix
    must not leak into the returned snippet."""
    conn = _fixture_conn()
    results, reconstructed = _search(conn, "hello", limit=5, path_filter=None)
    assert reconstructed == 1
    rebuilt = next(r for r in results if r["chunk_index"] == 1)
    assert rebuilt["snippet"] == "Goodbye world."


def test_search_strips_passage_prefix_from_any_returned_snippet():
    """If an FTS snippet (or a reconstructed one) happens to start with
    'passage: ' it must be stripped before reaching the caller."""
    conn = _fixture_conn()
    conn.execute(
        "INSERT INTO memory_search VALUES (2, 0, 0.77, '/notes/b.md', 'passage: Another doc.', 'polluted')"
    )
    results, _ = _search(conn, "polluted", limit=5, path_filter=None)
    assert results[0]["snippet"] == "Another doc."


def test_search_path_filter_restricts_results_to_matching_paths():
    conn = _fixture_conn()
    results, _ = _search(conn, "hello", limit=5, path_filter="%a.md")
    assert [r["path"] for r in results] == ["/notes/a.md", "/notes/a.md"]


def test_search_path_filter_with_no_matches_returns_empty():
    conn = _fixture_conn()
    assert _search(conn, "hello", limit=5, path_filter="%nowhere%") == ([], 0)


def test_search_without_path_filter_returns_all_hits():
    conn = _fixture_conn()
    results, _ = _search(conn, "hello", limit=5, path_filter=None)
    assert {r["path"] for r in results} == {"/notes/a.md", "/notes/b.md"}
    assert len(results) == 3


def test_search_respects_limit():
    conn = _fixture_conn()
    results, _ = _search(conn, "hello", limit=1, path_filter=None)
    assert len(results) == 1
