"""Download the multilingual-e5-large-instruct GGUF model from Hugging Face."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from setup._http import stream_download

MODEL_REPO = "Ralriki/multilingual-e5-large-instruct-GGUF"
MODEL_FILE = "multilingual-e5-large-instruct-q8_0.gguf"
MODEL_URL = f"https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILE}?download=true"
EXPECTED_MIN_BYTES = 500 * 1024 * 1024  # 500 MB sanity floor; actual ~603 MB

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "data" / "models"


def main() -> int:
    """Download the multilingual-e5-large-instruct GGUF embedding model from Hugging Face."""
    parser = argparse.ArgumentParser(description="Download the GGUF embedding model")
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=DEFAULT_MODEL_DIR,
        help="Target directory for the model file (default: <project>/data/models)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the model already exists",
    )
    args = parser.parse_args()

    dest = args.model_dir / MODEL_FILE

    if not args.force and dest.exists() and dest.stat().st_size >= EXPECTED_MIN_BYTES:
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"Model already present: {dest} ({size_mb:.1f} MB)", file=sys.stderr)
        return 0

    print(f"Downloading {MODEL_URL}", file=sys.stderr)
    stream_download(MODEL_URL, dest, timeout=300.0, chunk_size=1024 * 1024)

    size = dest.stat().st_size
    if size < EXPECTED_MIN_BYTES:
        raise RuntimeError(
            f"Downloaded file is too small ({size} bytes < {EXPECTED_MIN_BYTES}). "
            f"The download may have been truncated — try re-running with --force."
        )

    size_mb = size / (1024 * 1024)
    print(f"Model installed: {dest} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
