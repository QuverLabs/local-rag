"""Platform detection shared by download scripts and runtime guards."""

from __future__ import annotations

import platform


SUPPORTED = {
    ("macos", "arm64"),
    ("windows", "x86_64"),
    ("linux", "x86_64"),
}


def detect() -> tuple[str, str]:
    """Return (os_tag, arch_tag) normalized for sqlite-memory/sqlite-vector release assets.

    Raises RuntimeError for unsupported platforms with a clear message.
    """
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        return ("macos", "arm64")

    if system == "Windows":
        if machine in ("amd64", "x86_64"):
            return ("windows", "x86_64")
        raise RuntimeError(f"Unsupported Windows architecture: {machine!r}. Expected AMD64/x86_64.")

    if system == "Linux":
        if machine in ("x86_64", "amd64"):
            return ("linux", "x86_64")
        raise RuntimeError(f"Unsupported Linux architecture: {machine!r}. Expected x86_64.")

    raise RuntimeError(
        f"Unsupported platform: system={system!r}, machine={machine!r}. "
        f"Supported: {sorted(SUPPORTED)}."
    )


def extension_suffix() -> str:
    """Return the dynamic-library suffix for the current OS (e.g. '.dylib', '.dll', '.so')."""
    os_tag, _ = detect()
    return {"macos": ".dylib", "windows": ".dll", "linux": ".so"}[os_tag]
