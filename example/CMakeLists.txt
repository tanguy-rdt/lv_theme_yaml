cmake_minimum_required(VERSION 3.31)

project(lv_theme_yaml_example
    DESCRIPTION  "lv_theme_yaml_example"
    LANGUAGES    C CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(dependencies.cmake)
include(../cmake/lv_theme_yaml.cmake)

add_executable(lv_theme_yaml_example)

set(Python3_EXECUTABLE "${PROJECT_SOURCE_DIR}/../.venv/bin/python" CACHE FILEPATH "Python interpreter")

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
)

target_include_directories(lv_theme_yaml_example PRIVATE include)

target_link_libraries(lv_theme_yaml_example PRIVATE lvgl)
