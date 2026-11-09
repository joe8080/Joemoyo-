#include "PluginEditor.h"

namespace moyo
{
LookAndFeel::LookAndFeel()
{
    setColour (juce::Slider::textBoxTextColourId, Colours::text);
    setColour (juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
    setColour (juce::Slider::textBoxBackgroundColourId, juce::Colours::transparentBlack);
    setColour (juce::Label::textColourId, Colours::text);
    setColour (juce::ComboBox::backgroundColourId, Colours::panel);
    setColour (juce::ComboBox::outlineColourId, Colours::track);
    setColour (juce::ComboBox::textColourId, Colours::text);
    setColour (juce::ComboBox::arrowColourId, Colours::gold);
    setColour (juce::PopupMenu::backgroundColourId, Colours::panel);
    setColour (juce::PopupMenu::textColourId, Colours::text);
    setColour (juce::PopupMenu::highlightedBackgroundColourId, Colours::gold);
    setColour (juce::PopupMenu::highlightedTextColourId, Colours::bg);
    setColour (juce::TooltipWindow::backgroundColourId, Colours::panel);
    setColour (juce::TooltipWindow::textColourId, Colours::text);
}

void LookAndFeel::drawRotarySlider (juce::Graphics& g, int x, int y, int w, int h, float pos,
                                    float startAngle, float endAngle, juce::Slider& s)
{
    auto bounds = juce::Rectangle<float> ((float) x, (float) y, (float) w, (float) h).reduced (4.0f);
    const float size = juce::jmin (bounds.getWidth(), bounds.getHeight());
    auto r = bounds.withSizeKeepingCentre (size, size);
    const float stroke = juce::jmax (3.0f, size * 0.075f);
    const float radius = size * 0.5f - stroke * 0.5f;
    const auto c = r.getCentre();
    const float angle = startAngle + pos * (endAngle - startAngle);

    juce::Path trackArc, valueArc;
    trackArc.addCentredArc (c.x, c.y, radius, radius, 0, startAngle, endAngle, true);
    valueArc.addCentredArc (c.x, c.y, radius, radius, 0, startAngle, angle, true);
    const juce::PathStrokeType pst (stroke, juce::PathStrokeType::curved, juce::PathStrokeType::rounded);

    g.setColour (Colours::track);
    g.strokePath (trackArc, pst);
    g.setColour (s.isEnabled() ? Colours::gold : Colours::subtext);
    g.strokePath (valueArc, pst);

    // Knob body
    const float bodyR = radius - stroke * 1.2f;
    g.setGradientFill (juce::ColourGradient (juce::Colour (0xff2c2c34), c.x, c.y - bodyR,
                                             juce::Colour (0xff17171c), c.x, c.y + bodyR, false));
    g.fillEllipse (c.x - bodyR, c.y - bodyR, bodyR * 2, bodyR * 2);

    // Pointer
    const float len = bodyR * 0.75f;
    const juce::Point<float> tip (c.x + len * std::sin (angle), c.y - len * std::cos (angle));
    g.setColour (Colours::text);
    g.drawLine ({ c, tip }, juce::jmax (2.0f, stroke * 0.45f));
}

juce::Label* LookAndFeel::createSliderTextBox (juce::Slider& s)
{
    auto* l = LookAndFeel_V4::createSliderTextBox (s);
    l->setFont (juce::FontOptions (15.0f, juce::Font::bold));
    l->setJustificationType (juce::Justification::centred);
    return l;
}

Meter::Meter (juce::String name, float maxDb, bool isReduction)
    : title (std::move (name)), range (maxDb), reduction (isReduction) {}

void Meter::setValueDb (float db)
{
    // For reduction meters db is the amount removed (>= 0); for level meters it is dBFS.
    const float target = reduction ? juce::jlimit (0.0f, 1.0f, db / range)
                                   : juce::jlimit (0.0f, 1.0f, (db + range) / range);
    shown = target > shown ? target : shown * 0.85f + target * 0.15f; // fast up, smooth down
    repaint();
}

void Meter::paint (juce::Graphics& g)
{
    auto b = getLocalBounds().toFloat();
    auto titleArea = b.removeFromBottom (20.0f);
    auto bar = b.reduced (b.getWidth() * 0.28f, 2.0f);

    g.setColour (Colours::panel);
    g.fillRoundedRectangle (bar, 4.0f);

    const float fillH = bar.getHeight() * shown;
    auto fill = reduction ? bar.withHeight (fillH)                       // reduction grows down from the top
                          : bar.withTrimmedTop (bar.getHeight() - fillH); // level grows up from the bottom
    g.setColour (reduction ? Colours::gold : juce::Colour (0xff6fcf97));
    if (! reduction && shown > (range - 1.0f) / range) g.setColour (juce::Colour (0xffeb5757)); // near 0 dBFS
    g.fillRoundedRectangle (fill, 4.0f);

    g.setColour (Colours::subtext);
    g.setFont (juce::FontOptions (12.0f, juce::Font::bold));
    g.drawText (title, titleArea, juce::Justification::centred);
}
} // namespace moyo

MoyoVocalPolishEditor::MoyoVocalPolishEditor (MoyoVocalPolishProcessor& p)
    : AudioProcessorEditor (&p), processor (p)
{
    setLookAndFeel (&lnf);

    setupKnob (polish, "polish", "POLISH",
               "The main knob. Turns up cleanup EQ, compression, presence and sheen together.");
    setupKnob (warmth, "warmth", "WARMTH", "Analogue-style saturation and low-mid body.");
    setupKnob (air,    "air",    "AIR",    "High-frequency sheen for an expensive, open top end.");
    setupKnob (deess,  "deess",  "DE-ESS", "Tames harsh 's' and 't' sounds.");
    setupKnob (mix,    "mix",    "MIX",    "Blend processed and original vocal. Under 100% = parallel processing.");
    setupKnob (output, "output", "OUTPUT", "Final level. Match loudness with bypass for a fair comparison.");

    for (int i = 0; i < processor.getNumPrograms(); ++i)
        presetBox.addItem (processor.getProgramName (i), i + 1);
    presetBox.setSelectedId (processor.getCurrentProgram() + 1, juce::dontSendNotification);
    presetBox.setTooltip ("Starting points. Pick one, then adjust POLISH.");
    presetBox.onChange = [this]
    {
        if (presetBox.getSelectedId() > 0)
            processor.setCurrentProgram (presetBox.getSelectedId() - 1);
    };
    addAndMakeVisible (presetBox);

    compMeter.setTooltip ("How much the compressor is turning the vocal down.");
    deessMeter.setTooltip ("How much sibilance is being removed.");
    outMeter.setTooltip ("Output level. Red means you're close to clipping.");
    addAndMakeVisible (compMeter);
    addAndMakeVisible (deessMeter);
    addAndMakeVisible (outMeter);

    setResizable (true, true);
    setResizeLimits (540, 315, 1440, 840);
    getConstrainer()->setFixedAspectRatio (720.0 / 420.0);
    setSize (720, 420);

    startTimerHz (30);
}

MoyoVocalPolishEditor::~MoyoVocalPolishEditor()
{
    stopTimer();
    setLookAndFeel (nullptr);
}

void MoyoVocalPolishEditor::setupKnob (Knob& k, const juce::String& paramId, const juce::String& title, const juce::String& tip)
{
    k.slider.setSliderStyle (juce::Slider::RotaryVerticalDrag);
    k.slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, 90, 22);
    k.slider.setTooltip (tip + "  (Double-click to reset.)");
    k.slider.setMouseDragSensitivity (220);
    k.attachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (processor.apvts, paramId, k.slider);

    if (auto* param = processor.apvts.getParameter (paramId))
        k.slider.setDoubleClickReturnValue (true, param->convertFrom0to1 (param->getDefaultValue()));

    k.label.setText (title, juce::dontSendNotification);
    k.label.setJustificationType (juce::Justification::centred);
    k.label.setColour (juce::Label::textColourId, moyo::Colours::subtext);

    addAndMakeVisible (k.slider);
    addAndMakeVisible (k.label);
}

void MoyoVocalPolishEditor::timerCallback()
{
    compMeter.setValueDb (processor.compReductionDb.load());
    deessMeter.setValueDb (processor.deessReductionDb.load());
    outMeter.setValueDb (processor.outputPeakDb.load());

    const int prog = processor.getCurrentProgram() + 1;
    if (presetBox.getSelectedId() != prog)
        presetBox.setSelectedId (prog, juce::dontSendNotification);
}

void MoyoVocalPolishEditor::paint (juce::Graphics& g)
{
    const float s = getWidth() / 720.0f;
    g.fillAll (moyo::Colours::bg);

    auto header = getLocalBounds().removeFromTop (juce::roundToInt (56 * s)).toFloat();
    g.setColour (moyo::Colours::gold);
    g.setFont (juce::FontOptions (26.0f * s, juce::Font::bold));
    g.drawText ("MOYO", header.withTrimmedLeft (22 * s), juce::Justification::centredLeft);
    g.setColour (moyo::Colours::text);
    g.setFont (juce::FontOptions (16.0f * s));
    g.drawText ("VOCAL POLISH", header.withTrimmedLeft (102 * s), juce::Justification::centredLeft);

    g.setColour (moyo::Colours::track);
    g.drawHorizontalLine (juce::roundToInt (header.getBottom()), 18 * s, getWidth() - 18 * s);

    g.setColour (moyo::Colours::subtext.withAlpha (0.6f));
    g.setFont (juce::FontOptions (11.0f * s));
    g.drawText ("v1.0", getLocalBounds().removeFromBottom (juce::roundToInt (20 * s)).withTrimmedRight (juce::roundToInt (14 * s)),
                juce::Justification::centredRight);
}

void MoyoVocalPolishEditor::resized()
{
    const float s = getWidth() / 720.0f;
    auto area = getLocalBounds();
    auto header = area.removeFromTop (juce::roundToInt (56 * s));
    presetBox.setBounds (header.removeFromRight (juce::roundToInt (260 * s)).reduced (juce::roundToInt (14 * s), juce::roundToInt (11 * s)));

    area.reduce (juce::roundToInt (16 * s), juce::roundToInt (10 * s));

    auto meters = area.removeFromRight (juce::roundToInt (130 * s));
    const int mw = meters.getWidth() / 3;
    compMeter.setBounds (meters.removeFromLeft (mw));
    deessMeter.setBounds (meters.removeFromLeft (mw));
    outMeter.setBounds (meters);

    auto font = juce::FontOptions (14.0f * s, juce::Font::bold);
    auto placeKnob = [&] (Knob& k, juce::Rectangle<int> r, int textH)
    {
        k.label.setFont (font);
        k.label.setBounds (r.removeFromTop (juce::roundToInt (20 * s)));
        k.slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, r.getWidth(), textH);
        k.slider.setBounds (r);
    };

    // Big POLISH knob on the left.
    auto big = area.removeFromLeft (juce::roundToInt (250 * s));
    polish.label.setFont (juce::FontOptions (18.0f * s, juce::Font::bold));
    polish.label.setColour (juce::Label::textColourId, moyo::Colours::gold);
    polish.label.setBounds (big.removeFromTop (juce::roundToInt (26 * s)));
    polish.slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, big.getWidth(), juce::roundToInt (26 * s));
    polish.slider.setBounds (big.reduced (juce::roundToInt (6 * s), 0));

    // Five smaller knobs in two rows.
    area.removeFromLeft (juce::roundToInt (10 * s));
    auto top = area.removeFromTop (area.getHeight() / 2);
    auto bottom = area;
    const int tw = top.getWidth() / 3;
    const int textH = juce::roundToInt (22 * s);
    placeKnob (warmth, top.removeFromLeft (tw).reduced (4), textH);
    placeKnob (air,    top.removeFromLeft (tw).reduced (4), textH);
    placeKnob (deess,  top.reduced (4), textH);
    placeKnob (mix,    bottom.removeFromLeft (tw).reduced (4), textH);
    placeKnob (output, bottom.removeFromLeft (tw).reduced (4), textH);
}
