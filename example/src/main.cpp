#include <lvgl.h>

#include <string_view>

#include "day_theme.h"
#include "night_theme.h"
#include "translations.h"

static Theme* day_theme;
static Theme* night_theme;
static Theme* current_theme;

static lv_obj_t* theme_icon;
static lv_obj_t* return_icon;

static lv_event_code_t EVENT_THEME_CHANGED;

static bool is_arabic() {
    const char* lang = lv_translation_get_language();
    return lang && std::string_view(lang) == "ar";
}

static void refresh_icons() {
    lv_image_set_src(theme_icon, current_theme->image(Icon::PAINT));
    lv_image_set_src(return_icon, current_theme->image(Icon::RETURN));
}

static lv_obj_tree_walk_res_t replace_theme_styles(lv_obj_t* obj, void* user_data) {
    auto* next = static_cast<Theme*>(user_data);
    auto from = current_theme->rules();
    auto to = next->rules();

    for (size_t i = 0; i < from.size(); ++i) {
        lv_obj_replace_style(obj, from[i].style, to[i].style, from[i].selector);
    }
    return LV_OBJ_TREE_WALK_NEXT;
}

static void toggle_theme(lv_event_t*) {
    Theme* next = (current_theme == day_theme) ? night_theme : day_theme;

    lv_display_set_theme(lv_display_get_default(), next->lv());
    lv_obj_tree_walk(lv_screen_active(), replace_theme_styles, next);

    current_theme = next;
    lv_obj_send_event(lv_screen_active(), EVENT_THEME_CHANGED, next);
}

static void on_theme_changed(lv_event_t*) {
    refresh_icons();
}

static void toggle_language(lv_event_t*) {
    lv_translation_set_language(is_arabic() ? "fr" : "ar");
}

static void on_language_changed(lv_event_t* e) {
    lv_obj_t* screen = lv_event_get_current_target_obj(e);

    if (is_arabic()) {
        lv_obj_set_style_base_dir(screen, LV_BASE_DIR_RTL, 0);
        lv_obj_set_style_text_font(screen, &lv_font_dejavu_16_persian_hebrew, 0);
    } else {
        lv_obj_set_style_base_dir(screen, LV_BASE_DIR_LTR, 0);
        lv_obj_remove_local_style_prop(screen, LV_STYLE_TEXT_FONT, 0);
    }

    refresh_icons();
}

static void on_return(lv_event_t*) {
}

static lv_obj_t* create_container(lv_obj_t* parent) {
    lv_obj_t* cont = lv_obj_create(parent);
    lv_obj_remove_style_all(cont);
    lv_obj_set_scrollable(cont, false);
    lv_obj_set_style_pad_all(cont, 4, 0);
    lv_obj_set_style_pad_gap(cont, 4, 0);
    return cont;
}

static lv_obj_t* create_text_button(lv_obj_t* parent, const char* tag) {
    lv_obj_t* btn = lv_button_create(parent);
    lv_obj_t* label = lv_label_create(btn);
    lv_label_set_translation_tag(label, tag);
    lv_obj_center(label);
    return btn;
}

static lv_obj_t* create_icon_button(lv_obj_t* parent, lv_obj_t** icon) {
    lv_obj_t* btn = lv_button_create(parent);
    *icon = lv_image_create(btn);
    lv_obj_center(*icon);
    return btn;
}

static void create_grid(lv_obj_t* parent) {
    static const int32_t col_dsc[] = {LV_GRID_FR(1), LV_GRID_FR(1), LV_GRID_TEMPLATE_LAST};
    static const int32_t row_dsc[] = {LV_GRID_FR(1), LV_GRID_FR(1), LV_GRID_FR(1), LV_GRID_TEMPLATE_LAST};

    lv_obj_t* grid = create_container(parent);
    lv_obj_set_height(grid, lv_pct(100));
    lv_obj_set_flex_grow(grid, 1);
    lv_obj_set_grid_dsc_array(grid, col_dsc, row_dsc);

    const char* tags[] = {tr::PHOTOS, tr::MUSIC, tr::VIDEOS, tr::FILES, tr::CONTACTS, tr::SETTINGS};
    for (int i = 0; i < 6; ++i) {
        lv_obj_t* btn = create_text_button(grid, tags[i]);
        lv_obj_set_grid_cell(btn,
            LV_GRID_ALIGN_STRETCH, i % 2, 1,
            LV_GRID_ALIGN_STRETCH, i / 2, 1);
    }
}

static void create_menu(lv_obj_t* parent) {
    lv_obj_t* menu = create_container(parent);
    lv_obj_set_size(menu, 35, lv_pct(100));
    lv_obj_set_style_pad_left(menu, 0, 0);
    lv_obj_set_flex_flow(menu, LV_FLEX_FLOW_COLUMN);

    lv_obj_t* theme_btn = create_icon_button(menu, &theme_icon);
    lv_obj_add_event_cb(theme_btn, toggle_theme, LV_EVENT_CLICKED, nullptr);

    lv_obj_t* lang_btn = create_text_button(menu, tr::LANG_SWITCH);
    lv_obj_add_event_cb(lang_btn, toggle_language, LV_EVENT_CLICKED, nullptr);

    lv_obj_t* return_btn = create_icon_button(menu, &return_icon);
    lv_obj_add_event_cb(return_btn, on_return, LV_EVENT_CLICKED, nullptr);

    for (lv_obj_t* btn : {theme_btn, lang_btn, return_btn}) {
        lv_obj_set_width(btn, lv_pct(100));
        lv_obj_set_flex_grow(btn, 1);
    }
}

int main() {
    lv_init();

    lv_sdl_window_create(320, 240);
    lv_sdl_mouse_create();

    register_translations();
    EVENT_THEME_CHANGED = static_cast<lv_event_code_t>(lv_event_register_id());

    static DayTheme day;
    static NightTheme night;
    day_theme = &day;
    night_theme = &night;
    current_theme = &day;
    lv_display_set_theme(lv_display_get_default(), current_theme->lv());

    lv_obj_t* screen = lv_screen_active();
    lv_obj_set_flex_flow(screen, LV_FLEX_FLOW_ROW);
    lv_obj_set_style_pad_all(screen, 0, 0);
    lv_obj_set_style_pad_gap(screen, 0, 0);
    lv_obj_set_scrollable(screen, false);
    lv_obj_add_event_cb(screen, on_language_changed, LV_EVENT_TRANSLATION_LANGUAGE_CHANGED, nullptr);
    lv_obj_add_event_cb(screen, on_theme_changed, EVENT_THEME_CHANGED, nullptr);

    create_grid(screen);
    create_menu(screen);

    lv_translation_set_language("fr");

    while (true) {
        lv_timer_handler();
        lv_sleep_ms(5);
    }
}
