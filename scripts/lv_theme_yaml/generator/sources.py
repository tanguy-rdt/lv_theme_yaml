"""All the C++ files of a project, mapped to their place in the output layout."""

from __future__ import annotations

from pathlib import Path

from .. import naming
from ..model import Project
from . import shared_headers
from .layout import OutputLayout
from .theme import ThemeGenerator


def generate_sources(project: Project, layout: OutputLayout) -> dict[Path, str]:
    files = {
        layout.header(naming.IDS_HEADER): shared_headers.ids_header(project),
        layout.header(naming.COLORS_HEADER): shared_headers.colors_header(project),
        layout.header(naming.FONTS_HEADER): shared_headers.fonts_header(project),
    }
    for theme in project.themes:
        generator = ThemeGenerator(project, theme)
        files[layout.header(naming.theme_header(theme.name))] = generator.header()
        files[layout.source(naming.theme_source(theme.name))] = generator.source()
    return files
