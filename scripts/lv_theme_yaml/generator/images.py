"""Conversion of the PNG files into LVGL C sources, with LVGL's own LVGLImage.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .. import naming
from ..diagnostics import Diagnostics
from ..model import Project
from .layout import OutputLayout


@dataclass(frozen=True)
class ImageJob:
    symbol: str             # C symbol of the lv_image_dsc_t, also the file stem
    png: Path
    output: Path


def image_jobs(project: Project, layout: OutputLayout) -> list[ImageJob]:
    jobs = []
    for theme in project.themes:
        for key in project.icon_keys:
            image = theme.images[key]
            variants = [(image.ltr, False)] + ([(image.rtl, True)] if image.rtl else [])
            for png, rtl in variants:
                symbol = naming.image_symbol(theme.name, key, rtl=rtl)
                jobs.append(ImageJob(symbol, png, layout.image(naming.image_source(symbol))))
    return jobs


class ImageConverter:
    def __init__(self, lvgl_dir: Path, color_format: str) -> None:
        self.script = lvgl_dir / "scripts" / "LVGLImage.py"
        self.color_format = color_format

    def check(self, diagnostics: Diagnostics) -> bool:
        if not self.script.is_file():
            diagnostics.error(self.script, "", "LVGLImage.py not found (check --lvgl-dir)")
            return False
        return True

    def convert(self, job: ImageJob, work_dir: Path, diagnostics: Diagnostics) -> str | None:
        command = [
            sys.executable, str(self.script),
            "--ofmt", "C",
            "--cf", self.color_format,
            "--name", job.symbol,
            "-o", str(work_dir),
            str(job.png),
        ]
        process = subprocess.run(command, capture_output=True, text=True)
        produced = work_dir / naming.image_source(job.symbol)
        if process.returncode != 0 or not produced.is_file():
            detail = (process.stderr or process.stdout).strip().splitlines()
            diagnostics.error(job.png, "", "image conversion failed: " + (detail[-1] if detail else "no output"))
            return None
        return produced.read_text(encoding="utf-8")


def convert_images(jobs: list[ImageJob], lvgl_dir: Path, color_format: str,
                   diagnostics: Diagnostics) -> dict[Path, str]:
    converter = ImageConverter(lvgl_dir, color_format)
    if not converter.check(diagnostics):
        return {}

    results: dict[Path, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for job in jobs:
            if (content := converter.convert(job, Path(tmp), diagnostics)) is not None:
                results[job.output] = content
    return results
