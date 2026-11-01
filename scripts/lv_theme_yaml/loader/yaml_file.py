"""Strict YAML reading: every scalar stays a string and duplicate keys are reported."""

from __future__ import annotations

from typing import Any

import yaml

from ..diagnostics import Source


class _StrictLoader(yaml.BaseLoader):
    """BaseLoader keeps every scalar as a string; this adds duplicate key detection."""

    def __init__(self, stream: str) -> None:
        super().__init__(stream)
        self.duplicates: list[tuple[str, int]] = []

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        seen: set = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                self.duplicates.append((key, key_node.start_mark.line + 1))
            seen.add(key)
        return super().construct_mapping(node, deep)


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _StrictLoader.construct_mapping
)


def load_yaml(source: Source) -> Any:
    """Return the parsed document, or None when the file cannot be read."""
    if not source.path.is_file():
        source.error("", "file not found")
        return None

    try:
        loader = _StrictLoader(source.path.read_text(encoding="utf-8"))
        try:
            data = loader.get_single_data()
        finally:
            loader.dispose()
    except yaml.YAMLError as exc:
        source.error("", f"invalid YAML: {exc}")
        return None

    for key, line in loader.duplicates:
        source.error(f"line {line}", f"duplicate key '{key}'")
    return data
