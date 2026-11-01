"""Every C++ identifier and generated file name, in one place."""

from __future__ import annotations

COLORS_NAMESPACE = "theme_colors"
FONTS_NAMESPACE = "theme_fonts"

IDS_HEADER = "theme_ids.h"
COLORS_HEADER = "theme_colors.h"
FONTS_HEADER = "theme_fonts.h"
RUNTIME_HEADER = "theme.h"


def pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def enum_member(key: str) -> str:
    return key.upper()


def include_guard(file_name: str) -> str:
    return file_name.upper().replace(".", "_")


def theme_class(theme_name: str) -> str:
    return f"{pascal(theme_name)}Theme"


def theme_header(theme_name: str) -> str:
    return f"{theme_name}_theme.h"


def theme_source(theme_name: str) -> str:
    return f"{theme_name}_theme.cpp"


def style_props(style_name: str) -> str:
    return f"k{pascal(style_name)}Props"


def style_object(style_name: str) -> str:
    return f"k{pascal(style_name)}Style"


def widget_class(class_name: str) -> str:
    return f"lv_{class_name}_class"


def lvgl_font(lvgl_name: str) -> str:
    return f"lv_font_{lvgl_name}"


def image_symbol(theme_name: str, key: str, rtl: bool = False) -> str:
    return f"icon_{key}_{theme_name}" + ("_rtl" if rtl else "")


def image_source(symbol: str) -> str:
    return f"{symbol}.c"
