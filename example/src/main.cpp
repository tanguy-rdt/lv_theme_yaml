#include <lvgl.h>

#include <array>
#include <cstdint>
#include <string_view>

#include "day_theme.h"
#include "night_theme.h"
#include "theme_fonts.h"

constexpr auto kLanguages = std::to_array<const char*>({"fr", "ar", nullptr});

constexpr auto kTags = std::to_array<const char*>({
    "app_title",
    "lang_switch",
    "nav_section",
    "nav_dashboard",
    "nav_settings",
    "nav_apps",
    "nav_about",
    "cpu",
    "storage",
    "battery",
    "network",
    "online",
    "wifi",
    "bluetooth",
    "airplane",
    "notifications",
    "volume",
    "theme",
    "theme_options",
    "photos",
    "music",
    "videos",
    "files",
    "contacts",
    "tools",
    "about_text",
    "version",
    nullptr,
});

constexpr auto kTranslations = std::to_array<const char*>({
    "Demo LVGL", "عرض LVGL",
    "AR", "FR",
    "Menu", "القائمة",
    "Accueil", "الرئيسية",
    "Options", "الإعدادات",
    "Applications", "التطبيقات",
    "Infos", "حول",
    "Processeur", "المعالج",
    "Stockage", "التخزين",
    "Batterie", "البطارية",
    "Connexion", "الاتصال",
    "En ligne", "متصل",
    "Wi-Fi", "واي فاي",
    "Bluetooth", "بلوتوث",
    "Mode avion", "وضع الطيران",
    "Notifications", "الإشعارات",
    "Volume", "مستوى الصوت",
    "Apparence", "المظهر",
    "Jour\nNuit", "نهار\nليل",
    "Photos", "صور",
    "Musique", "موسيقى",
    "Films", "أفلام",
    "Fichiers", "ملفات",
    "Contacts", "جهات الاتصال",
    "Outils", "أدوات",
    "Exemple lv_theme_yaml", "مثال lv_theme_yaml",
    "Version 1.0", "الإصدار 1.0",
});

static_assert(kTranslations.size() == (kTags.size() - 1) * (kLanguages.size() - 1));

constexpr auto kDashboardColumns = std::to_array<int32_t>({LV_GRID_FR(1), LV_GRID_FR(1), LV_GRID_TEMPLATE_LAST});
constexpr auto kDashboardRows = std::to_array<int32_t>({LV_GRID_FR(1), LV_GRID_FR(1), LV_GRID_TEMPLATE_LAST});
constexpr auto kAppsColumns = std::to_array<int32_t>({LV_GRID_FR(1), LV_GRID_FR(1), LV_GRID_FR(1), LV_GRID_TEMPLATE_LAST});
constexpr auto kAppsRows = std::to_array<int32_t>({LV_GRID_FR(1), LV_GRID_FR(1), LV_GRID_TEMPLATE_LAST});

constexpr auto kAppTags = std::to_array<const char*>({"photos", "music", "videos", "files", "contacts", "tools"});

constexpr int kPageCount = 4;

static Theme* day_theme;
static Theme* night_theme;
static Theme* current_theme;

static lv_event_code_t EVENT_THEME_CHANGED;

static lv_obj_t* screen;
static lv_obj_t* title_label;
static lv_obj_t* theme_icon;
static lv_obj_t* return_icon;
static lv_obj_t* theme_dropdown;
static lv_obj_t* notifications_checkbox;
static lv_obj_t* cpu_arc;
static lv_obj_t* cpu_label;
static lv_obj_t* volume_label;

static std::array<lv_obj_t*, kPageCount> pages;
static std::array<lv_obj_t*, kPageCount> nav_buttons;

static bool is_arabic() {
    const char* lang = lv_translation_get_language();
    return lang && std::string_view(lang) == "ar";
}

static void switch_theme(Theme* next) {
    if (next == current_theme) {
        return;
    }
    if (current_theme->rules().size() != next->rules().size()) {
        LV_LOG_ERROR("themes must have the same rule layout to be switched");
        return;
    }

    lv_display_replace_theme(nullptr, next->lv());

    current_theme = next;
    lv_obj_send_event(screen, EVENT_THEME_CHANGED, next);
}

static void refresh_icons() {
    lv_image_set_src(theme_icon, current_theme->image(Icon::PAINT));
    lv_image_set_src(return_icon, current_theme->image(Icon::RETURN));
}

static void show_page(int index) {
    for (int i = 0; i < kPageCount; ++i) {
        lv_obj_set_hidden(pages[i], i != index);
        lv_obj_set_state(nav_buttons[i], LV_STATE_CHECKED, i == index);
    }
}

static void on_theme_changed(lv_event_t*) {
    refresh_icons();
    lv_dropdown_set_selected(theme_dropdown, current_theme == night_theme ? 1 : 0);
}

static void on_language_changed(lv_event_t*) {
    if (is_arabic()) {
        lv_obj_set_style_base_dir(screen, LV_BASE_DIR_RTL, 0);
        lv_obj_set_style_text_font(screen, theme_fonts::arabic, 0);
        lv_obj_set_style_text_font(title_label, theme_fonts::arabic, 0);
    } else {
        lv_obj_set_style_base_dir(screen, LV_BASE_DIR_LTR, 0);
        lv_obj_remove_local_style_prop(screen, LV_STYLE_TEXT_FONT, 0);
        lv_obj_set_style_text_font(title_label, theme_fonts::title, 0);
    }

    lv_checkbox_set_text(notifications_checkbox, lv_tr("notifications"));
    refresh_icons();
}

static void on_theme_button(lv_event_t*) {
    switch_theme(current_theme == day_theme ? night_theme : day_theme);
}

static void on_language_button(lv_event_t*) {
    lv_translation_set_language(is_arabic() ? "fr" : "ar");
}

static void on_return_button(lv_event_t*) {
    show_page(0);
}

static void on_nav_clicked(lv_event_t* e) {
    show_page(static_cast<int>(reinterpret_cast<intptr_t>(lv_event_get_user_data(e))));
}

static void on_theme_selected(lv_event_t* e) {
    auto* dropdown = lv_event_get_target_obj(e);
    switch_theme(lv_dropdown_get_selected(dropdown) == 1 ? night_theme : day_theme);
}

static void on_volume_changed(lv_event_t* e) {
    auto* slider = lv_event_get_target_obj(e);
    lv_label_set_text_fmt(volume_label, "%d %%", static_cast<int>(lv_slider_get_value(slider)));
}

static void on_cpu_timer(lv_timer_t*) {
    int32_t value = static_cast<int32_t>(lv_rand(20, 95));
    lv_arc_set_value(cpu_arc, value);
    lv_label_set_text_fmt(cpu_label, "%d %%", static_cast<int>(value));
}

static lv_obj_t* create_layout(lv_obj_t* parent, lv_flex_flow_t flow) {
    lv_obj_t* cont = lv_obj_create(parent);
    lv_obj_remove_style_all(cont);
    lv_obj_set_scrollable(cont, false);
    lv_obj_set_flex_flow(cont, flow);
    lv_obj_set_style_pad_gap(cont, 8, 0);
    return cont;
}

static lv_obj_t* create_label(lv_obj_t* parent, const char* tag) {
    lv_obj_t* label = lv_label_create(parent);
    lv_label_set_translation_tag(label, tag);
    return label;
}

static lv_obj_t* create_text_button(lv_obj_t* parent, const char* tag) {
    lv_obj_t* btn = lv_button_create(parent);
    lv_obj_t* label = create_label(btn, tag);
    lv_obj_center(label);
    return btn;
}

static lv_obj_t* create_icon_button(lv_obj_t* parent, lv_obj_t** icon) {
    lv_obj_t* btn = lv_button_create(parent);
    lv_obj_set_style_bg_color(btn, lv_color_make(255, 0, 0), 0);
    *icon = lv_image_create(btn);
    lv_obj_center(*icon);
    return btn;
}

static lv_obj_t* create_card(lv_obj_t* parent, const char* title_tag) {
    lv_obj_t* card = lv_obj_create(parent);
    lv_obj_set_scrollable(card, false);
    lv_obj_set_flex_flow(card, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(card, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    create_label(card, title_tag);
    return card;
}

static lv_obj_t* create_setting_row(lv_obj_t* parent, const char* tag) {
    lv_obj_t* row = create_layout(parent, LV_FLEX_FLOW_ROW);
    lv_obj_set_size(row, lv_pct(100), LV_SIZE_CONTENT);
    lv_obj_set_flex_align(row, LV_FLEX_ALIGN_SPACE_BETWEEN, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    create_label(row, tag);
    return row;
}

static lv_obj_t* create_page(lv_obj_t* parent) {
    lv_obj_t* page = create_layout(parent, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_size(page, lv_pct(100), lv_pct(100));
    return page;
}

static void create_header(lv_obj_t* parent) {
    lv_obj_t* header = lv_obj_create(parent);
    lv_obj_set_scrollable(header, false);
    lv_obj_set_size(header, lv_pct(100), LV_SIZE_CONTENT);
    lv_obj_set_flex_flow(header, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(header, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);

    title_label = create_label(header, "app_title");
    lv_obj_set_flex_grow(title_label, 1);

    lv_obj_t* lang_btn = create_text_button(header, "lang_switch");
    lv_obj_add_event_cb(lang_btn, on_language_button, LV_EVENT_CLICKED, nullptr);

    lv_obj_t* theme_btn = create_icon_button(header, &theme_icon);
    lv_obj_add_event_cb(theme_btn, on_theme_button, LV_EVENT_CLICKED, nullptr);

    lv_obj_t* return_btn = create_icon_button(header, &return_icon);
    lv_obj_add_event_cb(return_btn, on_return_button, LV_EVENT_CLICKED, nullptr);
}

static lv_obj_t* create_nav_button(lv_obj_t* parent, const char* icon, const char* tag) {
    lv_obj_t* btn = lv_button_create(parent);
    lv_obj_set_width(btn, lv_pct(100));
    lv_obj_set_flex_flow(btn, LV_FLEX_FLOW_ROW);
    lv_obj_set_flex_align(btn, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_gap(btn, 10, 0);

    lv_obj_t* icon_label = lv_label_create(btn);
    lv_label_set_text(icon_label, icon);
    create_label(btn, tag);
    return btn;
}

static void create_nav(lv_obj_t* parent) {
    lv_obj_t* nav = lv_obj_create(parent);
    lv_obj_set_size(nav, 200, lv_pct(100));
    lv_obj_set_flex_flow(nav, LV_FLEX_FLOW_COLUMN);

    create_label(nav, "nav_section");

    constexpr auto icons = std::to_array<const char*>({
        LV_SYMBOL_HOME, LV_SYMBOL_SETTINGS, LV_SYMBOL_LIST, LV_SYMBOL_FILE,
    });
    constexpr auto tags = std::to_array<const char*>({
        "nav_dashboard", "nav_settings", "nav_apps", "nav_about",
    });

    for (int i = 0; i < kPageCount; ++i) {
        nav_buttons[i] = create_nav_button(nav, icons[i], tags[i]);
        lv_obj_add_event_cb(nav_buttons[i], on_nav_clicked, LV_EVENT_CLICKED,
                            reinterpret_cast<void*>(static_cast<intptr_t>(i)));
    }
}

static lv_obj_t* create_dashboard_page(lv_obj_t* parent) {
    lv_obj_t* page = create_page(parent);
    lv_obj_set_layout(page, LV_LAYOUT_GRID);
    lv_obj_set_grid_dsc_array(page, kDashboardColumns.data(), kDashboardRows.data());

    lv_obj_t* cpu = create_card(page, "cpu");
    lv_obj_set_grid_cell(cpu, LV_GRID_ALIGN_STRETCH, 0, 1, LV_GRID_ALIGN_STRETCH, 0, 1);
    cpu_arc = lv_arc_create(cpu);
    lv_obj_set_size(cpu_arc, 110, 110);
    lv_obj_set_clickable(cpu_arc, false);
    lv_arc_set_value(cpu_arc, 62);
    cpu_label = lv_label_create(cpu_arc);
    lv_obj_set_style_text_font(cpu_label, theme_fonts::big, 0);
    lv_label_set_text(cpu_label, "62 %");
    lv_obj_center(cpu_label);

    lv_obj_t* storage = create_card(page, "storage");
    lv_obj_set_grid_cell(storage, LV_GRID_ALIGN_STRETCH, 1, 1, LV_GRID_ALIGN_STRETCH, 0, 1);
    lv_obj_t* storage_bar = lv_bar_create(storage);
    lv_obj_set_size(storage_bar, lv_pct(100), 14);
    lv_bar_set_value(storage_bar, 45, LV_ANIM_OFF);
    lv_obj_t* storage_value = lv_label_create(storage);
    lv_obj_set_style_text_font(storage_value, theme_fonts::big, 0);
    lv_label_set_text(storage_value, "45 %");

    lv_obj_t* battery = create_card(page, "battery");
    lv_obj_set_grid_cell(battery, LV_GRID_ALIGN_STRETCH, 0, 1, LV_GRID_ALIGN_STRETCH, 1, 1);
    lv_obj_t* battery_bar = lv_bar_create(battery);
    lv_obj_set_size(battery_bar, lv_pct(100), 14);
    lv_bar_set_value(battery_bar, 80, LV_ANIM_OFF);
    lv_obj_t* battery_value = lv_label_create(battery);
    lv_obj_set_style_text_font(battery_value, theme_fonts::big, 0);
    lv_label_set_text(battery_value, "80 %");

    lv_obj_t* network = create_card(page, "network");
    lv_obj_set_grid_cell(network, LV_GRID_ALIGN_STRETCH, 1, 1, LV_GRID_ALIGN_STRETCH, 1, 1);
    lv_obj_t* spinner = lv_spinner_create(network);
    lv_obj_set_size(spinner, 60, 60);
    create_label(network, "online");

    lv_timer_create(on_cpu_timer, 1500, nullptr);
    return page;
}

static lv_obj_t* create_settings_page(lv_obj_t* parent) {
    lv_obj_t* page = create_page(parent);

    lv_obj_t* wifi = lv_switch_create(create_setting_row(page, "wifi"));
    lv_obj_set_state(wifi, LV_STATE_CHECKED, true);

    lv_switch_create(create_setting_row(page, "bluetooth"));
    lv_switch_create(create_setting_row(page, "airplane"));

    notifications_checkbox = lv_checkbox_create(page);
    lv_obj_set_state(notifications_checkbox, LV_STATE_CHECKED, true);

    lv_obj_t* volume_row = create_setting_row(page, "volume");
    lv_obj_t* volume_controls = create_layout(volume_row, LV_FLEX_FLOW_ROW);
    lv_obj_set_size(volume_controls, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
    lv_obj_set_flex_align(volume_controls, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_gap(volume_controls, 16, 0);
    lv_obj_t* slider = lv_slider_create(volume_controls);
    lv_obj_set_width(slider, 180);
    lv_slider_set_value(slider, 70, LV_ANIM_OFF);
    lv_obj_add_event_cb(slider, on_volume_changed, LV_EVENT_VALUE_CHANGED, nullptr);
    volume_label = lv_label_create(volume_controls);
    lv_label_set_text(volume_label, "70 %");

    lv_obj_t* theme_row = create_setting_row(page, "theme");
    theme_dropdown = lv_dropdown_create(theme_row);
    lv_obj_set_width(theme_dropdown, 140);
    lv_dropdown_set_options_translation_tag(theme_dropdown, "theme_options");
    lv_obj_add_event_cb(theme_dropdown, on_theme_selected, LV_EVENT_VALUE_CHANGED, nullptr);

    return page;
}

static lv_obj_t* create_apps_page(lv_obj_t* parent) {
    lv_obj_t* page = create_page(parent);
    lv_obj_set_layout(page, LV_LAYOUT_GRID);
    lv_obj_set_grid_dsc_array(page, kAppsColumns.data(), kAppsRows.data());

    for (int i = 0; i < static_cast<int>(kAppTags.size()); ++i) {
        lv_obj_t* btn = create_text_button(page, kAppTags[i]);
        lv_obj_set_grid_cell(btn,
            LV_GRID_ALIGN_STRETCH, i % 3, 1,
            LV_GRID_ALIGN_STRETCH, i / 3, 1);
    }
    return page;
}

static lv_obj_t* create_about_page(lv_obj_t* parent) {
    lv_obj_t* page = create_page(parent);
    lv_obj_set_flex_align(page, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);

    lv_obj_t* name = create_label(page, "app_title");
    lv_obj_set_style_text_font(name, theme_fonts::big, 0);

    create_label(page, "about_text");
    create_label(page, "version");

    lv_obj_t* spinner = lv_spinner_create(page);
    lv_obj_set_size(spinner, 40, 40);
    return page;
}

static void create_ui() {
    lv_obj_set_flex_flow(screen, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_scrollable(screen, false);

    create_header(screen);

    lv_obj_t* body = create_layout(screen, LV_FLEX_FLOW_ROW);
    lv_obj_set_width(body, lv_pct(100));
    lv_obj_set_flex_grow(body, 1);

    create_nav(body);

    lv_obj_t* content = lv_obj_create(body);
    lv_obj_set_scrollable(content, false);
    lv_obj_set_height(content, lv_pct(100));
    lv_obj_set_flex_grow(content, 1);

    pages[0] = create_dashboard_page(content);
    pages[1] = create_settings_page(content);
    pages[2] = create_apps_page(content);
    pages[3] = create_about_page(content);
}

int main() {
    lv_init();

    lv_sdl_window_create(800, 480);
    lv_sdl_mouse_create();

    EVENT_THEME_CHANGED = static_cast<lv_event_code_t>(lv_event_register_id());
    lv_translation_add_static(kLanguages.data(), kTags.data(), kTranslations.data());
    lv_translation_set_language("fr");

    static DayTheme day;
    static NightTheme night;
    day_theme = &day;
    night_theme = &night;
    current_theme = &day;
    lv_display_set_theme(lv_display_get_default(), current_theme->lv());
    lv_theme_apply(lv_screen_active());

    screen = lv_screen_active();
    create_ui();

    lv_obj_add_event_cb(screen, on_language_changed, LV_EVENT_TRANSLATION_LANGUAGE_CHANGED, nullptr);
    lv_obj_add_event_cb(screen, on_theme_changed, EVENT_THEME_CHANGED, nullptr);

    on_language_changed(nullptr);
    show_page(0);

    while (true) {
        lv_timer_handler();
        lv_sleep_ms(5);
    }
}
