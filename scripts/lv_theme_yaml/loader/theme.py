"""One theme file: name, images and styles."""

from __future__ import annotations

from ..diagnostics import Source
from ..model import Selector, Style, Theme
from ..naming import pascal
from .identifiers import check_identifier
from .images import parse_images
from .props import parse_props
from .selectors import parse_selector
from .yaml_file import load_yaml

THEME_KEYS = {"name", "images", "styles"}
GLOBAL_ONLY_KEYS = ("colors", "fonts")
STYLE_KEYS = {"selectors", "props"}


def _check_top_level(source: Source, data: dict) -> None:
    for key in data:
        if key in GLOBAL_ONLY_KEYS:
            source.error(key, f"'{key}' is global only, define it in the global {key}.yaml")
        elif key not in THEME_KEYS:
            source.error(key, "unknown key (expected name, images, styles)")


def _parse_name(source: Source, data: dict) -> str | None:
    name = data.get("name")
    if name is None:
        source.error("name", "missing")
        return None
    if not check_identifier(source, "name", name, "theme name"):
        return None
    return name


def _parse_selectors(source: Source, key: str, data: object) -> list[Selector]:
    if data is None:
        source.error(key, "missing")
        return []
    if not isinstance(data, list) or not data:
        source.error(key, "expected a non-empty list")
        return []

    selectors = []
    for index, text in enumerate(data):
        if selector := parse_selector(source, f"{key}[{index}]", text):
            selectors.append(selector)
    return selectors


def _parse_style(source: Source, name: object, body: object) -> Style | None:
    key = f"styles.{name}"
    if not check_identifier(source, key, name, "style name"):
        return None
    if not isinstance(body, dict):
        source.error(key, "expected a mapping with selectors and props")
        return None
    for unknown in set(body) - STYLE_KEYS:
        source.error(f"{key}.{unknown}", "unknown key (expected selectors, props)")

    selectors = _parse_selectors(source, f"{key}.selectors", body.get("selectors"))
    props = parse_props(source, f"{key}.props", body.get("props"))
    return Style(name, tuple(selectors), tuple(props))


def _check_cpp_name_clashes(source: Source, styles: list[Style]) -> None:
    """Two style names can produce the same C++ name, e.g. 'a_b' and 'ab_'."""
    seen: dict[str, str] = {}
    for style in styles:
        ident = pascal(style.name)
        if ident in seen:
            source.error(f"styles.{style.name}", f"generates the same C++ name as 'styles.{seen[ident]}'")
        seen[ident] = style.name


def _parse_styles(source: Source, data: object) -> list[Style]:
    if data is None:
        source.error("styles", "missing")
        return []
    if not isinstance(data, dict) or not data:
        source.error("styles", "expected a non-empty mapping")
        return []

    styles = [style for name, body in data.items() if (style := _parse_style(source, name, body))]
    _check_cpp_name_clashes(source, styles)
    return styles


def load_theme(source: Source) -> Theme | None:
    data = load_yaml(source)
    if data is None:
        return None
    if not isinstance(data, dict):
        source.error("", "expected a mapping with name, images, styles")
        return None

    _check_top_level(source, data)
    name = _parse_name(source, data)
    images = parse_images(source, data.get("images"))
    styles = _parse_styles(source, data.get("styles"))

    if name is None:
        return None
    return Theme(source.path, name, images, tuple(styles))
