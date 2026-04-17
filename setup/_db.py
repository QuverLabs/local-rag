"""Shared helpers for the sqlite-memory connection used by ingest + server."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from setup._platform import extension_suffix

DEFAULT_SERVER_NAME = "local-rag"


def server_name() -> str:
    """MCP server name. Configurable via MCP_SERVER_NAME env var."""
    return os.environ.get("MCP_SERVER_NAME") or DEFAULT_SERVER_NAME


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name} (check your .env file)")
    return value


def load_extensions(conn: sqlite3.Connection, extensions_dir: Path) -> None:
    suffix = extension_suffix()
    vector = extensions_dir / f"vector{suffix}"
    memory = extensions_dir / f"memory{suffix}"
    if not vector.exists() or not memory.exists():
        raise SystemExit(
            f"Extensions not found in {extensions_dir}. "
            f"Run 'uv run python -m setup.download_extensions' first."
        )
    conn.enable_load_extension(True)
    # Load vector BEFORE memory — memory depends on it.
    conn.load_extension(str(vector))
    conn.load_extension(str(memory))


def set_option(conn: sqlite3.Connection, key: str, value) -> None:
    conn.execute("SELECT memory_set_option(?, ?)", [key, value])
