"""Shared HTTP helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from tqdm import tqdm


def stream_download(
    url: str,
    dest: Path,
    *,
    timeout: float = 60.0,
    chunk_size: int = 65536,
) -> None:
    """Stream-download url to dest with a tqdm progress bar.

    Writes to dest.with_suffix(dest.suffix + '.part') then os.replace() onto
    dest, so an interrupted download never leaves a truncated file in place.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    with httpx.stream("GET", url, follow_redirects=True, timeout=timeout) as response:
        response.raise_for_status()
        total = int(response.headers.get("Content-Length", 0))
        with open(part, "wb") as fp, tqdm(
            total=total,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=dest.name,
            file=sys.stderr,
        ) as bar:
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                fp.write(chunk)
                bar.update(len(chunk))
    os.replace(part, dest)
