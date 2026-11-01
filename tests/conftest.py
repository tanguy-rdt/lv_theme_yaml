import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lv_theme_yaml.diagnostics import Diagnostics, Source  # noqa: E402


@pytest.fixture
def diagnostics():
    return Diagnostics()


@pytest.fixture
def source(tmp_path, diagnostics):
    return Source(tmp_path / "theme.yaml", diagnostics)


@pytest.fixture
def write(tmp_path):
    """write("name.yaml", text) creates a file in the test directory and returns its path."""
    def _write(name: str, text: str) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path
    return _write


@pytest.fixture
def project_files(write):
    """A minimal valid project: two colors, one font, one theme with an image."""
    write("icon.png", "")
    return {
        "colors": write("colors.yaml", 'bg: "#102030"\ntext: rgb(1, 2, 3)\n'),
        "fonts": write("fonts.yaml", "body: montserrat_14\n"),
        "theme": write(
            "day.yaml",
            "name: day\n"
            "images:\n"
            "  back:\n"
            "    ltr: icon.png\n"
            "    rtl: icon.png\n"
            "styles:\n"
            "  screen:\n"
            '    selectors: [":screen"]\n'
            "    props: {bg_color: bg, text_font: body, pad_all: 4}\n"
            "  knob:\n"
            '    selectors: ["slider:pressed::knob"]\n'
            "    props: {radius: LV_RADIUS_CIRCLE}\n",
        ),
    }
