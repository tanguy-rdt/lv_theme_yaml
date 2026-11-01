"""Collection of the errors found in the input files."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO


class Diagnostics:
    """Collects every error so that all of them are reported at once."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def error(self, file: Path, key: str, message: str) -> None:
        location = f"{file}: {key}" if key else f"{file}"
        self.messages.append(f"{location}: {message}")

    def __bool__(self) -> bool:
        return bool(self.messages)

    def report(self, stream: TextIO | None = None) -> None:
        stream = stream or sys.stderr
        for message in self.messages:
            print(f"error: {message}", file=stream)
        print(f"{len(self.messages)} error(s), nothing generated", file=stream)


class Source:
    """A YAML file being parsed, with a shortcut to report errors located in it."""

    def __init__(self, path: Path, diagnostics: Diagnostics) -> None:
        self.path = path
        self.diagnostics = diagnostics

    def error(self, key: str, message: str) -> None:
        self.diagnostics.error(self.path, key, message)
