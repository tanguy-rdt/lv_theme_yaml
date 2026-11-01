"""Style properties, with the expansion of the shorthands LVGL has no constant for."""

from __future__ import annotations

from ..diagnostics import Source
from ..model import Prop
from .identifiers import is_identifier

SHORTHANDS = {
    "pad_all": ("pad_top", "pad_bottom", "pad_left", "pad_right"),
    "pad_hor": ("pad_left", "pad_right"),
    "pad_ver": ("pad_top", "pad_bottom"),
    "pad_gap": ("pad_row", "pad_column"),
}


def expand(name: str) -> tuple[str, ...]:
    return SHORTHANDS.get(name, (name,))


def parse_props(source: Source, key: str, data: object) -> list[Prop]:
    if not isinstance(data, dict) or not data:
        source.error(key, "expected a non-empty mapping prop: value")
        return []

    props: list[Prop] = []
    set_by: dict[str, str] = {}
    for name, value in data.items():
        prop_key = f"{key}.{name}"
        if not is_identifier(name):
            source.error(prop_key, "invalid prop name")
            continue
        if not isinstance(value, str) or not value.strip():
            source.error(prop_key, "expected a scalar value")
            continue

        for real in expand(name):
            if real in set_by:
                source.error(prop_key, f"'{real}' is already set by '{set_by[real]}'")
                continue
            set_by[real] = name
            props.append(Prop(real, value.strip()))
    return props
