#include <lvgl.h>
#include <map>

namespace light_theme {
constexpr lv_style_const_prop_t kButtonProps[] = {
    LV_STYLE_CONST_BG_COLOR(LV_COLOR_MAKE(59, 130, 246)),
    LV_STYLE_CONST_BG_OPA(LV_OPA_COVER),
    LV_STYLE_CONST_BORDER_COLOR(LV_COLOR_MAKE(37, 99, 235)),
    LV_STYLE_CONST_BORDER_WIDTH(1),
    LV_STYLE_CONST_RADIUS(8),
    LV_STYLE_CONST_TEXT_COLOR(LV_COLOR_MAKE(241, 245, 249)),
    LV_STYLE_CONST_PROPS_END,
};
constexpr LV_STYLE_CONST_INIT(kButtonStyle, kButtonProps);

static void apply_cb(lv_theme_t*, lv_obj_t* obj) {
    if (lv_obj_has_class(obj, &lv_button_class)) {
        lv_obj_add_style(obj, &kButtonStyle, LV_PART_MAIN);
    }
}
}

namespace dark_theme {
constexpr lv_style_const_prop_t kButtonProps[] = {
    LV_STYLE_CONST_BG_COLOR(LV_COLOR_MAKE(59, 130, 0)),
    LV_STYLE_CONST_BG_OPA(LV_OPA_COVER),
    LV_STYLE_CONST_BORDER_COLOR(LV_COLOR_MAKE(37, 99, 235)),
    LV_STYLE_CONST_BORDER_WIDTH(1),
    LV_STYLE_CONST_RADIUS(8),
    LV_STYLE_CONST_TEXT_COLOR(LV_COLOR_MAKE(241, 245, 249)),
    LV_STYLE_CONST_PROPS_END,
};
constexpr LV_STYLE_CONST_INIT(kButtonStyle, kButtonProps);

static void apply_cb(lv_theme_t*, lv_obj_t* obj) {
    if (lv_obj_has_class(obj, &lv_button_class)) {
        lv_obj_add_style(obj, &kButtonStyle, LV_PART_MAIN);
    }
}
}

struct ThemeManager {
    enum class Theme {
        LIGHT,
        DARK,
    };

    Theme active_theme = Theme::LIGHT;
    std::map<Theme, lv_theme_t*> themes;

    ThemeManager() {
        themes[Theme::LIGHT] = lv_theme_create();
        lv_theme_set_apply_cb(themes[Theme::LIGHT], light_theme::apply_cb);

        themes[Theme::DARK] = lv_theme_create();
        lv_theme_set_apply_cb(themes[Theme::DARK], dark_theme::apply_cb);
    }

    void set_theme(Theme theme) {
        auto display = lv_display_get_default();
        lv_obj_remove_theme(lv_screen_active(), 0);
        lv_display_set_theme(display, themes[theme]);

        active_theme = theme;

        lv_obj_tree_walk(lv_display_get_screen_active(display),
        [](lv_obj_t* obj, void*) {
            lv_theme_apply(obj);
            return LV_OBJ_TREE_WALK_NEXT;
        },
        nullptr);
    }
};

static void button_cb(lv_event_t* e) {
    auto* theme_manager = static_cast<ThemeManager*>(lv_event_get_user_data(e));
    theme_manager->set_theme(theme_manager->active_theme == ThemeManager::Theme::LIGHT ?
        ThemeManager::Theme::DARK : ThemeManager::Theme::LIGHT);
}

int main() {
    lv_init();

    lv_sdl_window_create(320, 240);
    lv_sdl_mouse_create();

    ThemeManager theme_manager;
    theme_manager.set_theme(ThemeManager::Theme::LIGHT);

    lv_obj_t* button = lv_button_create(lv_screen_active());
    lv_obj_add_event_cb(button, button_cb, LV_EVENT_CLICKED, &theme_manager);
    lv_obj_center(button);

    lv_obj_t* label = lv_label_create(button);
    lv_label_set_text(label, "Toggle");
    lv_obj_center(label);

    while (true) {
        lv_timer_handler();
        lv_sleep_ms(5);
    }

    return 0;
}