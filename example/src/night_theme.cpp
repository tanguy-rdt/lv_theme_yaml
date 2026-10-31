#include "night_theme.h"

#include <array>

LV_IMAGE_DECLARE(icon_return_night);
LV_IMAGE_DECLARE(icon_return_night_ar);
LV_IMAGE_DECLARE(icon_paint_night);

namespace {

constexpr const lv_font_t* kFontBody  = &lv_font_montserrat_14;
constexpr const lv_font_t* kFontTitle = &lv_font_montserrat_20;

constexpr lv_color_t kScreenBg      = LV_COLOR_MAKE(15, 23, 42);
constexpr lv_color_t kText          = LV_COLOR_MAKE(226, 232, 240);
constexpr lv_color_t kButtonBg      = LV_COLOR_MAKE(30, 41, 59);
constexpr lv_color_t kButtonPressed = LV_COLOR_MAKE(51, 65, 85);
constexpr lv_color_t kButtonBorder  = LV_COLOR_MAKE(71, 85, 105);
constexpr lv_color_t kButtonText    = LV_COLOR_MAKE(226, 232, 240);

constexpr auto kScreenProps = std::to_array<lv_style_const_prop_t>({
    LV_STYLE_CONST_BG_COLOR(kScreenBg),
    LV_STYLE_CONST_BG_OPA(LV_OPA_COVER),
    LV_STYLE_CONST_TEXT_COLOR(kText),
    LV_STYLE_CONST_TEXT_FONT(kFontBody),
    LV_STYLE_CONST_PROPS_END,
});
constexpr LV_STYLE_CONST_INIT(kScreenStyle, kScreenProps.data());

constexpr auto kButtonProps = std::to_array<lv_style_const_prop_t>({
    LV_STYLE_CONST_BG_COLOR(kButtonBg),
    LV_STYLE_CONST_BG_OPA(LV_OPA_COVER),
    LV_STYLE_CONST_BORDER_COLOR(kButtonBorder),
    LV_STYLE_CONST_BORDER_WIDTH(1),
    LV_STYLE_CONST_RADIUS(8),
    LV_STYLE_CONST_TEXT_COLOR(kButtonText),
    LV_STYLE_CONST_PAD_TOP(4),
    LV_STYLE_CONST_PAD_BOTTOM(4),
    LV_STYLE_CONST_PAD_LEFT(4),
    LV_STYLE_CONST_PAD_RIGHT(4),
    LV_STYLE_CONST_PROPS_END,
});
constexpr LV_STYLE_CONST_INIT(kButtonStyle, kButtonProps.data());

constexpr auto kButtonPressedProps = std::to_array<lv_style_const_prop_t>({
    LV_STYLE_CONST_BG_COLOR(kButtonPressed),
    LV_STYLE_CONST_PROPS_END,
});
constexpr LV_STYLE_CONST_INIT(kButtonPressedStyle, kButtonPressedProps.data());

constexpr auto kButtonDisabledProps = std::to_array<lv_style_const_prop_t>({
    LV_STYLE_CONST_OPA(LV_OPA_50),
    LV_STYLE_CONST_PROPS_END,
});
constexpr LV_STYLE_CONST_INIT(kButtonDisabledStyle, kButtonDisabledProps.data());

constexpr std::array kImages{
    &icon_return_night,
    &icon_paint_night,
};
static_assert(kImages.size() == static_cast<size_t>(Icon::COUNT));

constexpr std::array kImagesRtl{
    rtl(Icon::RETURN, &icon_return_night_ar),
};

constexpr std::array kFonts{
    kFontBody,
    kFontTitle,
};
static_assert(kFonts.size() == static_cast<size_t>(Font::COUNT));

constexpr std::array kColors{
    kScreenBg,
    kText,
    kButtonBg,
    kButtonPressed,
    kButtonBorder,
    kButtonText,
};
static_assert(kColors.size() == static_cast<size_t>(Color::COUNT));

bool is_screen(lv_obj_t* obj) { return lv_obj_get_parent(obj) == nullptr; }

constexpr auto kRules = std::to_array<Rule>({
    {.sel = {.cls = &lv_obj_class, .match = is_screen}, .style = &kScreenStyle},
    {.sel = {.cls = &lv_button_class}, .style = &kButtonStyle},
    {.sel = {.cls = &lv_button_class}, .style = &kButtonPressedStyle, .selector = LV_STATE_PRESSED},
    {.sel = {.cls = &lv_button_class}, .style = &kButtonDisabledStyle, .selector = LV_STATE_DISABLED},
});

}

NightTheme::NightTheme() : Theme(kRules, kColors, kFonts, kImages, kImagesRtl) {}
