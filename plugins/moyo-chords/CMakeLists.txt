cmake_minimum_required(VERSION 3.22)

project(MoyoChords VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(MOYO_BUILD_TESTS "Build the MOYO Chords test programs" OFF)

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

# An instrument that takes MIDI in and sends MIDI out: FL Studio loads it in the
# Channel Rack, where it can receive Piano Roll notes and feed other instruments.
juce_add_plugin(MoyoChords
    COMPANY_NAME            "Joe Moyo"
    BUNDLE_ID               "com.joemoyo.chords"
    PLUGIN_MANUFACTURER_CODE Jmoy
    PLUGIN_CODE             Mchd
    PRODUCT_NAME            "MOYO Chords"
    FORMATS                 ${MOYO_FORMATS}
    IS_SYNTH                TRUE
    NEEDS_MIDI_INPUT        TRUE
    NEEDS_MIDI_OUTPUT       TRUE
    IS_MIDI_EFFECT          FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    VST3_CATEGORIES         Instrument Generator
    AU_MAIN_TYPE            kAudioUnitType_MusicDevice
    COPY_PLUGIN_AFTER_BUILD FALSE)

set(MOYO_SOURCES
    Source/PluginProcessor.cpp
    Source/PluginEditor.cpp)

target_sources(MoyoChords PRIVATE ${MOYO_SOURCES})

# JUCE_VST3_EMULATE_MIDI_CC_WITH_PARAMETERS=0 stops JUCE adding ~2000 "MIDI CC" entries
# to the host's automation list.
target_compile_definitions(MoyoChords PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_VST3_EMULATE_MIDI_CC_WITH_PARAMETERS=0)

target_link_libraries(MoyoChords
    PRIVATE
        juce::juce_audio_utils
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags)

if(MOYO_BUILD_TESTS)
    # Pure C++ engine tests (theory, generator, voicing, rhythm).
    add_executable(MoyoChordsEngineTests Tests/engine_tests.cpp)
    target_include_directories(MoyoChordsEngineTests PRIVATE Source)

    # Plugin tests: real-time MIDI handling, state, MIDI export.
    juce_add_console_app(MoyoChordsPluginTests PRODUCT_NAME "MoyoChordsPluginTests")
    target_sources(MoyoChordsPluginTests PRIVATE Tests/plugin_tests.cpp ${MOYO_SOURCES})
    target_include_directories(MoyoChordsPluginTests PRIVATE Source)
    target_compile_definitions(MoyoChordsPluginTests PRIVATE
        JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_MODAL_LOOPS_PERMITTED=1 JucePlugin_Name="MOYO Chords")
    target_link_libraries(MoyoChordsPluginTests PRIVATE juce::juce_audio_utils)

    # Host test: loads the finished .vst3 the way a DAW does.
    juce_add_console_app(MoyoChordsHostTest PRODUCT_NAME "MoyoChordsHostTest")
    target_sources(MoyoChordsHostTest PRIVATE Tests/host_test.cpp)
    target_compile_definitions(MoyoChordsHostTest PRIVATE
        JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_PLUGINHOST_VST3=1)
    target_link_libraries(MoyoChordsHostTest PRIVATE juce::juce_audio_processors)
endif()
