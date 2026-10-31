#!/usr/bin/env python3
"""Generate LVGL 9.6 C++23 themes from YAML files.

Usage:
    gen_theme.py --colors colors.yaml --fonts fonts.yaml \
                 --theme day.yaml --theme night.yaml \
                 -o <output dir> [--lvgl-dir <lvgl source dir>] [--cf ARGB8888] \
                 [--stamp <file>] [--list-outputs] [--list-inputs]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")
HEX_RE = re.compile(r"^(?:#|0[xX])([0-9a-fA-F]{6})$")
RGB_RE = re.compile(r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$")

CPP_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool", "break",
    "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept",
    "const", "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await",
    "co_return", "co_yield", "decltype", "default", "delete", "do", "double", "dynamic_cast",
    "else", "enum", "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
    "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq",
    "nullptr", "operator", "or", "or_eq", "private", "protected", "public", "register",
    "reinterpret_cast", "requires", "return", "short", "signed", "sizeof", "static",
    "static_assert", "static_cast", "struct", "switch", "template", "this", "thread_local",
    "throw", "true", "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
}

SHORTHANDS = {
    "pad_all": ["pad_top", "pad_bottom", "pad_left", "pad_right"],
    "pad_hor": ["pad_left", "pad_right"],
    "pad_ver": ["pad_top", "pad_bottom"],
    "pad_gap": ["pad_row", "pad_column"],
}

THEME_KEYS = {"name", "images", "styles"}
STYLE_KEYS = {"selectors", "props"}
IMAGE_KEYS = {"ltr", "rtl"}

COLORS_NS = "theme_colors"
FONTS_NS = "theme_fonts"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class Errors:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def add(self, file: Path, path: str, message: str) -> None:
        location = f"{file}: {path}" if path else f"{file}"
        self.messages.append(f"{location}: {message}")

    def __bool__(self) -> bool:
        return bool(self.messages)


# ---------------------------------------------------------------------------
# YAML loading: every scalar stays a string, duplicate keys are reported
# ---------------------------------------------------------------------------

class _Loader(yaml.BaseLoader):
    pass


def _construct_mapping(loader: _Loader, node: yaml.MappingNode, deep: bool = False) -> dict:
    seen: set = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            loader.duplicates.append((key, key_node.start_mark.line + 1))
        seen.add(key)
    return yaml.BaseLoader.construct_mapping(loader, node, deep)


_Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml(path: Path, errors: Errors):
    if not path.is_file():
        errors.add(path, "", "file not found")
        return None
    try:
        loader = _Loader(path.read_text(encoding="utf-8"))
        loader.duplicates = []
        try:
            data = loader.get_single_data()
        finally:
            loader.dispose()
    except yaml.YAMLError as exc:
        errors.add(path, "", f"invalid YAML: {exc}")
        return None
    for key, line in loader.duplicates:
        errors.add(path, f"line {line}", f"duplicate key '{key}'")
    return data


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

@dataclass
class Color:
    name: str
    rgb: tuple[int, int, int]


@dataclass
class Font:
    name: str
    lvgl_name: str


@dataclass
class Image:
    key: str
    ltr: Path
    rtl: Path | None


@dataclass
class Selector:
    target: str | None          # class name, None for :screen
    parent: str | None = None
    ancestor: str | None = None
    states: list[str] = field(default_factory=list)
    part: str | None = None


@dataclass
class Style:
    name: str
    selectors: list[Selector]
    props: list[tuple[str, str]]   # (lvgl prop, raw value) after shorthand expansion


@dataclass
class Theme:
    file: Path
    name: str
    images: dict[str, Image]
    styles: list[Style]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def check_ident(value, file: Path, path: str, errors: Errors, what: str,
                cpp_name: bool = False, enum_member: bool = False) -> bool:
    if not isinstance(value, str) or not IDENT_RE.match(value):
        errors.add(file, path, f"invalid {what} '{value}' (expected snake_case: [a-z][a-z0-9_]*)")
        return False
    if cpp_name and value in CPP_KEYWORDS:
        errors.add(file, path, f"{what} '{value}' is a C++ keyword")
        return False
    if enum_member and value == "count":
        errors.add(file, path, f"{what} 'count' is reserved (it would clash with COUNT)")
        return False
    return True


def parse_color(value, file: Path, path: str, errors: Errors) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        errors.add(file, path, "color must be a string")
        return None
    text = value.strip()
    if m := HEX_RE.match(text):
        v = int(m.group(1), 16)
        return (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF
    if m := RGB_RE.match(text):
        rgb = tuple(int(c) for c in m.groups())
        if any(c > 255 for c in rgb):
            errors.add(file, path, f"color component out of range 0-255 in '{value}'")
            return None
        return rgb  # type: ignore[return-value]
    errors.add(file, path, f"invalid color '{value}' (expected #RRGGBB, 0xRRGGBB or rgb(r, g, b))")
    return None


def parse_selector(text, file: Path, path: str, errors: Errors) -> Selector | None:
    if not isinstance(text, str) or not text.strip():
        errors.add(file, path, "selector must be a non-empty string")
        return None

    tokens = re.sub(r"\s*>\s*", " > ", text.strip()).split()

    ancestor = parent = None
    if len(tokens) == 1:
        target_text = tokens[0]
    elif len(tokens) == 2 and ">" not in tokens:
        ancestor, target_text = tokens
    elif len(tokens) == 3 and tokens[1] == ">" and ">" not in (tokens[0], tokens[2]):
        parent, _, target_text = tokens
    elif len(tokens) == 4 and tokens[2] == ">" and ">" not in (tokens[0], tokens[1], tokens[3]):
        ancestor, parent, _, target_text = tokens
    else:
        errors.add(file, path, f"invalid selector '{text}' "
                               "(expected [ancestor ] [parent > ]target)")
        return None

    ok = True
    for role, name in (("ancestor", ancestor), ("parent", parent)):
        if name is not None and not IDENT_RE.match(name):
            errors.add(file, path, f"invalid {role} '{name}' in '{text}' "
                                   "(a class name only, no state or part)")
            ok = False

    base, sep, part = target_text.partition("::")
    if sep and (not part or not IDENT_RE.match(part)):
        errors.add(file, path, f"invalid part in '{text}'")
        ok = False

    cls, *states = base.split(":")
    for state in states:
        if not IDENT_RE.match(state):
            errors.add(file, path, f"invalid state '{state}' in '{text}'")
            ok = False

    if cls == "":
        if states[:1] != ["screen"]:
            errors.add(file, path, f"missing class in '{text}'")
            ok = False
        target = None
        states = states[1:]
    elif not IDENT_RE.match(cls):
        errors.add(file, path, f"invalid class '{cls}' in '{text}'")
        ok = False
        target = cls
    else:
        target = cls

    if not ok:
        return None
    return Selector(target=target, parent=parent, ancestor=ancestor,
                    states=states, part=part or None)


# ---------------------------------------------------------------------------
# Parsing the files
# ---------------------------------------------------------------------------

def parse_colors(path: Path, errors: Errors) -> list[Color]:
    data = load_yaml(path, errors)
    if data is None:
        return []
    if not isinstance(data, dict) or not data:
        errors.add(path, "", "expected a non-empty mapping name: color")
        return []
    colors = []
    for name, value in data.items():
        if check_ident(name, path, name, errors, "color name",
                       cpp_name=True, enum_member=True):
            if (rgb := parse_color(value, path, name, errors)) is not None:
                colors.append(Color(name, rgb))
    return colors


def parse_fonts(path: Path, errors: Errors) -> list[Font]:
    data = load_yaml(path, errors)
    if data is None:
        return []
    if not isinstance(data, dict) or not data:
        errors.add(path, "", "expected a non-empty mapping name: lvgl_font")
        return []
    fonts = []
    for name, value in data.items():
        if not check_ident(name, path, name, errors, "font name",
                           cpp_name=True, enum_member=True):
            continue
        if not isinstance(value, str) or not re.match(r"^[a-z0-9_]+$", value):
            errors.add(path, name, f"invalid LVGL font name '{value}' (e.g. montserrat_14)")
            continue
        fonts.append(Font(name, value))
    return fonts


def parse_images(data, file: Path, errors: Errors) -> dict[str, Image]:
    images: dict[str, Image] = {}
    if data is None:
        return images
    if not isinstance(data, dict):
        errors.add(file, "images", "expected a mapping key: path")
        return images

    def resolve(value, key_path: str) -> Path | None:
        if not isinstance(value, str) or not value.strip():
            errors.add(file, key_path, "expected a file path")
            return None
        resolved = (file.parent / value).resolve()
        if not resolved.is_file():
            errors.add(file, key_path, f"image file not found: {resolved}")
            return None
        return resolved

    for key, value in data.items():
        key_path = f"images.{key}"
        if not check_ident(key, file, key_path, errors, "image key", enum_member=True):
            continue
        if isinstance(value, dict):
            unknown = set(value) - IMAGE_KEYS
            if unknown:
                errors.add(file, key_path, f"unknown keys {sorted(unknown)} (expected ltr, rtl)")
            if "ltr" not in value:
                errors.add(file, key_path, "missing 'ltr'")
                continue
            ltr = resolve(value["ltr"], f"{key_path}.ltr")
            rtl = resolve(value["rtl"], f"{key_path}.rtl") if "rtl" in value else None
            if ltr and ("rtl" not in value or rtl) and not unknown:
                images[key] = Image(key, ltr, rtl)
        else:
            if ltr := resolve(value, key_path):
                images[key] = Image(key, ltr, None)
    return images


def parse_props(data, file: Path, path: str, errors: Errors) -> list[tuple[str, str]]:
    if not isinstance(data, dict) or not data:
        errors.add(file, path, "expected a non-empty mapping prop: value")
        return []
    props: list[tuple[str, str]] = []
    origin: dict[str, str] = {}
    for name, value in data.items():
        if not isinstance(name, str) or not IDENT_RE.match(name):
            errors.add(file, f"{path}.{name}", "invalid prop name")
            continue
        if not isinstance(value, str) or not value.strip():
            errors.add(file, f"{path}.{name}", "expected a scalar value")
            continue
        for real in SHORTHANDS.get(name, [name]):
            if real in origin:
                errors.add(file, f"{path}.{name}",
                           f"'{real}' is already set by '{origin[real]}'")
                continue
            origin[real] = name
            props.append((real, value.strip()))
    return props


def parse_theme(path: Path, errors: Errors) -> Theme | None:
    data = load_yaml(path, errors)
    if data is None:
        return None
    if not isinstance(data, dict):
        errors.add(path, "", "expected a mapping with name, images, styles")
        return None

    for key in data:
        if key in ("colors", "fonts"):
            errors.add(path, key, f"'{key}' is global only, define it in the global {key}.yaml")
        elif key not in THEME_KEYS:
            errors.add(path, key, "unknown key (expected name, images, styles)")

    name = data.get("name")
    if name is None:
        errors.add(path, "name", "missing")
    elif not check_ident(name, path, "name", errors, "theme name"):
        name = None

    images = parse_images(data.get("images"), path, errors)

    styles: list[Style] = []
    raw_styles = data.get("styles")
    if raw_styles is None:
        errors.add(path, "styles", "missing")
    elif not isinstance(raw_styles, dict) or not raw_styles:
        errors.add(path, "styles", "expected a non-empty mapping")
    else:
        for style_name, body in raw_styles.items():
            style_path = f"styles.{style_name}"
            if not check_ident(style_name, path, style_path, errors, "style name"):
                continue
            if not isinstance(body, dict):
                errors.add(path, style_path, "expected a mapping with selectors and props")
                continue
            for key in set(body) - STYLE_KEYS:
                errors.add(path, f"{style_path}.{key}", "unknown key (expected selectors, props)")

            raw_selectors = body.get("selectors")
            selectors: list[Selector] = []
            if raw_selectors is None:
                errors.add(path, f"{style_path}.selectors", "missing")
            elif not isinstance(raw_selectors, list) or not raw_selectors:
                errors.add(path, f"{style_path}.selectors", "expected a non-empty list")
            else:
                for i, text in enumerate(raw_selectors):
                    sel = parse_selector(text, path, f"{style_path}.selectors[{i}]", errors)
                    if sel:
                        selectors.append(sel)

            props = parse_props(body.get("props"), path, f"{style_path}.props", errors)
            styles.append(Style(style_name, selectors, props))

        seen: dict[str, str] = {}
        for style in styles:
            ident = pascal(style.name)
            if ident in seen:
                errors.add(path, f"styles.{style.name}",
                           f"generates the same C++ name as 'styles.{seen[ident]}'")
            seen[ident] = style.name

    if name is None:
        return None
    return Theme(path, name, images, styles)


# ---------------------------------------------------------------------------
# Cross-file checks
# ---------------------------------------------------------------------------

def check_global(colors: list[Color], fonts: list[Font], themes: list[Theme],
                 colors_file: Path, fonts_file: Path, errors: Errors) -> None:
    font_names = {f.name for f in fonts}
    for color in colors:
        if color.name in font_names:
            errors.add(colors_file, color.name, f"'{color.name}' is both a color and a font "
                                                f"(see {fonts_file})")

    seen: dict[str, Path] = {}
    for theme in themes:
        if theme.name in seen:
            errors.add(theme.file, "name", f"theme '{theme.name}' is already defined "
                                           f"in {seen[theme.name]}")
        seen[theme.name] = theme.file

    if themes:
        all_keys = set().union(*(t.images.keys() for t in themes))
        for theme in themes:
            missing = sorted(all_keys - theme.images.keys())
            if missing:
                errors.add(theme.file, "images",
                           f"missing image keys {missing} (every theme must define the same images)")


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def header_line(inputs: list[Path]) -> str:
    names = ", ".join(p.name for p in inputs)
    return f"// Generated by lv_theme_yaml from {names} — do not edit\n"


def array(name: str, element_type: str, items: list[str]) -> str:
    if not items:
        return f"constexpr std::array<{element_type}, 0> {name}{{}};\n"
    body = "".join(f"    {item},\n" for item in items)
    return f"constexpr std::array {name}{{\n{body}}};\n"


def image_symbol(theme: Theme, key: str, rtl: bool) -> str:
    return f"icon_{key}_{theme.name}" + ("_rtl" if rtl else "")


def gen_ids(colors: list[Color], fonts: list[Font], icon_keys: list[str],
            inputs: list[Path]) -> str:
    def enum(name: str, keys: list[str]) -> str:
        values = ", ".join([k.upper() for k in keys] + ["COUNT"])
        return f"enum class {name} {{ {values} }};\n"

    return (
        header_line(inputs)
        + "#ifndef THEME_IDS_H\n#define THEME_IDS_H\n\n"
        + enum("Color", [c.name for c in colors])
        + enum("Font", [f.name for f in fonts])
        + enum("Icon", icon_keys)
        + "\n#endif //THEME_IDS_H\n"
    )


def gen_colors(colors: list[Color], inputs: list[Path]) -> str:
    out = [header_line(inputs),
           "#ifndef THEME_COLORS_H\n#define THEME_COLORS_H\n\n",
           "#include <lvgl.h>\n\n#include <array>\n\n",
           "#include \"theme_ids.h\"\n\n",
           f"namespace {COLORS_NS} {{\n\n"]
    for c in colors:
        out.append(f"inline constexpr lv_color_t {c.name} = LV_COLOR_MAKE({c.rgb[0]}, {c.rgb[1]}, {c.rgb[2]});\n")
    out.append("\ninline " + array("kColors", "lv_color_t", [c.name for c in colors]))
    out.append("static_assert(kColors.size() == static_cast<size_t>(Color::COUNT));\n")
    out.append(f"\n}}\n\n#endif //THEME_COLORS_H\n")
    return "".join(out)


def gen_fonts(fonts: list[Font], inputs: list[Path]) -> str:
    out = [header_line(inputs),
           "#ifndef THEME_FONTS_H\n#define THEME_FONTS_H\n\n",
           "#include <lvgl.h>\n\n#include <array>\n\n",
           "#include \"theme_ids.h\"\n\n",
           f"namespace {FONTS_NS} {{\n\n"]
    for f in fonts:
        out.append(f"inline constexpr const lv_font_t* {f.name} = &lv_font_{f.lvgl_name};\n")
    out.append("\ninline " + array("kFonts", "const lv_font_t*", [f.name for f in fonts]))
    out.append("static_assert(kFonts.size() == static_cast<size_t>(Font::COUNT));\n")
    out.append(f"\n}}\n\n#endif //THEME_FONTS_H\n")
    return "".join(out)


def gen_theme_header(theme: Theme, inputs: list[Path]) -> str:
    guard = f"{theme.name.upper()}_THEME_H"
    cls = f"{pascal(theme.name)}Theme"
    return (
        header_line(inputs)
        + f"#ifndef {guard}\n#define {guard}\n\n"
        + "#include \"theme.h\"\n#include \"theme_ids.h\"\n\n"
        + f"class {cls} : public Theme {{\n"
        + "    public:\n"
        + f"        {cls}();\n"
        + "};\n\n"
        + f"#endif //{guard}\n"
    )


def selector_value(sel: Selector) -> str | None:
    terms = []
    if sel.part and sel.part != "main":
        terms.append(f"LV_PART_{sel.part.upper()}")
    terms += [f"LV_STATE_{s.upper()}" for s in sel.states]
    if not terms:
        return None
    if sel.part and sel.part != "main" and sel.states:
        terms[0] = f"static_cast<lv_style_selector_t>({terms[0]})"
    return " | ".join(terms)


def gen_rule(sel: Selector, style_ident: str) -> str:
    fields = [f".cls = &lv_{sel.target or 'obj'}_class"]
    if sel.parent:
        fields.append(f".parent = &lv_{sel.parent}_class")
    if sel.ancestor:
        fields.append(f".ancestor = &lv_{sel.ancestor}_class")
    if sel.target is None:
        fields.append(".match = is_screen")
    rule = f"{{.sel = {{{', '.join(fields)}}}, .style = &{style_ident}"
    if (value := selector_value(sel)) is not None:
        rule += f", .selector = {value}"
    return rule + "}"


def prop_value(raw: str, colors: dict[str, Color], fonts: dict[str, Font]) -> str:
    if raw in colors:
        return f"{COLORS_NS}::{raw}"
    if raw in fonts:
        return f"{FONTS_NS}::{raw}"
    return raw


def gen_theme_source(theme: Theme, icon_keys: list[str], colors: dict[str, Color],
                     fonts: dict[str, Font], inputs: list[Path]) -> str:
    cls = f"{pascal(theme.name)}Theme"
    out = [header_line(inputs),
           f"#include \"{theme.name}_theme.h\"\n",
           "#include \"theme_colors.h\"\n",
           "#include \"theme_fonts.h\"\n\n",
           "#include <array>\n\n"]

    declares = []
    for key in icon_keys:
        image = theme.images[key]
        declares.append(image_symbol(theme, key, False))
        if image.rtl:
            declares.append(image_symbol(theme, key, True))
    for symbol in declares:
        out.append(f"LV_IMAGE_DECLARE({symbol});\n")
    if declares:
        out.append("\n")

    out.append("namespace {\n\n")

    for style in theme.styles:
        ident = pascal(style.name)
        props = "".join(f"    LV_STYLE_CONST_{prop.upper()}({prop_value(value, colors, fonts)}),\n"
                        for prop, value in style.props)
        out.append(f"constexpr auto k{ident}Props = std::to_array<lv_style_const_prop_t>({{\n"
                   f"{props}    LV_STYLE_CONST_PROPS_END,\n}});\n")
        out.append(f"constexpr LV_STYLE_CONST_INIT(k{ident}Style, k{ident}Props.data());\n\n")

    out.append(array("kImages", "const lv_image_dsc_t*",
                     [f"&{image_symbol(theme, key, False)}" for key in icon_keys]))
    out.append("static_assert(kImages.size() == static_cast<size_t>(Icon::COUNT));\n\n")

    out.append(array("kImagesRtl", "RTLImage",
                     [f"rtl(Icon::{key.upper()}, &{image_symbol(theme, key, True)})"
                      for key in icon_keys if theme.images[key].rtl]))
    out.append("\n")

    if any(sel.target is None for style in theme.styles for sel in style.selectors):
        out.append("bool is_screen(lv_obj_t* obj) { return lv_obj_get_parent(obj) == nullptr; }\n\n")

    rules = [gen_rule(sel, f"k{pascal(style.name)}Style")
             for style in theme.styles for sel in style.selectors]
    body = "".join(f"    {rule},\n" for rule in rules)
    out.append(f"constexpr auto kRules = std::to_array<Rule>({{\n{body}}});\n\n")

    out.append("}\n\n")
    out.append(f"{cls}::{cls}()\n"
               f"    : Theme(kRules, {COLORS_NS}::kColors, {FONTS_NS}::kFonts, kImages, kImagesRtl) {{}}\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_if_changed(path: Path, content: bytes) -> None:
    if path.is_file() and path.read_bytes() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def image_jobs(themes: list[Theme], icon_keys: list[str]) -> list[tuple[str, Path]]:
    jobs = []
    for theme in themes:
        for key in icon_keys:
            image = theme.images[key]
            jobs.append((image_symbol(theme, key, False), image.ltr))
            if image.rtl:
                jobs.append((image_symbol(theme, key, True), image.rtl))
    return jobs


def convert_images(jobs: list[tuple[str, Path]], lvgl_dir: Path, cf: str,
                   out_dir: Path, errors: Errors) -> dict[Path, bytes]:
    script = lvgl_dir / "scripts" / "LVGLImage.py"
    if not script.is_file():
        errors.add(script, "", "LVGLImage.py not found (check --lvgl-dir)")
        return {}
    results: dict[Path, bytes] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for symbol, png in jobs:
            cmd = [sys.executable, str(script), "--ofmt", "C", "--cf", cf,
                   "--name", symbol, "-o", tmp, str(png)]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            produced = Path(tmp) / f"{symbol}.c"
            if proc.returncode != 0 or not produced.is_file():
                detail = (proc.stderr or proc.stdout).strip().splitlines()
                errors.add(png, "", "image conversion failed: "
                                    + (detail[-1] if detail else "no output"))
                continue
            results[out_dir / f"{symbol}.c"] = produced.read_bytes()
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate LVGL C++ themes from YAML.")
    parser.add_argument("--colors", type=Path, required=True, help="global colors.yaml")
    parser.add_argument("--fonts", type=Path, required=True, help="global fonts.yaml")
    parser.add_argument("--theme", type=Path, action="append", required=True,
                        help="theme file (repeat for each theme)")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output directory")
    parser.add_argument("--lvgl-dir", type=Path,
                        help="LVGL source directory, used to convert PNG images with LVGLImage.py; "
                             "without it, images are only declared")
    parser.add_argument("--cf", default="ARGB8888", help="image color format (default ARGB8888)")
    parser.add_argument("--stamp", type=Path, help="file touched after a successful generation")
    parser.add_argument("--list-outputs", action="store_true",
                        help="print the files that would be generated and exit")
    parser.add_argument("--list-inputs", action="store_true",
                        help="print the YAML and image files the generation depends on and exit")
    args = parser.parse_args(argv)

    errors = Errors()
    colors = parse_colors(args.colors, errors)
    fonts = parse_fonts(args.fonts, errors)
    themes = [t for p in args.theme if (t := parse_theme(p, errors)) is not None]
    check_global(colors, fonts, themes, args.colors, args.fonts, errors)

    if errors:
        for message in errors.messages:
            print(f"error: {message}", file=sys.stderr)
        print(f"{len(errors.messages)} error(s), nothing generated", file=sys.stderr)
        return 1

    if args.list_inputs:
        listed = [p.resolve() for p in (args.colors, args.fonts, *args.theme)]
        for theme in themes:
            for image in theme.images.values():
                listed += [image.ltr] + ([image.rtl] if image.rtl else [])
        print("\n".join(str(p) for p in dict.fromkeys(listed)))
        return 0

    out_dir = args.output.resolve()
    icon_keys = list(themes[0].images) if themes else []
    inputs = [args.colors, args.fonts, *args.theme]
    jobs = image_jobs(themes, icon_keys)

    files: dict[Path, bytes] = {
        out_dir / "theme_ids.h": gen_ids(colors, fonts, icon_keys, inputs).encode(),
        out_dir / "theme_colors.h": gen_colors(colors, [args.colors]).encode(),
        out_dir / "theme_fonts.h": gen_fonts(fonts, [args.fonts]).encode(),
    }
    color_map = {c.name: c for c in colors}
    font_map = {f.name: f for f in fonts}
    for theme in themes:
        theme_inputs = [args.colors, args.fonts, theme.file]
        files[out_dir / f"{theme.name}_theme.h"] = gen_theme_header(theme, theme_inputs).encode()
        files[out_dir / f"{theme.name}_theme.cpp"] = gen_theme_source(
            theme, icon_keys, color_map, font_map, theme_inputs).encode()

    if args.list_outputs:
        listed = list(files)
        if args.lvgl_dir:
            listed += [out_dir / f"{symbol}.c" for symbol, _ in jobs]
        print("\n".join(str(p) for p in listed))
        return 0

    if args.lvgl_dir:
        files.update(convert_images(jobs, args.lvgl_dir.resolve(), args.cf, out_dir, errors))
        if errors:
            for message in errors.messages:
                print(f"error: {message}", file=sys.stderr)
            print(f"{len(errors.messages)} error(s), nothing generated", file=sys.stderr)
            return 1

    for path, content in files.items():
        write_if_changed(path, content)

    if args.stamp:
        args.stamp.parent.mkdir(parents=True, exist_ok=True)
        args.stamp.touch()
    return 0


if __name__ == "__main__":
    sys.exit(main())
