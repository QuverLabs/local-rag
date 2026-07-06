r"""Build a self-contained Windows distribution bundle (ZIP) of the RAG project.

Run on macOS after a successful ingest. The resulting ZIP contains:

    rag-bundle-YYYY-MM-DD-HHMM/
      source/                           # server.py, ingest.py, setup/, pyproject.toml, uv.lock, ...
      data/
        memory.db                       # copied from <project>/data/memory.db
        models/*.gguf                   # copied from <project>/data/models/
        extensions/{vector,memory}.dll  # downloaded fresh for Windows
      bin/
        uv.exe                          # portable uv for Windows (no install needed)
      install.ps1
      install.bat
      README-windows.md
      manifest.json                     # SHA256 of every file

The user runs `install.bat` on Windows — it unpacks deps into a local `.venv`
via the bundled uv.exe, writes `.env` with bundle-absolute paths, and
auto-registers the MCP server in `%APPDATA%\Claude\claude_desktop_config.json`.

No admin rights, no external downloads, no PATH mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from setup._archive import extract_from_tar_gz
from setup._http import stream_download
from setup.download_extensions import (
    MEMORY_ASSETS,
    MEMORY_URL_TEMPLATE,
    MEMORY_VERSION,
    VECTOR_ASSETS,
    VECTOR_URL_TEMPLATE,
    VECTOR_VERSION,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
_SCRIPTS_DIR = Path(__file__).resolve().parent

UV_ASSET = "uv-x86_64-pc-windows-msvc.zip"
UV_URL_TEMPLATE = "https://github.com/astral-sh/uv/releases/download/{version}/{asset}"

# Files/dirs copied verbatim from <project>/ into bundle/source/.
SOURCE_FILES = [
    "server.py",
    "ingest.py",
    "pyproject.toml",
    "uv.lock",
    ".env.example",
    "claude_desktop_config.example.json",
    "README.md",
]
SOURCE_DIRS = ["setup"]


def _read_uv_version_from_tool_versions() -> str:
    for line in (PROJECT_ROOT / ".tool-versions").read_text().splitlines():
        parts = line.split("#", 1)[0].split()
        if len(parts) == 2 and parts[0] == "uv":
            return parts[1]
    raise RuntimeError(".tool-versions is missing a 'uv <version>' line")


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_uv_exe(archive: Path, out_path: Path) -> None:
    """Pull uv.exe out of the Astral Windows zip."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        candidates = [n for n in zf.namelist() if n.lower().endswith("uv.exe")]
        if not candidates:
            raise RuntimeError(f"uv.exe not found in {archive.name}. Contents: {zf.namelist()}")
        # Prefer the shortest-path entry (usually top-level uv.exe, not uvx.exe or a nested copy).
        member = min(candidates, key=len)
        with zf.open(member) as src, open(out_path, "wb") as dst:
            shutil.copyfileobj(src, dst)


# Text suffixes get DEFLATE compression; the rest stays STORED (already compressed).
_TEXT_SUFFIXES = {".py", ".toml", ".lock", ".md", ".json", ".ps1", ".bat", ".example", ".txt", ".cfg", ".ini"}


def _compression_for(name: str) -> int:
    if Path(name).suffix.lower() in _TEXT_SUFFIXES:
        return zipfile.ZIP_DEFLATED
    return zipfile.ZIP_STORED


# ---------------------------------------------------------------------------
# Bundle assembly.
# ---------------------------------------------------------------------------


def _gather_source_tree(staging: Path) -> list[Path]:
    """Copy source files/dirs into staging/source/ and return the list of files created."""
    src_out = staging / "source"
    src_out.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []

    for name in SOURCE_FILES:
        src = PROJECT_ROOT / name
        if not src.is_file():
            raise SystemExit(f"Missing source file: {src}")
        dst = src_out / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst)

    for dirname in SOURCE_DIRS:
        src = PROJECT_ROOT / dirname
        if not src.is_dir():
            raise SystemExit(f"Missing source dir: {src}")
        for child in src.rglob("*"):
            if child.is_dir():
                continue
            if "__pycache__" in child.parts or child.suffix in {".pyc", ".pyo"}:
                continue
            rel = child.relative_to(PROJECT_ROOT)
            dst = src_out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, dst)
            copied.append(dst)

    return copied


def _copy_data_artifacts(staging: Path) -> list[Path]:
    """Copy memory.db and the GGUF model into staging/data/."""
    copied: list[Path] = []

    memory_db = PROJECT_ROOT / "data" / "memory.db"
    if not memory_db.is_file():
        raise SystemExit(
            "data/memory.db not found. Run ingest.py on the Mac first: "
            "NOTES_DIR=<your-notes> uv run python ingest.py"
        )
    dst = staging / "data" / "memory.db"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(memory_db, dst)
    copied.append(dst)

    models_src = PROJECT_ROOT / "data" / "models"
    ggufs = sorted(models_src.glob("*.gguf"))
    if not ggufs:
        raise SystemExit(f"No .gguf model in {models_src}. Run setup/download_model.py first.")
    for gguf in ggufs:
        dst = staging / "data" / "models" / gguf.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gguf, dst)
        copied.append(dst)

    return copied


_WINDOWS_KEY = ("windows", "x86_64")


def _download_windows_extension(
    staging: Path, url_template: str, version: str, asset: str, out_name: str
) -> Path:
    """Fetch one Windows extension DLL from GitHub Releases into staging/data/extensions/."""
    ext_dir = staging / "data" / "extensions"
    ext_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_str:
        archive = Path(tmp_str) / asset
        stream_download(url_template.format(version=version, asset=asset), archive, timeout=120.0)
        out = ext_dir / out_name
        extract_from_tar_gz(archive, ".dll", out)
    return out


def _download_portable_uv(staging: Path, uv_version: str) -> Path:
    """Fetch uv.exe for Windows into staging/bin/uv.exe."""
    bin_dir = staging / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        url = UV_URL_TEMPLATE.format(version=uv_version, asset=UV_ASSET)
        archive = tmp / UV_ASSET
        stream_download(url, archive, timeout=120.0)
        uv_exe = bin_dir / "uv.exe"
        _extract_uv_exe(archive, uv_exe)
    return uv_exe


def _write_installers_and_readme(staging: Path) -> list[Path]:
    files: list[Path] = []

    ps1_src = (_SCRIPTS_DIR / "install.ps1").read_text(encoding="utf-8")
    ps1 = staging / "install.ps1"
    ps1.write_text(ps1_src, encoding="utf-8")
    files.append(ps1)

    # Write install.bat with CRLF line endings for Windows friendliness.
    bat_src = (_SCRIPTS_DIR / "install.bat").read_text(encoding="utf-8")
    bat = staging / "install.bat"
    bat.write_bytes(bat_src.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    files.append(bat)

    readme_src = (_SCRIPTS_DIR / "README-windows.md").read_text(encoding="utf-8")
    readme = staging / "README-windows.md"
    readme.write_text(readme_src, encoding="utf-8")
    files.append(readme)

    return files


def _build_manifest(staging: Path, bundle_name: str, uv_version: str) -> Path:
    entries = []
    for path in sorted(staging.rglob("*")):
        if path.is_dir():
            continue
        if path.name == "manifest.json":
            continue
        rel = path.relative_to(staging).as_posix()
        entries.append(
            {
                "path": rel,
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    manifest = {
        "bundle": bundle_name,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "uv_version": uv_version,
        "sqlite_vector_version": VECTOR_VERSION,
        "sqlite_memory_version": MEMORY_VERSION,
        "files": entries,
    }
    out = staging / "manifest.json"
    out.write_text(f"{json.dumps(manifest, indent=2)}\n", encoding="utf-8")
    return out


def _zip_bundle(staging: Path, bundle_name: str, out_zip: Path) -> None:
    """Write staging/ into out_zip, nested under bundle_name/ as the top-level folder."""
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    # allowZip64=True — the GGUF alone is 600 MB, total bundle easily fits in standard ZIP32
    # but larger datasets could push over 4 GB, so keep it safe.
    with zipfile.ZipFile(out_zip, "w", allowZip64=True) as zf:
        for path in sorted(staging.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(staging).as_posix()
            arcname = f"{bundle_name}/{rel}"
            compression = _compression_for(rel)
            size_mb = path.stat().st_size / (1024 * 1024)
            print(
                f"  add {arcname} ({size_mb:.1f} MB, "
                f"{'DEFLATE' if compression == zipfile.ZIP_DEFLATED else 'STORED'})",
                file=sys.stderr,
            )
            zf.write(path, arcname=arcname, compress_type=compression)


def main() -> int:
    """Assemble a timestamped Windows distribution ZIP from the current project state."""
    parser = argparse.ArgumentParser(description="Build a Windows distribution bundle")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DIST_DIR,
        help="Where to write the .zip (default: <project>/dist)",
    )
    parser.add_argument(
        "--uv-version",
        default=None,
        help="Portable uv version to bundle (default: read from .tool-versions)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing bundle zip with the same timestamped name",
    )
    args = parser.parse_args()

    uv_version = args.uv_version or _read_uv_version_from_tool_versions()

    bundle_name = f"rag-bundle-{datetime.now().strftime('%Y-%m-%d-%H%M')}"
    out_zip = args.output_dir / f"{bundle_name}.zip"

    if out_zip.exists() and not args.force:
        raise SystemExit(f"{out_zip} already exists. Re-run with --force to overwrite.")

    print(f"Building bundle: {bundle_name}", file=sys.stderr)
    print(f"Output:         {out_zip}", file=sys.stderr)
    print(f"uv version:     {uv_version}", file=sys.stderr)
    print("", file=sys.stderr)

    with tempfile.TemporaryDirectory(prefix="rag-bundle-") as staging_str:
        staging = Path(staging_str)

        print("Step 1/5: copying source tree...", file=sys.stderr)
        _gather_source_tree(staging)

        print("Step 2/5: copying data artifacts (memory.db + GGUF)...", file=sys.stderr)
        _copy_data_artifacts(staging)

        print(
            "Step 3/5: downloading Windows binaries (vector.dll, memory.dll, uv.exe in parallel)...",
            file=sys.stderr,
        )
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(
                    _download_windows_extension,
                    staging,
                    VECTOR_URL_TEMPLATE,
                    VECTOR_VERSION,
                    VECTOR_ASSETS[_WINDOWS_KEY],
                    "vector.dll",
                ),
                pool.submit(
                    _download_windows_extension,
                    staging,
                    MEMORY_URL_TEMPLATE,
                    MEMORY_VERSION,
                    MEMORY_ASSETS[_WINDOWS_KEY],
                    "memory.dll",
                ),
                pool.submit(_download_portable_uv, staging, uv_version),
            ]
            for future in futures:
                future.result()

        print("Step 4/5: writing installers and README...", file=sys.stderr)
        _write_installers_and_readme(staging)

        print("Step 5/5: building manifest + zipping...", file=sys.stderr)
        _build_manifest(staging, bundle_name, uv_version)

        _zip_bundle(staging, bundle_name, out_zip)

    size_mb = out_zip.stat().st_size / (1024 * 1024)
    print("", file=sys.stderr)
    print(f"Bundle ready: {out_zip} ({size_mb:.1f} MB)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
