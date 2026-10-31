# lv_theme_yaml_add(<target>
#     COLORS <colors.yaml>
#     FONTS  <fonts.yaml>
#     THEMES <theme.yaml>...
#     [LVGL_DIR <lvgl source dir>]   # default: ${lvgl_SOURCE_DIR}
#     [IMAGE_CF <format>]            # default: ARGB8888
#     [OUTPUT_DIR <dir>])            # default: ${CMAKE_CURRENT_BINARY_DIR}/<target>_theme_gen
#
# Generates the theme sources from the YAML files at build time, adds them to <target>
# and adds the output directory to its include paths.

include_guard(GLOBAL)

set(_LV_THEME_YAML_SCRIPT "${CMAKE_CURRENT_LIST_DIR}/../scripts/gen_theme.py")

function(lv_theme_yaml_add target)
    cmake_parse_arguments(PARSE_ARGV 1 ARG "" "COLORS;FONTS;LVGL_DIR;IMAGE_CF;OUTPUT_DIR" "THEMES")

    if(ARG_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR "lv_theme_yaml_add: unknown arguments: ${ARG_UNPARSED_ARGUMENTS}")
    endif()
    if(NOT TARGET ${target})
        message(FATAL_ERROR "lv_theme_yaml_add: '${target}' is not a target")
    endif()
    foreach(required COLORS FONTS THEMES)
        if(NOT ARG_${required})
            message(FATAL_ERROR "lv_theme_yaml_add: ${required} is required")
        endif()
    endforeach()

    if(NOT ARG_LVGL_DIR)
        if(NOT lvgl_SOURCE_DIR)
            message(FATAL_ERROR "lv_theme_yaml_add: LVGL_DIR not given and lvgl_SOURCE_DIR is not set")
        endif()
        set(ARG_LVGL_DIR "${lvgl_SOURCE_DIR}")
    endif()
    if(NOT ARG_IMAGE_CF)
        set(ARG_IMAGE_CF ARGB8888)
    endif()
    if(NOT ARG_OUTPUT_DIR)
        set(ARG_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/${target}_theme_gen")
    endif()

    find_package(Python3 COMPONENTS Interpreter REQUIRED)

    set(args
        --colors "${ARG_COLORS}"
        --fonts "${ARG_FONTS}"
        -o "${ARG_OUTPUT_DIR}"
        --lvgl-dir "${ARG_LVGL_DIR}"
        --cf "${ARG_IMAGE_CF}")
    foreach(theme IN LISTS ARG_THEMES)
        list(APPEND args --theme "${theme}")
    endforeach()

    foreach(mode inputs outputs)
        execute_process(
            COMMAND "${Python3_EXECUTABLE}" "${_LV_THEME_YAML_SCRIPT}" ${args} --list-${mode}
            WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
            OUTPUT_VARIABLE list
            ERROR_VARIABLE error
            RESULT_VARIABLE result
            OUTPUT_STRIP_TRAILING_WHITESPACE)
        if(NOT result EQUAL 0)
            message(FATAL_ERROR "lv_theme_yaml_add(${target}): theme generation failed:\n${error}")
        endif()
        string(REPLACE "\n" ";" list "${list}")
        set(${mode} ${list})
    endforeach()

    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${inputs} "${_LV_THEME_YAML_SCRIPT}")

    set(stamp "${ARG_OUTPUT_DIR}/.stamp")
    add_custom_command(
        OUTPUT "${stamp}"
        BYPRODUCTS ${outputs}
        COMMAND "${Python3_EXECUTABLE}" "${_LV_THEME_YAML_SCRIPT}" ${args} --stamp "${stamp}"
        WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
        DEPENDS ${inputs} "${_LV_THEME_YAML_SCRIPT}"
        COMMENT "Generating LVGL themes for ${target}"
        VERBATIM)
    add_custom_target(${target}_theme_gen DEPENDS "${stamp}")

    target_sources(${target} PRIVATE ${outputs})
    target_include_directories(${target} PRIVATE "${ARG_OUTPUT_DIR}")
    add_dependencies(${target} ${target}_theme_gen)
endfunction()
