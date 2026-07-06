# local-rag — Windows bundle

This bundle contains everything you need to run the RAG MCP server on Windows:

- `source/` — project code (`server.py`, `ingest.py`, `setup/`, `pyproject.toml`, `uv.lock`)
- `data/memory.db` — pre-built index of the notes (built on the Mac side)
- `data/models/*.gguf` — local embedding model (~603 MB)
- `data/extensions/vector.dll` + `memory.dll` — SQLite extensions for Windows x64
- `bin/uv.exe` — portable [uv](https://github.com/astral-sh/uv) (no system install)
- `install.ps1` + `install.bat` — one-click installer
- `manifest.json` — SHA256 of every bundled file

## Prerequisites

- Windows 10/11 x64.
- Claude Desktop installed.
- ~1.5 GB free disk space.
- No admin rights needed.

## Install (one-time)

1. Unzip this bundle anywhere you like (e.g. `C:\\Users\\<you>\\rag-bundle\\`). Keep the folder — the installer writes paths that point inside it.
2. Double-click `install.bat`.
3. The installer will:
   - Run `uv sync` inside `source\\` to create a local `.venv` with FastMCP + deps.
   - Write `source\\.env` with bundle-absolute paths.
   - Merge a `local-rag` entry into `%APPDATA%\\Claude\\claude_desktop_config.json`
     (creating the file if missing, backing up any existing one to `.bak`).
4. Restart Claude Desktop.

In a conversation, the `local_rag_search` tool should now appear among available tools.

## Re-indexing

The bundled `memory.db` is a frozen snapshot from the Mac. To refresh the
notes, re-run `ingest.py` on the Mac, rebuild a new bundle with
`scripts/make_bundle.py`, and replace the old `data/memory.db` + (only if the
model changed) `data/models/*.gguf` on Windows.

## Moving the bundle

Paths in `source/.env` are absolute. If you move the bundle folder, re-run
`install.bat` so it regenerates `.env` and the config snippet with the new
location.

## Troubleshooting

- **Claude Desktop doesn't show the tool.** Check `%APPDATA%\\Claude\\logs\\`
  for MCP server errors. The `command` in `claude_desktop_config.json` must be
  the absolute path to `bin\\uv.exe` inside the bundle.
- **`load_extension is not allowed`.** Shouldn't happen with the bundled uv
  (it ships a Python built with extension loading). If it does, please report.
- **`sqlite_memory.dll is not a valid SQLite extension`.** Bundle is corrupt.
  Check `manifest.json` against actual file hashes.
