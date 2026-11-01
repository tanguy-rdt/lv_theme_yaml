"""Loads every input file and runs the checks that span several files."""

from __future__ import annotations

from pathlib import Path

from ..diagnostics import Diagnostics, Source
from ..model import Color, Font, Project, Theme
from .colors import load_colors
from .fonts import load_fonts
from .theme import load_theme


def _check_color_font_clashes(colors: list[Color], fonts: list[Font],
                              colors_file: Path, fonts_file: Path,
                              diagnostics: Diagnostics) -> None:
    """A prop value is resolved by name, so a name cannot be both."""
    font_names = {font.name for font in fonts}
    for color in colors:
        if color.name in font_names:
            diagnostics.error(colors_file, color.name,
                              f"'{color.name}' is both a color and a font (see {fonts_file})")


def _check_unique_theme_names(themes: list[Theme], diagnostics: Diagnostics) -> None:
    seen: dict[str, Path] = {}
    for theme in themes:
        if theme.name in seen:
            diagnostics.error(theme.file, "name",
                              f"theme '{theme.name}' is already defined in {seen[theme.name]}")
        seen[theme.name] = theme.file


def _check_same_images(themes: list[Theme], diagnostics: Diagnostics) -> None:
    """Theme::image(Icon::X) must work whatever the active theme is."""
    if not themes:
        return
    all_keys = set().union(*(theme.images.keys() for theme in themes))
    for theme in themes:
        missing = sorted(all_keys - theme.images.keys())
        if missing:
            diagnostics.error(theme.file, "images",
                              f"missing image keys {missing} (every theme must define the same images)")


def load_project(colors_file: Path, fonts_file: Path, theme_files: list[Path],
                 diagnostics: Diagnostics) -> Project:
    """Always returns a project; check `diagnostics` before using it."""
    colors = load_colors(Source(colors_file, diagnostics))
    fonts = load_fonts(Source(fonts_file, diagnostics))
    themes = [theme for file in theme_files if (theme := load_theme(Source(file, diagnostics)))]

    _check_color_font_clashes(colors, fonts, colors_file, fonts_file, diagnostics)
    _check_unique_theme_names(themes, diagnostics)
    _check_same_images(themes, diagnostics)

    return Project(colors_file, fonts_file, tuple(colors), tuple(fonts), tuple(themes))
