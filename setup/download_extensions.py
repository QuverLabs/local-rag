"""Download and unpack sqlite-vector and sqlite-memory extensions for the current platform."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from setup._archive import extract_from_tar_gz
from setup._http import stream_download
from setup._platform import detect, extension_suffix

VECTOR_VERSION = "0.9.95"
MEMORY_VERSION = "0.9.0"

VECTOR_ASSETS = {
    ("macos", "arm64"): f"vector-macos-arm64-{VECTOR_VERSION}.tar.gz",
    ("windows", "x86_64"): f"vector-windows-x86_64-{VECTOR_VERSION}.tar.gz",
    ("linux", "x86_64"): f"vector-linux-x86_64-{VECTOR_VERSION}.tar.gz",
}

MEMORY_ASSETS = {
    ("macos", "arm64"): f"memory-macos-arm64-local-{MEMORY_VERSION}.tar.gz",
    ("windows", "x86_64"): f"memory-windows-x86_64-local-{MEMORY_VERSION}.tar.gz",
    ("linux", "x86_64"): f"memory-linux-x86_64-local-{MEMORY_VERSION}.tar.gz",
}

VECTOR_URL_TEMPLATE = "https://github.com/sqliteai/sqlite-vector/releases/download/{version}/{asset}"
MEMORY_URL_TEMPLATE = "https://github.com/sqliteai/sqlite-memory/releases/download/{version}/{asset}"

DEFAULT_EXTENSIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "extensions"


def _extract_extension(archive: Path, target_dir: Path, suffix: str, expected_stem: str) -> Path:
    """Extract the first *suffix binary from a tar.gz, install it as expected_stem+suffix."""
    target_dir.mkdir(parents=True, exist_ok=True)
    final = target_dir / f"{expected_stem}{suffix}"
    extract_from_tar_gz(archive, suffix, final)
    # 0o755 is required: sqlite3.load_extension rejects non-executable files on macOS/Linux.
    os.chmod(final, 0o755)  # noqa: S103
    return final


def main() -> int:
    """Download and unpack sqlite-vector + sqlite-memory extensions for the current platform."""
    parser = argparse.ArgumentParser(description="Download sqlite-vector + sqlite-memory extensions")
    parser.add_argument(
        "--extensions-dir",
        type=Path,
        default=DEFAULT_EXTENSIONS_DIR,
        help="Target directory for extension binaries (default: <project>/data/extensions)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if extensions already exist",
    )
    args = parser.parse_args()

    os_tag, arch_tag = detect()
    suffix = extension_suffix()
    key = (os_tag, arch_tag)

    vector_final = args.extensions_dir / f"vector{suffix}"
    memory_final = args.extensions_dir / f"memory{suffix}"

    if not args.force and vector_final.exists() and memory_final.exists():
        print(f"Extensions already present in {args.extensions_dir}", file=sys.stderr)
        print(f"  vector: {vector_final}")
        print(f"  memory: {memory_final}")
        return 0

    args.extensions_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        vector_url = VECTOR_URL_TEMPLATE.format(version=VECTOR_VERSION, asset=VECTOR_ASSETS[key])
        vector_archive = tmp / VECTOR_ASSETS[key]
        print(f"Downloading {vector_url}", file=sys.stderr)
        stream_download(vector_url, vector_archive)
        vector_path = _extract_extension(vector_archive, args.extensions_dir, suffix, "vector")

        memory_url = MEMORY_URL_TEMPLATE.format(version=MEMORY_VERSION, asset=MEMORY_ASSETS[key])
        memory_archive = tmp / MEMORY_ASSETS[key]
        print(f"Downloading {memory_url}", file=sys.stderr)
        stream_download(memory_url, memory_archive)
        memory_path = _extract_extension(memory_archive, args.extensions_dir, suffix, "memory")

    print("Extensions installed:")
    print(f"  vector: {vector_path}")
    print(f"  memory: {memory_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
