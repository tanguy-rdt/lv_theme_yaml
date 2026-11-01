"""Validated description of a theme project, independent of YAML and of C++."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Color:
    name: str
    rgb: tuple[int, int, int]


@dataclass(frozen=True)
class Font:
    name: str
    lvgl_name: str          # without the lv_font_ prefix, e.g. montserrat_14


@dataclass(frozen=True)
class Image:
    key: str
    ltr: Path
    rtl: Path | None = None


@dataclass(frozen=True)
class Selector:
    target: str | None      # widget class, None for :screen
    parent: str | None = None
    ancestor: str | None = None
    states: tuple[str, ...] = ()
    part: str | None = None

    @property
    def is_screen(self) -> bool:
        return self.target is None


@dataclass(frozen=True)
class Prop:
    name: str               # LVGL property after shorthand expansion, e.g. pad_top
    value: str              # raw value from the YAML file


@dataclass(frozen=True)
class Style:
    name: str
    selectors: tuple[Selector, ...]
    props: tuple[Prop, ...]


@dataclass(frozen=True)
class Theme:
    file: Path
    name: str
    images: dict[str, Image]
    styles: tuple[Style, ...]

    @property
    def uses_screen_selector(self) -> bool:
        return any(sel.is_screen for style in self.styles for sel in style.selectors)


@dataclass(frozen=True)
class Project:
    colors_file: Path
    fonts_file: Path
    colors: tuple[Color, ...]
    fonts: tuple[Font, ...]
    themes: tuple[Theme, ...] = field(default_factory=tuple)

    @property
    def icon_keys(self) -> list[str]:
        """Image keys shared by every theme, in the order of the first theme."""
        return list(self.themes[0].images) if self.themes else []

    @property
    def color_names(self) -> set[str]:
        return {color.name for color in self.colors}

    @property
    def font_names(self) -> set[str]:
        return {font.name for font in self.fonts}

    @property
    def input_files(self) -> list[Path]:
        """Every file the generation depends on: YAML files and images."""
        files = [self.colors_file.resolve(), self.fonts_file.resolve()]
        files += [theme.file.resolve() for theme in self.themes]
        for theme in self.themes:
            for image in theme.images.values():
                files.append(image.ltr)
                if image.rtl:
                    files.append(image.rtl)
        return list(dict.fromkeys(files))
