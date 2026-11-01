from lv_theme_yaml.cli import main
from lv_theme_yaml.generator import OutputLayout, generate_sources, image_jobs
from lv_theme_yaml.loader import load_project


def _project(project_files, diagnostics):
    project = load_project(project_files["colors"], project_files["fonts"],
                           [project_files["theme"]], diagnostics)
    assert not diagnostics
    return project


def test_layout(tmp_path, project_files, diagnostics):
    layout = OutputLayout(tmp_path / "gen")
    files = generate_sources(_project(project_files, diagnostics), layout)
    names = sorted(str(path.relative_to(layout.root)) for path in files)
    assert names == [
        "include/day_theme.h",
        "include/theme_colors.h",
        "include/theme_fonts.h",
        "include/theme_ids.h",
        "src/day_theme.cpp",
    ]


def test_image_jobs_go_to_src_images(tmp_path, project_files, diagnostics):
    layout = OutputLayout(tmp_path / "gen")
    jobs = image_jobs(_project(project_files, diagnostics), layout)
    assert [job.symbol for job in jobs] == ["icon_back_day", "icon_back_day_rtl"]
    assert all(job.output.parent == layout.images_dir for job in jobs)


def test_theme_source(tmp_path, project_files, diagnostics):
    layout = OutputLayout(tmp_path / "gen")
    source = generate_sources(_project(project_files, diagnostics), layout)[layout.source("day_theme.cpp")]

    assert "LV_STYLE_CONST_BG_COLOR(theme_colors::bg)" in source
    assert "LV_STYLE_CONST_TEXT_FONT(theme_fonts::body)" in source
    assert "LV_STYLE_CONST_PAD_LEFT(4)" in source
    assert "LV_STYLE_CONST_RADIUS(LV_RADIUS_CIRCLE)" in source
    assert "{.sel = {.cls = &lv_obj_class, .match = is_screen}, .style = &kScreenStyle}" in source
    assert (".selector = static_cast<lv_style_selector_t>(LV_PART_KNOB) | LV_STATE_PRESSED"
            in source)
    assert "rtl(Icon::BACK, &icon_back_day_rtl)" in source
    assert ": Theme(kRules, theme_colors::kColors, theme_fonts::kFonts, kImages, kImagesRtl) {}" in source


def test_section_order(tmp_path, project_files, diagnostics):
    layout = OutputLayout(tmp_path / "gen")
    source = generate_sources(_project(project_files, diagnostics), layout)[layout.source("day_theme.cpp")]
    markers = ["#include", "LV_IMAGE_DECLARE", "namespace {", "kScreenProps", "kImages{",
               "kImagesRtl{", "is_screen(lv_obj_t*", "kRules", "DayTheme::DayTheme()"]
    positions = [source.index(marker) for marker in markers]
    assert positions == sorted(positions)


def test_cli_writes_only_changed_files(tmp_path, project_files):
    out = tmp_path / "gen"
    args = ["--colors", str(project_files["colors"]), "--fonts", str(project_files["fonts"]),
            "--theme", str(project_files["theme"]), "-o", str(out)]
    assert main(args) == 0

    header = out / "include" / "theme_ids.h"
    before = header.stat().st_mtime_ns
    assert main(args) == 0
    assert header.stat().st_mtime_ns == before


def test_cli_reports_errors(tmp_path, write, project_files, capsys):
    broken = write("broken.yaml", "name: x\nstyles: {s: {selectors: ['a > b > c'], props: {radius: 1}}}\n")
    out = tmp_path / "gen"
    code = main(["--colors", str(project_files["colors"]), "--fonts", str(project_files["fonts"]),
                 "--theme", str(broken), "-o", str(out)])
    assert code == 1
    assert "invalid selector 'a > b > c'" in capsys.readouterr().err
    assert not out.exists()
