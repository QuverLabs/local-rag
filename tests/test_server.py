from __future__ import annotations

import sqlite3

import pytest

from server import _fetch_document, _search


def _fixture_conn() -> sqlite3.Connection:
    """An in-memory DB that mirrors the subset of sqlite-memory's schema the
    server's SQL touches (dbmem_content, dbmem_vault, memory_search).

    memory_search is a virtual table in production, but its column shape is
    stable (hash, seq, ranking, path, snippet) and we also need a query-like
    column for the fixture's WHERE clause. A plain table with those columns
    plus ``query`` reproduces the shape faithfully for these tests.

    Ingest stores values with a ``passage: `` prefix (so the e5-instruct
    embedding gets the signal it was trained on). Server strips that prefix
    before handing content to callers and prepends ``query: `` to user
    queries before hitting memory_search. The fixture below reflects those
    invariants.
    """
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
    # File A: stored with 'passage: ' prefix. Raw content (post-strip) is 27
    # chars, stored value is 36 chars. Chunks are indexed against the stored
    # value, so chunk 0 spans the prefix + first sentence.
    conn.execute(
        "INSERT INTO dbmem_content VALUES (1, '/notes/a.md', 'passage: Hello world. Goodbye world.', 36)"
    )
    conn.execute("INSERT INTO dbmem_vault VALUES (1, 0, 0, 22)")  # "passage: Hello world. "
    conn.execute("INSERT INTO dbmem_vault VALUES (1, 1, 22, 14)")  # "Goodbye world."

    # File B: single-chunk, also prefixed.
    conn.execute("INSERT INTO dbmem_content VALUES (2, '/notes/b.md', 'passage: Another doc.', 21)")
    conn.execute("INSERT INTO dbmem_vault VALUES (2, 0, 0, 21)")

    # Search rows are keyed by the prepended query form ('query: hello').
    # When the test calls _search(conn, 'hello', ...) the server should
    # prepend 'query: ' before looking up in memory_search.
    conn.execute(
        "INSERT INTO memory_search VALUES (1, 0, 0.91, '/notes/a.md', 'Hello world', 'query: hello')"
    )
    conn.execute("INSERT INTO memory_search VALUES (1, 1, 0.55, '/notes/a.md', '', 'query: hello')")
    conn.execute(
        "INSERT INTO memory_search VALUES (2, 0, 0.40, '/notes/b.md', 'Another doc.', 'query: hello')"
    )
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


def test_search_prepends_query_prefix_before_lookup():
    """Caller passes the raw user query; _search internally prepends
    'query: ' so it matches how the text was indexed (with 'passage: ')."""
    conn = _fixture_conn()
    results, _ = _search(conn, "hello", limit=5, path_filter=None)
    assert len(results) == 3  # fixture seeded with 'query: hello'


def test_search_hit_includes_chunk_metadata():
    conn = _fixture_conn()
    results, _ = _search(conn, "hello", limit=5, path_filter=None)
    first = results[0]
    assert first["chunk_index"] == 0
    assert first["total_chunks"] == 2
    assert first["char_offset"] == 0
    assert first["char_length"] == 22


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
        "INSERT INTO memory_search VALUES (2, 0, 0.77, '/notes/b.md', 'passage: Another doc.', 'query: polluted')"
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
