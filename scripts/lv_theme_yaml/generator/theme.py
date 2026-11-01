"""The header and source of one theme class."""

from __future__ import annotations

from .. import naming
from ..model import Project, Prop, Selector, Style, Theme
from . import cpp


class ThemeGenerator:
    """Writes <name>_theme.h and <name>_theme.cpp for one theme of the project."""

    def __init__(self, project: Project, theme: Theme) -> None:
        self.project = project
        self.theme = theme
        self.class_name = naming.theme_class(theme.name)
        self.inputs = [project.colors_file, project.fonts_file, theme.file]

    # -- header ---------------------------------------------------------------

    def header(self) -> str:
        file_name = naming.theme_header(self.theme.name)
        body = (
            cpp.include_groups([cpp.local(naming.RUNTIME_HEADER), cpp.local(naming.IDS_HEADER)])
            + f"class {self.class_name} : public Theme {{\n"
            + "    public:\n"
            + f"        {self.class_name}();\n"
            + "};\n"
        )
        return cpp.header_file(self.inputs, naming.include_guard(file_name), body)

    # -- source ---------------------------------------------------------------

    def source(self) -> str:
        return (
            cpp.banner(self.inputs)
            + cpp.include_groups(
                [
                    cpp.local(naming.theme_header(self.theme.name)),
                    cpp.local(naming.COLORS_HEADER),
                    cpp.local(naming.FONTS_HEADER),
                ],
                [cpp.system("array")],
            )
            + self._image_declarations()
            + "namespace {\n\n"
            + "".join(self._style(style) for style in self.theme.styles)
            + self._image_tables()
            + self._is_screen()
            + self._rules()
            + "}\n\n"
            + self._constructor()
        )

    def _image_declarations(self) -> str:
        symbols = []
        for key in self.project.icon_keys:
            symbols.append(naming.image_symbol(self.theme.name, key))
            if self.theme.images[key].rtl:
                symbols.append(naming.image_symbol(self.theme.name, key, rtl=True))
        if not symbols:
            return ""
        return "".join(f"LV_IMAGE_DECLARE({symbol});\n" for symbol in symbols) + "\n"

    def _style(self, style: Style) -> str:
        props_name = naming.style_props(style.name)
        props = [self._prop(prop) for prop in style.props] + ["LV_STYLE_CONST_PROPS_END"]
        return (
            cpp.to_array(props_name, "lv_style_const_prop_t", props)
            + f"constexpr LV_STYLE_CONST_INIT({naming.style_object(style.name)}, {props_name}.data());\n\n"
        )

    def _prop(self, prop: Prop) -> str:
        return f"LV_STYLE_CONST_{prop.name.upper()}({self._value(prop.value)})"

    def _value(self, raw: str) -> str:
        """A color or font name refers to the global constant, anything else is copied."""
        if raw in self.project.color_names:
            return f"{naming.COLORS_NAMESPACE}::{raw}"
        if raw in self.project.font_names:
            return f"{naming.FONTS_NAMESPACE}::{raw}"
        return raw

    def _image_tables(self) -> str:
        keys = self.project.icon_keys
        images = [f"&{naming.image_symbol(self.theme.name, key)}" for key in keys]
        rtl_images = [
            f"rtl(Icon::{naming.enum_member(key)}, &{naming.image_symbol(self.theme.name, key, rtl=True)})"
            for key in keys
            if self.theme.images[key].rtl
        ]
        return (
            cpp.std_array("kImages", "const lv_image_dsc_t*", images)
            + cpp.count_assert("kImages", "Icon") + "\n"
            + cpp.std_array("kImagesRtl", "RTLImage", rtl_images) + "\n"
        )

    def _is_screen(self) -> str:
        if not self.theme.uses_screen_selector:
            return ""
        return "bool is_screen(lv_obj_t* obj) { return lv_obj_get_parent(obj) == nullptr; }\n\n"

    def _rules(self) -> str:
        rules = [
            _rule(selector, naming.style_object(style.name))
            for style in self.theme.styles
            for selector in style.selectors
        ]
        return cpp.to_array("kRules", "Rule", rules) + "\n"

    def _constructor(self) -> str:
        return (
            f"{self.class_name}::{self.class_name}()\n"
            f"    : Theme(kRules, {naming.COLORS_NAMESPACE}::kColors, "
            f"{naming.FONTS_NAMESPACE}::kFonts, kImages, kImagesRtl) {{}}\n"
        )


def _rule(selector: Selector, style: str) -> str:
    fields = [f".cls = &{naming.widget_class(selector.target or 'obj')}"]
    if selector.parent:
        fields.append(f".parent = &{naming.widget_class(selector.parent)}")
    if selector.ancestor:
        fields.append(f".ancestor = &{naming.widget_class(selector.ancestor)}")
    if selector.is_screen:
        fields.append(".match = is_screen")

    rule = f"{{.sel = {{{', '.join(fields)}}}, .style = &{style}"
    if (value := _style_selector(selector)) is not None:
        rule += f", .selector = {value}"
    return rule + "}"


def _style_selector(selector: Selector) -> str | None:
    """LV_PART_* | LV_STATE_*, or None for the main part in the default state.

    Mixing the two enums needs a cast to avoid -Wdeprecated-enum-enum-conversion.
    """
    has_part = selector.part is not None and selector.part != "main"
    terms = [f"LV_PART_{selector.part.upper()}"] if has_part else []
    terms += [f"LV_STATE_{state.upper()}" for state in selector.states]
    if not terms:
        return None
    if has_part and selector.states:
        terms[0] = f"static_cast<lv_style_selector_t>({terms[0]})"
    return " | ".join(terms)
