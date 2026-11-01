"""Command line: load the YAML files, then list, generate or convert."""

from __future__ import annotations

import argparse
from pathlib import Path

from .diagnostics import Diagnostics
from .generator import OutputLayout, convert_images, generate_sources, image_jobs, write_files
from .loader import load_project


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="gen_theme.py", description="Generate LVGL C++ themes from YAML.")
    parser.add_argument("--colors", type=Path, required=True, help="global colors.yaml")
    parser.add_argument("--fonts", type=Path, required=True, help="global fonts.yaml")
    parser.add_argument("--theme", type=Path, action="append", required=True, dest="themes",
                        help="theme file (repeat for each theme)")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="output directory (include/ and src/ are created inside)")
    parser.add_argument("--lvgl-dir", type=Path,
                        help="LVGL source directory, used to convert PNG images with LVGLImage.py; "
                             "without it, images are only declared")
    parser.add_argument("--cf", default="ARGB8888", help="image color format (default ARGB8888)")
    parser.add_argument("--stamp", type=Path, help="file touched after a successful generation")

    listing = parser.add_mutually_exclusive_group()
    listing.add_argument("--list-outputs", action="store_true",
                         help="print the files that would be generated and exit")
    listing.add_argument("--list-inputs", action="store_true",
                         help="print the YAML and image files the generation depends on and exit")
    return parser.parse_args(argv)


def print_paths(paths: list[Path]) -> None:
    print("\n".join(str(path) for path in paths))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    diagnostics = Diagnostics()

    project = load_project(args.colors, args.fonts, args.themes, diagnostics)
    if diagnostics:
        diagnostics.report()
        return 1

    if args.list_inputs:
        print_paths(project.input_files)
        return 0

    layout = OutputLayout(args.output.resolve())
    files = generate_sources(project, layout)
    jobs = image_jobs(project, layout) if args.lvgl_dir else []

    if args.list_outputs:
        print_paths([*files, *(job.output for job in jobs)])
        return 0

    if jobs:
        files.update(convert_images(jobs, args.lvgl_dir.resolve(), args.cf, diagnostics))
        if diagnostics:
            diagnostics.report()
            return 1

    write_files(files)

    if args.stamp:
        args.stamp.parent.mkdir(parents=True, exist_ok=True)
        args.stamp.touch()
    return 0
