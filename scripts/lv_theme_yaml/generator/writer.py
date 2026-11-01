"""Writing the output without touching files whose content did not change.

Unchanged files keep their timestamp, so the build system does not recompile them.
"""

from __future__ import annotations

from pathlib import Path


def write_if_changed(path: Path, content: str) -> bool:
    data = content.encode("utf-8")
    if path.is_file() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


def write_files(files: dict[Path, str]) -> int:
    """Returns the number of files actually written."""
    return sum(write_if_changed(path, content) for path, content in files.items())
