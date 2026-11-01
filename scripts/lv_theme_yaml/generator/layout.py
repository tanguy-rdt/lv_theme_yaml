"""Where each generated file goes.

<output>/
├── include/        headers: theme_ids.h, theme_colors.h, theme_fonts.h, <name>_theme.h
└── src/            theme sources: <name>_theme.cpp
    └── images/     converted images: icon_<key>_<theme>[_rtl].c
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OutputLayout:
    root: Path

    @property
    def include_dir(self) -> Path:
        return self.root / "include"

    @property
    def src_dir(self) -> Path:
        return self.root / "src"

    @property
    def images_dir(self) -> Path:
        return self.src_dir / "images"

    def header(self, name: str) -> Path:
        return self.include_dir / name

    def source(self, name: str) -> Path:
        return self.src_dir / name

    def image(self, name: str) -> Path:
        return self.images_dir / name
