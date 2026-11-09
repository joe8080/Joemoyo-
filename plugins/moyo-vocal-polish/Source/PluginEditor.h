#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"

namespace moyo
{
struct Colours
{
    static inline const juce::Colour bg      { 0xff050505 };
    static inline const juce::Colour panel   { 0xff121412 };
    static inline const juce::Colour track   { 0xff262a24 };
    static inline const juce::Colour lime    { 0xffa6ff00 };
    static inline const juce::Colour limeDim { 0xff5c8a0a };
    static inline const juce::Colour text    { 0xfff1f5ec };
    static inline const juce::Colour subtext { 0xff8d9688 };
    static inline const juce::Colour warn    { 0xffff4d4d };
};

class LookAndFeel : public juce::LookAndFeel_V4
{
public:
    LookAndFeel();
    void drawRotarySlider (juce::Graphics&, int x, int y, int w, int h, float pos,
                           float startAngle, float endAngle, juce::Slider&) override;
    juce::Label* createSliderTextBox (juce::Slider&) override;
    void drawButtonBackground (juce::Graphics&, juce::Button&, const juce::Colour&, bool over, bool down) override;
    void drawButtonText (juce::Graphics&, juce::TextButton&, bool over, bool down) override;
};

// Vertical bar meter with a dB readout on top.
class Meter : public juce::Component, public juce::SettableTooltipClient
{
public:
    Meter (juce::String name, float maxDb, bool isReduction);
    void setValueDb (float db);
    void paint (juce::Graphics&) override;

private:
    juce::String title;
    float range, shown = 0.0f, readout = 0.0f, hold = 0.0f;
    int holdFrames = 0;
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
    using ButtonAttachment = juce::AudioProcessorValueTreeState::ButtonAttachment;

    void timerCallback() override;
    void setupKnob (Knob&, const juce::String& paramId, const juce::String& title, const juce::String& tip);
    void setupToggle (juce::TextButton&, const juce::String& text, const juce::String& tip);
    void refreshSlotButtons();

    MoyoVocalPolishProcessor& processor;
    moyo::LookAndFeel lnf;

    Knob polish, warmth, air, deess, input, mix, output;
    juce::ComboBox presetBox;

    juce::TextButton slotA { "A" }, slotB { "B" }, copySlot { "COPY" };
    juce::TextButton hearOriginal { "HEAR ORIGINAL" }, autoGain { "AUTO GAIN" }, clipGuard { "CLIP GUARD" };
    std::unique_ptr<ButtonAttachment> originalAtt, autoGainAtt, clipGuardAtt;

    moyo::Meter inMeter    { "IN", 60.0f, false },
                compMeter  { "COMP", 18.0f, true },
                deessMeter { "DE-ESS", 14.0f, true },
                outMeter   { "OUT", 60.0f, false };
    juce::Label autoGainReadout;

    juce::TooltipWindow tooltips { this, 600 };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MoyoVocalPolishEditor)
};
