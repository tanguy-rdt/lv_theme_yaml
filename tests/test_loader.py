import pytest

from lv_theme_yaml.diagnostics import Source
from lv_theme_yaml.loader import load_project
from lv_theme_yaml.loader.colors import parse_color
from lv_theme_yaml.loader.props import parse_props
from lv_theme_yaml.loader.selectors import parse_selector
from lv_theme_yaml.loader.yaml_file import load_yaml
from lv_theme_yaml.model import Prop, Selector


# -- colors -------------------------------------------------------------------

@pytest.mark.parametrize("text, rgb", [
    ("#102030", (0x10, 0x20, 0x30)),
    ("0xFFAA00", (255, 170, 0)),
    ("rgb(1, 2, 3)", (1, 2, 3)),
    ("rgb(0,0,255)", (0, 0, 255)),
])
def test_valid_colors(source, diagnostics, text, rgb):
    assert parse_color(source, "c", text) == rgb
    assert not diagnostics


@pytest.mark.parametrize("text", ["blue", "#12345", "rgb(256, 0, 0)", "rgb(1, 2)", "12"])
def test_invalid_colors(source, diagnostics, text):
    assert parse_color(source, "c", text) is None
    assert diagnostics


# -- selectors ----------------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("button", Selector("button")),
    ("list > button", Selector("button", parent="list")),
    ("list button", Selector("button", ancestor="list")),
    ("obj list > button", Selector("button", parent="list", ancestor="obj")),
    ("button:checked:pressed", Selector("button", states=("checked", "pressed"))),
    ("switch:checked::indicator", Selector("switch", states=("checked",), part="indicator")),
    (":screen", Selector(None)),
    (":screen::scrollbar", Selector(None, part="scrollbar")),
])
def test_valid_selectors(source, diagnostics, text, expected):
    assert parse_selector(source, "s", text) == expected
    assert not diagnostics


@pytest.mark.parametrize("text", [
    "a > b > c", "a b c", "> a", "a >", "list:pressed > button", "button:", "::knob", ":hover", "",
])
def test_invalid_selectors(source, diagnostics, text):
    assert parse_selector(source, "s", text) is None
    assert diagnostics


# -- props --------------------------------------------------------------------

def test_shorthand_expansion(source, diagnostics):
    props = parse_props(source, "p", {"pad_all": "4", "radius": "8"})
    assert props == [Prop("pad_top", "4"), Prop("pad_bottom", "4"),
                     Prop("pad_left", "4"), Prop("pad_right", "4"), Prop("radius", "8")]
    assert not diagnostics


def test_shorthand_conflict(source, diagnostics):
    parse_props(source, "p", {"pad_all": "4", "pad_left": "2"})
    assert "'pad_left' is already set by 'pad_all'" in diagnostics.messages[0]


# -- yaml ---------------------------------------------------------------------

def test_duplicate_keys(write, diagnostics):
    path = write("x.yaml", "a: 1\na: 2\n")
    load_yaml(Source(path, diagnostics))
    assert diagnostics.messages == [f"{path}: line 2: duplicate key 'a'"]


def test_scalars_stay_strings(write, diagnostics):
    path = write("x.yaml", "a: true\nb: 8\n")
    assert load_yaml(Source(path, diagnostics)) == {"a": "true", "b": "8"}


# -- project ------------------------------------------------------------------

def test_valid_project(project_files, diagnostics):
    project = load_project(project_files["colors"], project_files["fonts"],
                           [project_files["theme"]], diagnostics)
    assert not diagnostics
    assert [c.name for c in project.colors] == ["bg", "text"]
    assert project.icon_keys == ["back"]
    assert project.themes[0].uses_screen_selector


def _errors(diagnostics):
    return "\n".join(diagnostics.messages)


def test_color_and_font_with_same_name(write, project_files, diagnostics):
    fonts = write("fonts.yaml", "bg: montserrat_14\nbody: montserrat_14\n")
    load_project(project_files["colors"], fonts, [project_files["theme"]], diagnostics)
    assert "'bg' is both a color and a font" in _errors(diagnostics)


def test_theme_cannot_define_globals(write, project_files, diagnostics):
    theme = write("t.yaml", "name: t\ncolors: {a: '#000000'}\nstyles: {s: {selectors: [a], props: {radius: 1}}}\n")
    load_project(project_files["colors"], project_files["fonts"], [theme], diagnostics)
    assert "'colors' is global only" in _errors(diagnostics)


def test_duplicate_theme_names(project_files, diagnostics):
    theme = project_files["theme"]
    load_project(project_files["colors"], project_files["fonts"], [theme, theme], diagnostics)
    assert "theme 'day' is already defined" in _errors(diagnostics)


def test_themes_must_share_images(write, project_files, diagnostics):
    night = write("night.yaml", "name: night\nstyles: {s: {selectors: [a], props: {radius: 1}}}\n")
    load_project(project_files["colors"], project_files["fonts"],
                 [project_files["theme"], night], diagnostics)
    assert "missing image keys ['back']" in _errors(diagnostics)


def test_missing_image_file(write, project_files, diagnostics):
    theme = write("t.yaml", "name: t\nimages: {a: nope.png}\nstyles: {s: {selectors: [a], props: {radius: 1}}}\n")
    load_project(project_files["colors"], project_files["fonts"], [theme], diagnostics)
    assert "image file not found" in _errors(diagnostics)


def test_reserved_and_keyword_names(write, project_files, diagnostics):
    colors = write("c.yaml", 'default: "#000000"\ncount: "#000000"\n')
    load_project(colors, project_files["fonts"], [project_files["theme"]], diagnostics)
    errors = _errors(diagnostics)
    assert "'default' is a C++ keyword" in errors
    assert "'count' is reserved" in errors
