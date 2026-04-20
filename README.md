# local-rag

Local Retrieval-Augmented Generation over your markdown notes, exposed to
Claude Desktop as an MCP tool. Your notes, your machine — no cloud, no API
keys, no external vector DB.

## What it does

- Indexes a folder of `.md` files into a local SQLite database.
- Embeds every chunk with [`multilingual-e5-large-instruct`](https://huggingface.co/Ralriki/multilingual-e5-large-instruct-GGUF)
  (GGUF, 1024 dim — strong Polish support).
- Runs hybrid search (semantic + FTS5) via the
  [`sqlite-memory`](https://github.com/sqliteai/sqlite-memory) extension.
- Exposes a `local_rag_search` tool over stdio MCP (FastMCP), so Claude pulls
  relevant context from your notes inside any conversation.

## Requirements

- **macOS** (Apple Silicon) for indexing; **Windows x64** supported for
  server-only via a self-contained ZIP bundle.
- **Python 3.14+** (Homebrew — the system Python on macOS cannot load SQLite
  extensions).
- **uv** (`brew install uv`).
- **~1.5 GB** disk (model + DB).
- **Claude Desktop** installed.

---

## Quickstart (macOS)

```bash
brew install python@3.14 uv
git clone <this-repo> local-rag && cd local-rag
uv sync

# One-time downloads
uv run python -m setup.download_extensions   # ~2 MB, SQLite extensions
uv run python -m setup.download_model        # ~603 MB, embedding model

# Configure
cp .env.example .env
# Edit .env and set NOTES_DIR to the folder with your .md files

# Build the index
uv run python ingest.py
```

Verify the MCP server runs before wiring Claude Desktop (optional):

```bash
npx @modelcontextprotocol/inspector uv run --directory "$PWD" server.py
```

### Wire into Claude Desktop

```bash
uv run python -m setup.install_claude_desktop
```

This auto-detects `uv`, the repo path, and `MCP_SERVER_NAME` from `.env`
(default `local-rag`), then merges an entry into
`~/Library/Application Support/Claude/claude_desktop_config.json` (existing
file backed up as `.bak`; other MCP servers preserved). Restart Claude
Desktop.

**Flags:** `--uv <path>`, `--project-dir <path>`, `--name <id>`.

**Multiple deployments:** clone into a separate folder and set a distinct
`MCP_SERVER_NAME` in its `.env` (e.g. `work-notes`, `personal-notes`).

**Manual setup:** copy `claude_desktop_config.example.json` into the config
path above and replace the placeholder paths.

---

## Deploy to Windows (server-only)

The bundle is a self-contained ZIP with code, index, model, extensions, and a
portable `uv.exe`. The recipient unzips, double-clicks `install.bat`, restarts
Claude Desktop — no admin rights, no internet at install time.

### Build the bundle (on macOS, after a successful ingest)

```bash
uv run python -m scripts.make_bundle
```

Output: `dist/rag-bundle-YYYY-MM-DD-HHMM.zip` (~1 GB). Contents:

| Path                        | What                                                   |
|-----------------------------|--------------------------------------------------------|
| `source/`                   | code + `uv.lock` (exact dep set reproduced on Windows) |
| `data/memory.db`            | your indexed notes                                     |
| `data/models/*.gguf`        | embedding model                                        |
| `data/extensions/*.dll`     | `vector.dll` + `memory.dll` (Windows x64)              |
| `bin/uv.exe`                | portable uv                                            |
| `install.ps1` + `.bat`      | one-click installer                                    |
| `README-windows.md`         | end-user instructions                                  |
| `manifest.json`             | SHA256 of every file                                   |

**Flags:** `--force` (overwrite), `--uv-version X.Y.Z` (pin portable uv),
`--name my-bundle`.

### Install on Windows

1. Unzip the bundle anywhere (e.g. `C:\Users\<you>\rag-bundle\`). Keep the
   folder — the installer writes absolute paths into it.
2. Double-click `install.bat`. It runs `uv sync` in `source\`, writes
   `source\.env` with bundle paths, and registers `local-rag` in
   `%APPDATA%\Claude\claude_desktop_config.json` (existing file backed up to
   `.bak`).
3. Restart Claude Desktop. The `local_rag_search` tool should appear.

### Update the Windows index

`memory.db` is a frozen snapshot. To refresh:

- **Index changed, everything else same:** re-run `ingest.py` on the Mac,
  copy the new `data/memory.db` over the Windows one. No reinstall.
- **Model or extension version changed:** rebuild the bundle and ship the
  full ZIP.

### Moving the bundle folder

Paths in `source/.env` are absolute. If the folder moves on Windows, re-run
`install.bat` to rewrite `.env` and the config entry.

---

## How it works

**Ingest** (`ingest.py`): opens SQLite → loads `sqlite-vector` then
`sqlite-memory` → sets the local model → calls
`memory_add_directory(NOTES_DIR, context)`. The extension walks the tree,
chunks markdown structurally (512-token chunks, 100-token overlap), embeds
each chunk via llama.cpp, and stores both the vector and raw text for FTS5.

**Serve** (`server.py`): FastMCP stdio server that re-opens the same DB,
reloads the extensions and model (per-connection state), and exposes two
tools:

```python
local_rag_search(query: str, limit: int = 5, path_filter: str | None = None) -> list[dict]
# each hit: {
#   "path": str, "snippet": str, "ranking": float,
#   "chunk_index": int, "total_chunks": int,
#   "char_offset": int, "char_length": int,
# }
# path_filter is a SQL LIKE pattern over the source path (use % as wildcard)
# so callers can scope a query to one document or subtree.

local_rag_fetch_document(path: str) -> dict
# returns: {"path": str, "content": str, "length": int, "total_chunks": int}
# use this after search when a snippet is truncated, a chunk boundary cuts
# mid-sentence, or you need the surrounding context around a hit.
```

## Configuration (`.env`)

| Variable                | Default        | Purpose                                          |
|-------------------------|----------------|--------------------------------------------------|
| `MCP_SERVER_NAME`       | `local-rag`    | Server name in `claude_desktop_config.json`      |
| `NOTES_DIR`             | —              | Folder of `.md` files to index                   |
| `MEMORY_DB`             | —              | SQLite file (created on first ingest)            |
| `EXTENSIONS_DIR`        | —              | Directory with `vector`/`memory` extensions      |
| `MODEL_PATH`            | —              | Path to the `.gguf` model                        |
| `MEMORY_VECTOR_WEIGHT`  | `0.5`          | Hybrid-search weight (semantic)                  |
| `MEMORY_TEXT_WEIGHT`    | `0.5`          | Hybrid-search weight (FTS5)                      |
| `MEMORY_MAX_RESULTS`    | `10`           | Max hits returned by the extension               |
| `MEMORY_MIN_SCORE`      | `0.6`          | Minimum ranking score                            |
| `MEMORY_MAX_TOKENS`     | `256`          | Chunk size at ingest time                        |
| `MEMORY_OVERLAP_TOKENS` | `50`           | Chunk overlap at ingest time                     |

Defaults for the weights are balanced for Polish (0.5/0.5 instead of
`sqlite-memory`'s default 0.6/0.4). The 256/50 chunk defaults are lower than
`sqlite-memory`'s 512/100 because 512/100 hangs the chunker in an infinite
loop inside llama.cpp on some Polish markdown files — uninterruptible from
Python, so `ingest.py` silently wedges. Raise these only if you know your
corpus doesn't trigger the bug.

## Development

```bash
uv sync --group dev
uv run ruff check . && uv run ruff format --check .
uv run pytest -q
```

CI (GitHub Actions) runs the same commands on every push and PR.

## Known limitations

- **Not incremental.** Every `ingest.py` run wipes `data/memory.db` (and its
  `-wal` / `-shm` / `-journal` siblings) and rebuilds the index from scratch.
- **Polish retrieval tuning is empirical.** The model expects
  `query:` / `passage:` prefixes that the current ingest does not add. If
  Polish rankings look weak, switch to manual chunking via `memory_add_text`
  with a `passage:` prefix and prepend `query:` in `server.py`.
- **Extension version must match the DB.** After upgrading `sqlite-memory`
  on either side, re-ingest or schema drift can make the DB unreadable.

## Troubleshooting

- **MCP tool doesn't appear in Claude Desktop.** The `command` path in
  `claude_desktop_config.json` must be absolute — Claude Desktop does not
  inherit your shell `PATH`. Logs: `~/Library/Logs/Claude/` (macOS),
  `%APPDATA%\Claude\logs\` (Windows).
- **`load_extension is not allowed`.** Your Python was built without
  extension loading. On macOS use Homebrew Python (`brew install python@3.14`);
  the system Python lacks this.
- **`memory.dylib is not a valid SQLite extension`.** Re-download:
  `uv run python -m setup.download_extensions --force`.
