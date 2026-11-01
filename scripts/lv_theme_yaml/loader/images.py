"""The images section of a theme file."""

from __future__ import annotations

from pathlib import Path

from ..diagnostics import Source
from ..model import Image
from .identifiers import check_identifier

IMAGE_KEYS = {"ltr", "rtl"}


def _resolve(source: Source, key: str, value: object) -> Path | None:
    """Image paths are relative to the theme file."""
    if not isinstance(value, str) or not value.strip():
        source.error(key, "expected a file path")
        return None
    path = (source.path.parent / value).resolve()
    if not path.is_file():
        source.error(key, f"image file not found: {path}")
        return None
    return path


def _parse_image(source: Source, key: str, name: str, value: object) -> Image | None:
    if not isinstance(value, dict):
        ltr = _resolve(source, key, value)
        return Image(name, ltr) if ltr else None

    unknown = set(value) - IMAGE_KEYS
    if unknown:
        source.error(key, f"unknown keys {sorted(unknown)} (expected ltr, rtl)")
    if "ltr" not in value:
        source.error(key, "missing 'ltr'")
        return None

    ltr = _resolve(source, f"{key}.ltr", value["ltr"])
    rtl = _resolve(source, f"{key}.rtl", value["rtl"]) if "rtl" in value else None
    if not ltr or ("rtl" in value and not rtl) or unknown:
        return None
    return Image(name, ltr, rtl)


def parse_images(source: Source, data: object) -> dict[str, Image]:
    if data is None:
        return {}
    if not isinstance(data, dict):
        source.error("images", "expected a mapping key: path")
        return {}

    images: dict[str, Image] = {}
    for name, value in data.items():
        key = f"images.{name}"
        if not check_identifier(source, key, name, "image key", enum_member=True):
            continue
        if image := _parse_image(source, key, name, value):
            images[name] = image
    return images
