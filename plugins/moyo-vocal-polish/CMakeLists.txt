cmake_minimum_required(VERSION 3.22)

project(MoyoVocalPolish VERSION 1.1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Universal binary on Mac (Apple Silicon + Intel)
if(APPLE)
    set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "" FORCE)
    set(CMAKE_OSX_DEPLOYMENT_TARGET "10.13" CACHE STRING "" FORCE)
endif()

# Use a local JUCE checkout if given (-DMOYO_JUCE_PATH=...), otherwise download it.
if(MOYO_JUCE_PATH)
    add_subdirectory(${MOYO_JUCE_PATH} juce EXCLUDE_FROM_ALL)
else()
    include(FetchContent)
    FetchContent_Declare(JUCE
        GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
        GIT_TAG        8.0.4
        GIT_SHALLOW    TRUE)
    FetchContent_MakeAvailable(JUCE)
endif()

set(MOYO_FORMATS VST3)
if(APPLE)
    list(APPEND MOYO_FORMATS AU)
endif()

juce_add_plugin(MoyoVocalPolish
    COMPANY_NAME            "Joe Moyo"
    COMPANY_WEBSITE         ""
    BUNDLE_ID               "com.joemoyo.vocalpolish"
    PLUGIN_MANUFACTURER_CODE Jmoy
    PLUGIN_CODE             Vxp1
    PRODUCT_NAME            "MOYO Vocal Polish"
    FORMATS                 ${MOYO_FORMATS}
    IS_SYNTH                FALSE
    NEEDS_MIDI_INPUT        FALSE
    NEEDS_MIDI_OUTPUT       FALSE
    IS_MIDI_EFFECT          FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    VST3_CATEGORIES         Fx Dynamics EQ
    AU_MAIN_TYPE            kAudioUnitType_Effect
    COPY_PLUGIN_AFTER_BUILD FALSE)

target_sources(MoyoVocalPolish PRIVATE
    Source/PluginProcessor.cpp
    Source/PluginEditor.cpp)

target_compile_definitions(MoyoVocalPolish PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0)

target_link_libraries(MoyoVocalPolish
    PRIVATE
        juce::juce_audio_utils
        juce::juce_dsp
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags)
