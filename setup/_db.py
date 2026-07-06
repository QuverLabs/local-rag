"""Shared helpers for the sqlite-memory connection used by ingest + server."""

from __future__ import annotations

import os
import sqlite3
import warnings
from pathlib import Path

# Silence macOS resource_tracker "leaked semaphore" warnings from the
# subprocess llama.cpp spawns. Must be set before multiprocessing imports;
# the tracker subprocess reads PYTHONWARNINGS at its own startup.
os.environ.setdefault("PYTHONWARNINGS", "ignore::UserWarning:multiprocessing.resource_tracker")
warnings.filterwarnings(
    "ignore",
    message=r"resource_tracker: There appear to be \d+ leaked semaphore objects",
    category=UserWarning,
    module=r"multiprocessing\.resource_tracker",
)

from dotenv import load_dotenv

from setup._platform import extension_suffix

DEFAULT_SERVER_NAME = "local-rag"


def repo_root() -> Path:
    """Absolute path to the repo root (parent of the ``setup`` package)."""
    return Path(__file__).resolve().parent.parent


def load_env(project_dir: Path | None = None) -> None:
    """Load a ``.env`` file from ``project_dir`` (or the repo root) if present."""
    env_file = (project_dir or repo_root()) / ".env"
    if env_file.exists():
        load_dotenv(env_file)


def server_name() -> str:
    """MCP server name. Configurable via MCP_SERVER_NAME env var."""
    return os.environ.get("MCP_SERVER_NAME") or DEFAULT_SERVER_NAME


def require_env(name: str) -> str:
    """Return env var ``name`` or exit with a clear error pointing at the .env file."""
    value = os.environ.get(name)
    if value is None:
        raise SystemExit(f"Missing required environment variable: {name} (check your .env file)")
    return value


def require_env_path(name: str) -> Path:
    """Resolve an env var to an absolute, expanded ``Path``."""
    return Path(require_env(name)).expanduser().resolve()


def env_float(name: str, default: float) -> float:
    """Read a float env var with a default fallback."""
    return float(os.environ.get(name, default))


def env_int(name: str, default: int) -> int:
    """Read an int env var with a default fallback."""
    return int(os.environ.get(name, default))


def load_extensions(conn: sqlite3.Connection, extensions_dir: Path) -> None:
    """Load the vector + memory sqlite extensions into ``conn`` from ``extensions_dir``."""
    suffix = extension_suffix()
    vector = extensions_dir / f"vector{suffix}"
    memory = extensions_dir / f"memory{suffix}"
    missing = [p for p in (vector, memory) if not p.exists()]
    if missing:
        names = ", ".join(p.name for p in missing)
        raise SystemExit(
            f"Extension(s) not found in {extensions_dir}: {names}. "
            f"Run 'uv run python -m setup.download_extensions' first."
        )
    conn.enable_load_extension(True)
    # Load vector BEFORE memory — memory depends on it.
    conn.load_extension(str(vector))
    conn.load_extension(str(memory))


def set_option(conn: sqlite3.Connection, key: str, value) -> None:
    """Set a sqlite-memory option (``memory_set_option``) on the given connection."""
    conn.execute("SELECT memory_set_option(?, ?)", [key, value])


def set_model(conn: sqlite3.Connection, model_path: Path) -> None:
    """Register the local embedding model. Per-connection state; re-apply on every open."""
    conn.execute("SELECT memory_set_model('local', ?)", [str(model_path)])


def open_memory_connection(
    memory_db: Path,
    extensions_dir: Path,
    model_path: Path,
    *,
    check_same_thread: bool = True,
) -> sqlite3.Connection:
    """Open a sqlite-memory connection with the vector+memory extensions and model loaded.

    Callers still apply their own ``set_option(...)`` calls afterwards — ingest and
    server need different option sets (chunk size vs. search tuning), so those stay
    at the call site.
    """
    conn = sqlite3.connect(memory_db, check_same_thread=check_same_thread)
    try:
        load_extensions(conn, extensions_dir)
        set_model(conn, model_path)
    except Exception:
        conn.close()
        raise
    return conn
