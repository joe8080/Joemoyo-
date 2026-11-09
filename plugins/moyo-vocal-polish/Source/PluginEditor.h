#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"

namespace moyo
{
struct Colours
{
    static inline const juce::Colour bg      { 0xff121216 };
    static inline const juce::Colour panel   { 0xff1c1c22 };
    static inline const juce::Colour track   { 0xff34343d };
    static inline const juce::Colour gold    { 0xffe8b04b };
    static inline const juce::Colour text    { 0xfff2efe8 };
    static inline const juce::Colour subtext { 0xff9a978f };
};

class LookAndFeel : public juce::LookAndFeel_V4
{
public:
    LookAndFeel();
    void drawRotarySlider (juce::Graphics&, int x, int y, int w, int h, float pos,
                           float startAngle, float endAngle, juce::Slider&) override;
    juce::Label* createSliderTextBox (juce::Slider&) override;
};

// Vertical bar meter. Shows gain reduction (fills downward-meaning "how much
// is being taken off") or level, depending on how it is fed.
class Meter : public juce::Component, public juce::SettableTooltipClient
{
public:
    Meter (juce::String name, float maxDb, bool isReduction);
    void setValueDb (float db);
    void paint (juce::Graphics&) override;

private:
    juce::String title;
    float range, shown = 0.0f;
    bool reduction;
};
} // namespace moyo

class MoyoVocalPolishEditor : public juce::AudioProcessorEditor, private juce::Timer
{
public:
    explicit MoyoVocalPolishEditor (MoyoVocalPolishProcessor&);
    ~MoyoVocalPolishEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    struct Knob
    {
        juce::Slider slider;
        juce::Label label;
        std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> attachment;
    };

    void timerCallback() override;
    void setupKnob (Knob&, const juce::String& paramId, const juce::String& title, const juce::String& tip);

    MoyoVocalPolishProcessor& processor;
    moyo::LookAndFeel lnf;

    Knob polish, warmth, air, deess, mix, output;
    juce::ComboBox presetBox;
    moyo::Meter compMeter { "COMP", 18.0f, true }, deessMeter { "DE-ESS", 14.0f, true }, outMeter { "OUT", 48.0f, false };
    juce::TooltipWindow tooltips { this, 600 };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MoyoVocalPolishEditor)
};
