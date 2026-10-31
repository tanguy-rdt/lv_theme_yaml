cmake_minimum_required(VERSION 3.31)

project(lv_theme_yaml_example
    DESCRIPTION  "lv_theme_yaml_example"
    LANGUAGES    C CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)

FetchContent_Declare(
    SDL2
    GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
    GIT_TAG release-2.32.4
)
FetchContent_MakeAvailable(SDL2)

set(LV_BUILD_USE_KCONFIG ON)
set(LV_BUILD_DEFCONFIG_PATH "${CMAKE_CURRENT_SOURCE_DIR}/configs/sdl2.defconfig")

FetchContent_Declare(
    lvgl
    GIT_REPOSITORY https://github.com/lvgl/lvgl.git
    GIT_TAG v9.6.0
)
FetchContent_MakeAvailable(lvgl)

target_link_libraries(lvgl PRIVATE SDL2::SDL2)

include(../cmake/lv_theme_yaml.cmake)

add_executable(lv_theme_yaml_example)

lv_theme_yaml_add(lv_theme_yaml_example
    COLORS theme/colors.yaml
    FONTS  theme/fonts.yaml
    THEMES
        theme/day.yaml
        theme/night.yaml
)

target_sources(lv_theme_yaml_example
    PRIVATE
        src/main.cpp
        src/day_theme.cpp
        src/night_theme.cpp
        icon/day/ar/return.c
        icon/day/fr/paint.c
        icon/day/fr/return.c
        icon/night/ar/return.c
        icon/night/fr/paint.c
        icon/night/fr/return.c
)

target_include_directories(lv_theme_yaml_example PRIVATE include)

target_link_libraries(lv_theme_yaml_example PRIVATE lvgl)
