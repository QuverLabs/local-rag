"""Shared HTTP helpers."""

from __future__ import annotations

import os
import sys
from hashlib import sha256
from pathlib import Path

import httpx
from tqdm import tqdm


def stream_download(
    url: str,
    dest: Path,
    *,
    timeout: float = 60.0,
    chunk_size: int = 65536,
    expected_sha256: str | None = None,
) -> None:
    """Stream-download url to dest with a tqdm progress bar.

    Writes to dest.with_suffix(dest.suffix + '.part') then os.replace() onto
    dest, so an interrupted download never leaves a truncated file in place.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(f"{dest.suffix}.part")
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=timeout) as response:
            response.raise_for_status()
            raw_total = response.headers.get("Content-Length")
            total = int(raw_total) if raw_total else None  # None → indefinite spinner
            with (
                open(part, "wb") as fp,
                tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=dest.name,
                    file=sys.stderr,
                ) as progress,
            ):
                for chunk in response.iter_bytes(chunk_size=chunk_size):
                    fp.write(chunk)
                    progress.update(len(chunk))
        if expected_sha256 is not None:
            digest = sha256()
            with part.open("rb") as fp:
                while chunk := fp.read(1024 * 1024):
                    digest.update(chunk)
            actual = digest.hexdigest()
            if actual != expected_sha256:
                raise RuntimeError(
                    f"SHA256 mismatch for {dest.name}: expected {expected_sha256}, got {actual}"
                )
        os.replace(part, dest)
    except Exception:
        part.unlink(missing_ok=True)
        raise
