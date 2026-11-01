include(FetchContent)

find_package(SDL2 QUIET)

if(NOT SDL2_FOUND)
    message(STATUS "SDL2 : not found, downloading sources...")

    FetchContent_Declare(
        SDL2
        GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
        GIT_TAG release-2.32.10
    )
    FetchContent_MakeAvailable(SDL2)
endif()

set(LV_BUILD_USE_KCONFIG ON)
set(LV_BUILD_DEFCONFIG_PATH "${PROJECT_SOURCE_DIR}/configs/example.defconfig")

find_package(lvgl_src QUIET)

if(LVGL_SOURCE_DIR)
    add_subdirectory(${LVGL_SOURCE_DIR} ${CMAKE_BINARY_DIR}/lvgl)
else()
    message(STATUS "LVGL : not found, downloading sources...")

    FetchContent_Declare(
        lvgl
        GIT_REPOSITORY https://github.com/lvgl/lvgl.git
        GIT_TAG v9.6.0
    )
    FetchContent_MakeAvailable(lvgl)
endif()

target_link_libraries(lvgl PRIVATE SDL2::SDL2)