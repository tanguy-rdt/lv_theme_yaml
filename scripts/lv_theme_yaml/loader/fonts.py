"""The global fonts.yaml file."""

from __future__ import annotations

import re

from ..diagnostics import Source
from ..model import Font
from .identifiers import check_identifier
from .yaml_file import load_yaml

LVGL_FONT_RE = re.compile(r"^[a-z0-9_]+$")


def load_fonts(source: Source) -> list[Font]:
    data = load_yaml(source)
    if data is None:
        return []
    if not isinstance(data, dict) or not data:
        source.error("", "expected a non-empty mapping name: lvgl_font")
        return []

    fonts = []
    for name, value in data.items():
        if not check_identifier(source, name, name, "font name", cpp_name=True, enum_member=True):
            continue
        if not isinstance(value, str) or not LVGL_FONT_RE.match(value):
            source.error(name, f"invalid LVGL font name '{value}' (e.g. montserrat_14)")
            continue
        fonts.append(Font(name, value))
    return fonts
