#ifndef TRANSLATIONS_H
#define TRANSLATIONS_H

#include <lvgl.h>

// Tags utilisés dans l'interface
namespace tr {
inline constexpr const char* PHOTOS      = "photos";
inline constexpr const char* MUSIC       = "music";
inline constexpr const char* VIDEOS      = "videos";
inline constexpr const char* FILES       = "files";
inline constexpr const char* CONTACTS    = "contacts";
inline constexpr const char* SETTINGS    = "settings";
inline constexpr const char* LANG_SWITCH = "lang_switch";   // affiche la langue vers laquelle on bascule
}

// Langues : la première sert de repli quand une traduction manque
inline const char* const kLanguages[] = {"fr", "ar", nullptr};

inline const char* const kTags[] = {
    tr::PHOTOS,
    tr::MUSIC,
    tr::VIDEOS,
    tr::FILES,
    tr::CONTACTS,
    tr::SETTINGS,
    tr::LANG_SWITCH,
    nullptr,
};

// Toutes les traductions de la première langue, puis toutes celles de la deuxième,
// dans l'ordre de kTags
inline const char* const kTranslations[] = {
    // fr
    "Photos",
    "Musique",
    "Vidéos",
    "Fichiers",
    "Contacts",
    "Réglages",
    "AR",
    // ar
    "صور",
    "موسيقى",
    "فيديو",
    "ملفات",
    "جهات الاتصال",
    "الإعدادات",
    "FR",
};

inline void register_translations() {
    lv_translation_add_static(kLanguages, kTags, kTranslations);
}

#endif //TRANSLATIONS_H
