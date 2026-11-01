"""Headers shared by every theme: identifiers, colors and fonts."""

from __future__ import annotations

from .. import naming
from ..model import Project
from . import cpp

_COMMON_INCLUDES = cpp.include_groups(
    [cpp.system("lvgl.h")],
    [cpp.system("array")],
    [cpp.local(naming.IDS_HEADER)],
)


def ids_header(project: Project) -> str:
    body = (
        cpp.enum_class("Color", [naming.enum_member(color.name) for color in project.colors])
        + cpp.enum_class("Font", [naming.enum_member(font.name) for font in project.fonts])
        + cpp.enum_class("Icon", [naming.enum_member(key) for key in project.icon_keys])
    )
    inputs = [project.colors_file, project.fonts_file, *(theme.file for theme in project.themes)]
    return cpp.header_file(inputs, naming.include_guard(naming.IDS_HEADER), body)


def colors_header(project: Project) -> str:
    constants = "".join(
        f"inline constexpr lv_color_t {color.name} = LV_COLOR_MAKE({r}, {g}, {b});\n"
        for color in project.colors
        for r, g, b in [color.rgb]
    )
    body = (
        _COMMON_INCLUDES
        + f"namespace {naming.COLORS_NAMESPACE} {{\n\n"
        + constants
        + "\ninline " + cpp.std_array("kColors", "lv_color_t", [c.name for c in project.colors])
        + cpp.count_assert("kColors", "Color")
        + "\n}\n"
    )
    return cpp.header_file([project.colors_file], naming.include_guard(naming.COLORS_HEADER), body)


def fonts_header(project: Project) -> str:
    constants = "".join(
        f"inline constexpr const lv_font_t* {font.name} = &{naming.lvgl_font(font.lvgl_name)};\n"
        for font in project.fonts
    )
    body = (
        _COMMON_INCLUDES
        + f"namespace {naming.FONTS_NAMESPACE} {{\n\n"
        + constants
        + "\ninline " + cpp.std_array("kFonts", "const lv_font_t*", [f.name for f in project.fonts])
        + cpp.count_assert("kFonts", "Font")
        + "\n}\n"
    )
    return cpp.header_file([project.fonts_file], naming.include_guard(naming.FONTS_HEADER), body)
