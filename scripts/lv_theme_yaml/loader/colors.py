"""The global colors.yaml file."""

from __future__ import annotations

import re

from ..diagnostics import Source
from ..model import Color
from .identifiers import check_identifier
from .yaml_file import load_yaml

HEX_RE = re.compile(r"^(?:#|0[xX])([0-9a-fA-F]{6})$")
RGB_RE = re.compile(r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$")


def parse_color(source: Source, key: str, value: object) -> tuple[int, int, int] | None:
    """Accepts #RRGGBB, 0xRRGGBB and rgb(r, g, b)."""
    if not isinstance(value, str):
        source.error(key, "color must be a string")
        return None

    text = value.strip()
    if match := HEX_RE.match(text):
        number = int(match.group(1), 16)
        return (number >> 16) & 0xFF, (number >> 8) & 0xFF, number & 0xFF

    if match := RGB_RE.match(text):
        r, g, b = (int(component) for component in match.groups())
        if max(r, g, b) > 255:
            source.error(key, f"color component out of range 0-255 in '{value}'")
            return None
        return r, g, b

    source.error(key, f"invalid color '{value}' (expected #RRGGBB, 0xRRGGBB or rgb(r, g, b))")
    return None


def load_colors(source: Source) -> list[Color]:
    data = load_yaml(source)
    if data is None:
        return []
    if not isinstance(data, dict) or not data:
        source.error("", "expected a non-empty mapping name: color")
        return []

    colors = []
    for name, value in data.items():
        if not check_identifier(source, name, name, "color name", cpp_name=True, enum_member=True):
            continue
        if (rgb := parse_color(source, name, value)) is not None:
            colors.append(Color(name, rgb))
    return colors
