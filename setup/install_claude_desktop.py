"""Register the MCP server in Claude Desktop's config."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from setup._db import load_env, server_name
from setup._platform import detect


def _config_path(os_tag: str) -> Path:
    if os_tag == "macos":
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if os_tag == "windows":
        return Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
    raise SystemExit(f"Claude Desktop config path unknown for os={os_tag!r}")


def _find_uv() -> Path:
    uv = shutil.which("uv")
    if not uv:
        raise SystemExit("Could not find 'uv' on PATH. Install it (brew install uv) or pass --uv <path>.")
    return Path(uv).resolve()


def main() -> int:
    """Register (or update) this repo's MCP server entry in Claude Desktop's config JSON."""
    parser = argparse.ArgumentParser(description="Wire the MCP server into Claude Desktop's config.")
    parser.add_argument(
        "--uv",
        type=Path,
        default=None,
        help="Absolute path to the uv binary (default: auto-detect via PATH).",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Absolute path to the project directory (default: this repo).",
    )
    parser.add_argument(
        "--name",
        default=None,
        help=(
            "MCP server name to register in Claude Desktop. Overrides "
            "MCP_SERVER_NAME from the project's .env."
        ),
    )
    args = parser.parse_args()

    os_tag, _ = detect()
    config_path = _config_path(os_tag)
    project_dir = args.project_dir.expanduser().resolve()
    uv_path = args.uv.expanduser().resolve() if args.uv else _find_uv()

    if args.uv and not uv_path.is_file():
        raise SystemExit(f"uv binary not found at {uv_path}")
    if not (project_dir / "server.py").is_file():
        raise SystemExit(f"server.py not found under {project_dir}")

    load_env(project_dir)
    name = args.name or server_name()

    if config_path.exists():
        raw = config_path.read_bytes()
        try:
            config = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise SystemExit(f"Existing config at {config_path} is not valid JSON: {e}") from e
        backup = config_path.with_suffix(f"{config_path.suffix}.bak")
        backup.write_bytes(raw)
        print(f"Backed up existing config -> {backup}", file=sys.stderr)
    else:
        config = {}
        config_path.parent.mkdir(parents=True, exist_ok=True)

    new_entry = {
        "command": str(uv_path),
        "args": ["run", "--directory", str(project_dir), "server.py"],
    }
    servers = config.setdefault("mcpServers", {})
    existing = servers.get(name)
    if existing and existing != new_entry:
        print(
            f"Warning: replacing different {name!r} entry (was {existing})",
            file=sys.stderr,
        )
    servers[name] = new_entry

    tmp = config_path.with_suffix(f"{config_path.suffix}.tmp")
    tmp.write_text(f"{json.dumps(config, indent=2)}\n", encoding="utf-8")
    os.replace(tmp, config_path)
    print(f"Wrote {name!r} MCP server entry to {config_path}")
    print("Restart Claude Desktop to pick up the change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
