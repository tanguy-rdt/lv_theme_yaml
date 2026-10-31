#ifndef THEME_H
#define THEME_H

#include <lvgl.h>

#include <span>
#include <string_view>

struct RTLImage {
    int id;
    const lv_image_dsc_t* dsc;
};

template <typename E>
constexpr RTLImage rtl(E e, const lv_image_dsc_t* dsc) {
    return {static_cast<int>(e), dsc};
}

struct Selector {
    const lv_obj_class_t* cls      = nullptr;
    const lv_obj_class_t* parent   = nullptr;
    const lv_obj_class_t* ancestor = nullptr;
    bool (*match)(lv_obj_t*)       = nullptr;
};

struct Rule {
    Selector sel;
    const lv_style_t* style = nullptr;
    lv_style_selector_t selector = LV_PART_MAIN;
};

class Theme {
    public:
        Theme(const Theme&) = delete;
        Theme& operator=(const Theme&) = delete;
        virtual ~Theme() { lv_theme_delete(_theme); }

        lv_theme_t* lv() const { return _theme; }
        std::span<const Rule> rules() const { return _rules; }

        template <typename E>
        lv_color_t color(E e) const {
            auto i = static_cast<size_t>(e);
            return i < _colors.size() ? _colors[i] : lv_color_black();
        }

        template <typename E>
        const lv_font_t* font(E e) const {
            auto i = static_cast<size_t>(e);
            return i < _fonts.size() ? _fonts[i] : nullptr;
        }

        template <typename E>
        const lv_image_dsc_t* image(E e) const {
            const int id = static_cast<int>(e);

            if (is_rtl()) {
                for (const RTLImage& r : _images_rtl) {
                    if (r.id == id) return r.dsc;
                }
            }

            return static_cast<size_t>(id) < _images.size() ? _images[id] : nullptr;
        }

    protected:
        Theme(std::span<const Rule> rules,
              std::span<const lv_color_t> colors,
              std::span<const lv_font_t* const> fonts,
              std::span<const lv_image_dsc_t* const> images,
              std::span<const RTLImage> images_rtl = {})
            : _rules(rules),
              _colors(colors),
              _fonts(fonts),
              _images(images),
              _images_rtl(images_rtl) {
            _theme = lv_theme_create();
            lv_theme_set_user_data(_theme, this);
            lv_theme_set_apply_cb(_theme, apply_cb);
        }

    private:
        static void apply_cb(lv_theme_t* th, lv_obj_t* obj) {
            auto* self = static_cast<Theme*>(lv_theme_get_user_data(th));
            for (const Rule& r : self->_rules) {
                if (matches(r.sel, obj)) {
                    lv_obj_add_style(obj, r.style, r.selector);
                }
            }
        }

        static bool matches(const Selector& s, lv_obj_t* obj) {
            if (s.cls && !lv_obj_check_type(obj, s.cls)) return false;

            lv_obj_t* parent = lv_obj_get_parent(obj);
            if (s.parent && !(parent && lv_obj_check_type(parent, s.parent))) return false;

            if (s.ancestor) {
                lv_obj_t* p = parent;
                while (p && !lv_obj_check_type(p, s.ancestor)) p = lv_obj_get_parent(p);
                if (!p) return false;
            }

            if (s.match && !s.match(obj)) return false;
            return true;
        }

        static bool is_rtl() {
            const char* lang = lv_translation_get_language();
            return lang && std::string_view(lang) == "ar";
        }

        lv_theme_t* _theme;
        std::span<const Rule> _rules;
        std::span<const lv_color_t> _colors;
        std::span<const lv_font_t* const> _fonts;
        std::span<const lv_image_dsc_t* const> _images;
        std::span<const RTLImage> _images_rtl;
};

#endif //THEME_H
