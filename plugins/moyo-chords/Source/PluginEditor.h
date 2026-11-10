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
    juce::Font getComboBoxFont (juce::ComboBox&) override;
};

// One chord in the progression. Click to hear and select it; the strip at the
// bottom locks it or rolls a new chord in its place.
class ChordCard : public juce::Component, public juce::SettableTooltipClient
{
public:
    std::function<void()> onSelect, onLock, onRoll;

    void setData (const juce::String& chordName, const juce::String& roman, const juce::String& lengthText,
                  bool isLocked, bool isSelected, bool isPlaying);
    void paint (juce::Graphics&) override;
    void mouseUp (const juce::MouseEvent&) override;

private:
    juce::String name, numeral, length;
    bool locked = false, selected = false, playing = false;
};

// Shows which notes are sounding.
class KeyboardDisplay : public juce::Component
{
public:
    void setNotes (juce::uint64 low, juce::uint64 high);
    void paint (juce::Graphics&) override;

private:
    bool isLit (int note) const { return note < 64 ? ((lo >> note) & 1) != 0 : ((hi >> (note - 64)) & 1) != 0; }
    juce::uint64 lo = 0, hi = 0;
    static constexpr int firstNote = 24, lastNote = 96;
};

// Drag from here into the DAW to drop the progression as a MIDI clip.
class DragZone : public juce::Component, public juce::SettableTooltipClient
{
public:
    std::function<juce::File()> makeFile;
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override { dragging = false; }
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseEnter (const juce::MouseEvent&) override { hover = true; repaint(); }
    void mouseExit (const juce::MouseEvent&) override { hover = false; repaint(); }

private:
    bool dragging = false, hover = false;
};
} // namespace moyo

class MoyoChordsEditor : public juce::AudioProcessorEditor, private juce::Timer
{
public:
    explicit MoyoChordsEditor (MoyoChordsProcessor&);
    ~MoyoChordsEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;

private:
    struct Knob
    {
        juce::Slider slider;
        juce::Label label;
        std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> attachment;
    };
    struct Menu
    {
        juce::ComboBox box;
        juce::Label label;
        std::unique_ptr<juce::AudioProcessorValueTreeState::ComboBoxAttachment> attachment;
    };

    void timerCallback() override;
    void setupKnob (Knob&, const juce::String& paramId, const juce::String& title, const juce::String& tip);
    void setupMenu (Menu&, const juce::String& paramId, const juce::String& title, const juce::String& tip);
    void refreshCards();
    void refreshSlotEditor();
    void applySlotEditor();
    void selectSlot (int slot, bool audition);

    MoyoChordsProcessor& processor;
    moyo::LookAndFeel lnf;

    Menu key, scale, count, chordLen, voicing, registerMenu, bass, rhythm, keysMode, sound;
    juce::ComboBox styleBox;
    juce::Label styleLabel;

    juce::TextButton generateButton { "GENERATE" }, varyButton { "VARY" }, undoButton { "<" }, redoButton { ">" };
    juce::TextButton playButton { "PLAY" }, syncButton { "PLAY WITH SONG" }, saveButton { "SAVE MIDI" };
    std::unique_ptr<juce::AudioProcessorValueTreeState::ButtonAttachment> syncAttachment;

    std::array<moyo::ChordCard, moyo::kMaxSlots> cards;
    int selectedSlot = 0;

    juce::Label slotTitle;
    juce::ComboBox slotRoot, slotQuality, slotInversion, slotOctave, slotLength;
    bool updatingSlotEditor = false;

    Knob complexity, colour, strum, humanise, swing, gate, volume;

    moyo::KeyboardDisplay keyboard;
    moyo::DragZone dragZone;
    std::unique_ptr<juce::FileChooser> chooser;

    int seenVersion = -1, seenPlaying = -2;
    juce::String seenKeyScale;
    juce::TooltipWindow tooltips { this, 600 };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MoyoChordsEditor)
};
