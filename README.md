# local-rag

Local RAG over a folder of markdown notes. Indexing is done on macOS with
[`sqlite-memory`](https://github.com/sqliteai/sqlite-memory) + local embeddings
from `multilingual-e5-large-instruct` (GGUF, 1024 dim, strong Polish support).
A FastMCP server exposes a `search_memory` tool to Claude Desktop, so the model
can pull relevant context from your notes directly in a conversation.

Supported platforms: macOS arm64 (Apple Silicon) and Windows x64.

## Setup on macOS (Apple Silicon)

```bash
brew install python@3.12 uv
cd /Users/<you>/local-rag
uv sync
uv run python -m setup.download_extensions   # ~2 MB, produces data/extensions/{vector,memory}.dylib
uv run python -m setup.download_model        # ~603 MB GGUF, several minutes

cp .env.example .env
# Edit .env: set NOTES_DIR to the folder containing your .md files

uv run python ingest.py                      # builds data/memory.db
```

Optional: inspect the MCP server end-to-end before wiring Claude Desktop:

```bash
npx @modelcontextprotocol/inspector uv run --directory /Users/<you>/local-rag server.py
```

Then wire the server into Claude Desktop:

```bash
uv run python -m setup.install_claude_desktop
```

The script auto-detects your `uv` binary and this repo's path, reads
`MCP_SERVER_NAME` from `.env` (default `local-rag`), and merges an entry into
`~/Library/Application Support/Claude/claude_desktop_config.json` (backing up
any existing file to `.bak`; other MCP servers are preserved). Restart Claude
Desktop to pick up the change.

To run multiple deployments side by side, clone the repo into a separate folder
and set a different `MCP_SERVER_NAME` in its `.env` (e.g. `work-notes`).

Flags: `--uv <path>` to override the binary, `--project-dir <path>` for a
different checkout, `--name <id>` to override `MCP_SERVER_NAME` for this run.

If you prefer manual setup, copy `claude_desktop_config.example.json` into the
config path above and replace the `/opt/homebrew/bin/uv` and project path
placeholders.

## Deploy to Windows (server-only)

Ship a single, self-contained ZIP from the Mac. The user on Windows unzips,
double-clicks `install.bat`, and pastes one config snippet. No system `uv`
install, no admin rights, no external downloads at install time.

### Build the bundle (on macOS, after a successful ingest)

```bash
uv run python -m scripts.make_bundle
```

This writes `dist/rag-bundle-YYYY-MM-DD-HHMM.zip` (~1 GB) containing:

- `source/` — code + `uv.lock` (so Windows reproduces the exact dep set)
- `data/memory.db` — your indexed notes
- `data/models/*.gguf` — the embedding model
- `data/extensions/{vector,memory}.dll` — freshly downloaded for Windows x64
- `bin/uv.exe` — portable uv for Windows
- `install.ps1` + `install.bat` — one-click installer
- `README-windows.md` + `manifest.json` (SHA256 of every file)

Flags:
- `--force` — overwrite an existing bundle zip with the same timestamp name.
- `--uv-version 0.11.7` — pin a specific portable uv version.
- `--name my-bundle` — override the folder/zip name.

### Install on Windows

1. Copy the ZIP to the Windows machine and unzip it anywhere
   (e.g. `C:\Users\<you>\rag-bundle\`). Keep the folder — the installer
   writes paths that point inside it.
2. Double-click `install.bat`. It will:
   - Run `uv sync` inside `source\` using the bundled `bin\uv.exe`, creating
     a local `.venv` with FastMCP + deps.
   - Write `source\.env` with bundle-absolute paths.
   - Merge a `local-rag` entry into `%APPDATA%\Claude\claude_desktop_config.json`,
     creating the file if missing and backing up any existing one to `.bak`
     (other MCP servers in the file are preserved).
3. Restart Claude Desktop. The `search_memory` tool should now appear in
   conversations.

### Re-indexing

The bundled `memory.db` is a frozen snapshot. To refresh the notes: re-run
`ingest.py` on the Mac, rebuild the bundle, and ship a new ZIP. If you only
want to swap the DB (same model, same `sqlite-memory` version), copy the new
`data/memory.db` over the old one on Windows — no reinstall needed.

### Moving the bundle folder

Paths in `source/.env` are absolute. If the user moves the bundle folder on
Windows, re-run `install.bat` so it rewrites `.env` and the config snippet
with the new location.

## How it works

`ingest.py` opens a SQLite database, loads the `sqlite-vector` then
`sqlite-memory` extensions, sets the local embedding model, and calls
`memory_add_directory(NOTES_DIR, context)`. The extension walks the directory,
chunks markdown using its built-in structural chunker (512-token chunks with
100-token overlap), embeds each chunk with the local GGUF model via llama.cpp,
and stores both the vector and the raw text for FTS5.

`server.py` is a FastMCP stdio server that re-opens the same database, loads
the extensions, re-applies the local model (it's per-connection state), and
exposes one tool:

```python
search_memory(query: str, limit: int = 5) -> list[dict]
```

Each result has `path`, `snippet`, and `ranking` (hybrid vector + text score).

## Known limitations

- **Re-indexing is not incremental.** To re-ingest, delete `data/memory.db`
  and run `ingest.py` again.
- **Polish search quality — empirical tuning may be needed.** The model
  (`multilingual-e5-large-instruct`) is trained with `query:` / `passage:`
  prefixes that the current ingest does not add manually. If rankings look
  weak on Polish queries, switch to manual chunking + `memory_add_text` with
  a `passage:` prefix, and prepend `query:` to the search string in
  `server.py`.
- **Extension version must match the database.** If you upgrade
  `sqlite-memory` on the Mac, upgrade on Windows too or re-ingest — schema
  drift between versions can make the DB unreadable.

## Troubleshooting

- `MCP server not appearing in Claude Desktop`: the `command` path in
  `claude_desktop_config.json` must be absolute. Claude Desktop does not
  inherit your shell `PATH`. Check the Claude Desktop logs under
  `~/Library/Logs/Claude/` on macOS.
- `load_extension is not allowed`: your Python was built without extension
  loading support. On macOS, install Python from Homebrew
  (`brew install python@3.12`) — the system Python ships without this.
- `memory.dylib is not a valid SQLite extension`: run
  `uv run python -m setup.download_extensions --force` to re-download a clean copy.
