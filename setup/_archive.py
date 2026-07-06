"""Shared archive-extraction helpers used by download_extensions and make_bundle."""

from __future__ import annotations

import shutil
import tarfile
from pathlib import Path


def extract_from_tar_gz(archive: Path, suffix: str, out_path: Path) -> None:
    """Extract the shortest-path *suffix member from a tar.gz directly into out_path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        candidates = [m for m in tar.getmembers() if m.isfile() and m.name.lower().endswith(suffix)]
        if not candidates:
            names = ", ".join(m.name for m in tar.getmembers())
            raise RuntimeError(f"No *{suffix} in {archive.name}. Contents: {names}")
        member = min(candidates, key=lambda m: len(m.name))
        with tar.extractfile(member) as src, open(out_path, "wb") as dst:
            if src is None:
                raise RuntimeError(f"Failed to read {member.name} from {archive.name}")
            shutil.copyfileobj(src, dst)
