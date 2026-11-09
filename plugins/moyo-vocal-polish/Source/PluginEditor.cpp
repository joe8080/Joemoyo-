#include "PluginEditor.h"

namespace moyo
{
LookAndFeel::LookAndFeel()
{
    setColour (juce::Slider::textBoxTextColourId, Colours::text);
    setColour (juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
    setColour (juce::Slider::textBoxBackgroundColourId, juce::Colours::transparentBlack);
    setColour (juce::Slider::textBoxHighlightColourId, Colours::limeDim);
    setColour (juce::Label::textColourId, Colours::text);
    setColour (juce::ComboBox::backgroundColourId, Colours::panel);
    setColour (juce::ComboBox::outlineColourId, Colours::track);
    setColour (juce::ComboBox::textColourId, Colours::text);
    setColour (juce::ComboBox::arrowColourId, Colours::lime);
    setColour (juce::PopupMenu::backgroundColourId, Colours::panel);
    setColour (juce::PopupMenu::textColourId, Colours::text);
    setColour (juce::PopupMenu::highlightedBackgroundColourId, Colours::lime);
    setColour (juce::PopupMenu::highlightedTextColourId, Colours::bg);
    setColour (juce::TooltipWindow::backgroundColourId, Colours::panel);
    setColour (juce::TooltipWindow::textColourId, Colours::text);
    setColour (juce::TooltipWindow::outlineColourId, Colours::limeDim);
}

void LookAndFeel::drawRotarySlider (juce::Graphics& g, int x, int y, int w, int h, float pos,
                                    float startAngle, float endAngle, juce::Slider& s)
{
    auto bounds = juce::Rectangle<float> ((float) x, (float) y, (float) w, (float) h).reduced (4.0f);
    const float size = juce::jmin (bounds.getWidth(), bounds.getHeight());
    auto r = bounds.withSizeKeepingCentre (size, size);
    const float stroke = juce::jmax (3.0f, size * 0.075f);
    const float radius = size * 0.5f - stroke * 0.85f; // leaves room for the glow
    const auto c = r.getCentre();
    const float angle = startAngle + pos * (endAngle - startAngle);

    // Gain knobs (range crosses zero) draw their arc from the centre.
    const bool bipolar = s.getMinimum() < 0.0 && s.getMaximum() > 0.0;
    const float zeroPos = bipolar ? (float) s.valueToProportionOfLength (0.0) : 0.0f;
    const float arcFrom = startAngle + zeroPos * (endAngle - startAngle);

    juce::Path trackArc, valueArc;
    trackArc.addCentredArc (c.x, c.y, radius, radius, 0, startAngle, endAngle, true);
    valueArc.addCentredArc (c.x, c.y, radius, radius, 0, juce::jmin (arcFrom, angle), juce::jmax (arcFrom, angle), true);
    const juce::PathStrokeType pst (stroke, juce::PathStrokeType::curved, juce::PathStrokeType::rounded);

    g.setColour (Colours::track);
    g.strokePath (trackArc, pst);

    // Soft glow under the value arc.
    g.setColour (Colours::lime.withAlpha (0.18f));
    g.strokePath (valueArc, juce::PathStrokeType (stroke * 1.7f, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
    g.setColour (s.isEnabled() ? Colours::lime : Colours::subtext);
    g.strokePath (valueArc, pst);

    // Knob body
    const float bodyR = radius - stroke * 1.25f;
    g.setGradientFill (juce::ColourGradient (juce::Colour (0xff22261f), c.x, c.y - bodyR,
                                             juce::Colour (0xff0b0c0a), c.x, c.y + bodyR, false));
    g.fillEllipse (c.x - bodyR, c.y - bodyR, bodyR * 2, bodyR * 2);
    g.setColour (juce::Colour (0xff2e332a));
    g.drawEllipse (c.x - bodyR, c.y - bodyR, bodyR * 2, bodyR * 2, 1.0f);

    // Pointer
    const float len = bodyR * 0.78f;
    const juce::Point<float> from (c.x + bodyR * 0.25f * std::sin (angle), c.y - bodyR * 0.25f * std::cos (angle));
    const juce::Point<float> tip (c.x + len * std::sin (angle), c.y - len * std::cos (angle));
    g.setColour (Colours::text);
    g.drawLine ({ from, tip }, juce::jmax (2.0f, stroke * 0.45f));
}

juce::Label* LookAndFeel::createSliderTextBox (juce::Slider& s)
{
    auto* l = LookAndFeel_V4::createSliderTextBox (s);
    l->setFont (juce::FontOptions (15.0f, juce::Font::bold));
    l->setJustificationType (juce::Justification::centred);
    return l;
}

void LookAndFeel::drawButtonBackground (juce::Graphics& g, juce::Button& b, const juce::Colour&, bool over, bool down)
{
    auto r = b.getLocalBounds().toFloat().reduced (1.0f);
    const float corner = r.getHeight() * 0.22f;
    const bool on = b.getToggleState();
    const bool warn = b.getProperties()["warn"];
    const auto accent = warn ? Colours::warn : Colours::lime;

    g.setColour (on ? accent : (over ? Colours::track : Colours::panel));
    g.fillRoundedRectangle (r, corner);
    g.setColour (on ? accent : (down ? Colours::lime : Colours::track.brighter (0.3f)));
    g.drawRoundedRectangle (r, corner, 1.5f);
}

void LookAndFeel::drawButtonText (juce::Graphics& g, juce::TextButton& b, bool, bool)
{
    const bool on = b.getToggleState();
    g.setColour (on ? Colours::bg : Colours::text);
    g.setFont (juce::FontOptions (juce::jlimit (11.0f, 20.0f, b.getHeight() * 0.42f), juce::Font::bold));
    g.drawText (b.getButtonText(), b.getLocalBounds(), juce::Justification::centred);
}

Meter::Meter (juce::String name, float maxDb, bool isReduction)
    : title (std::move (name)), range (maxDb), reduction (isReduction) {}

void Meter::setValueDb (float db)
{
    // Reduction meters: db is the amount removed (>= 0). Level meters: db is dBFS.
    const float target = reduction ? juce::jlimit (0.0f, 1.0f, db / range)
                                   : juce::jlimit (0.0f, 1.0f, (db + range) / range);
    shown = target > shown ? target : shown * 0.85f + target * 0.15f; // fast up, smooth down

    // Readout holds the peak for ~1 s so it can actually be read.
    if (db > hold || --holdFrames <= 0) { hold = db; holdFrames = 30; }
    readout = hold;
    repaint();
}

void Meter::paint (juce::Graphics& g)
{
    auto b = getLocalBounds().toFloat();
    auto titleArea = b.removeFromBottom (20.0f);
    auto valueArea = b.removeFromTop (18.0f);
    auto bar = b.reduced (b.getWidth() * 0.26f, 3.0f);

    g.setColour (Colours::panel);
    g.fillRoundedRectangle (bar, 4.0f);

    const float fillH = bar.getHeight() * shown;
    auto fill = reduction ? bar.withHeight (fillH)                       // reduction hangs from the top
                          : bar.withTrimmedTop (bar.getHeight() - fillH); // level rises from the bottom
    const bool hot = ! reduction && readout > -1.0f;
    g.setColour (hot ? Colours::warn : (reduction ? Colours::lime : Colours::lime.withAlpha (0.75f)));
    g.fillRoundedRectangle (fill, 4.0f);

    juce::String text;
    if (reduction)        text = readout > 0.05f ? "-" + juce::String (readout, 1) : "0.0";
    else if (readout < -59.0f) text = "-inf";
    else                  text = juce::String (readout, 1);

    g.setColour (hot ? Colours::warn : Colours::text);
    g.setFont (juce::FontOptions (12.0f, juce::Font::bold));
    g.drawText (text, valueArea, juce::Justification::centred);

    g.setColour (Colours::subtext);
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
    setupKnob (input,  "input",  "INPUT",  "Level going in. More input = the compressor works harder.");
    setupKnob (mix,    "mix",    "MIX",    "Blend processed and original vocal. Under 100% = parallel processing.");
    setupKnob (output, "output", "OUTPUT", "Final level out of the plugin.");

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

    // A/B settings slots
    for (auto* b : { &slotA, &slotB, &copySlot })
        addAndMakeVisible (*b);
    slotA.setTooltip ("Settings slot A.");
    slotB.setTooltip ("Settings slot B. Set up two versions and flip between them.");
    copySlot.setTooltip ("Copy the slot you're on into the other slot.");
    slotA.onClick = [this] { processor.selectSlot (0); refreshSlotButtons(); };
    slotB.onClick = [this] { processor.selectSlot (1); refreshSlotButtons(); };
    copySlot.onClick = [this]
    {
        processor.copyActiveSlotToOther();
        copySlot.setButtonText (processor.getActiveSlot() == 0 ? "A > B" : "B > A");
        juce::Timer::callAfterDelay (900, [safe = juce::Component::SafePointer<juce::TextButton> (&copySlot)]
                                     { if (safe != nullptr) safe->setButtonText ("COPY"); });
    };
    refreshSlotButtons();

    // Listening / safety toggles
    setupToggle (hearOriginal, "HEAR ORIGINAL", "Switches to your untouched vocal at the same level, so you hear exactly what MOYO is doing. Click again to hear MOYO.");
    hearOriginal.getProperties().set ("warn", true);
    setupToggle (autoGain, "AUTO GAIN", "Keeps the output as loud as the input, so you judge the sound, not the volume.");
    setupToggle (clipGuard, "CLIP GUARD", "Rounds off peaks so the output never goes over 0 dB.");
    originalAtt  = std::make_unique<ButtonAttachment> (processor.apvts, "original",  hearOriginal);
    autoGainAtt  = std::make_unique<ButtonAttachment> (processor.apvts, "autogain",  autoGain);
    clipGuardAtt = std::make_unique<ButtonAttachment> (processor.apvts, "clipguard", clipGuard);

    inMeter.setTooltip ("Input level.");
    compMeter.setTooltip ("How much the compressor is turning the vocal down.");
    deessMeter.setTooltip ("How much sibilance is being removed.");
    outMeter.setTooltip ("Output level. Red means you're close to clipping.");
    for (auto* m : { &inMeter, &compMeter, &deessMeter, &outMeter })
        addAndMakeVisible (*m);

    autoGainReadout.setJustificationType (juce::Justification::centredLeft);
    autoGainReadout.setColour (juce::Label::textColourId, moyo::Colours::subtext);
    addAndMakeVisible (autoGainReadout);

    setResizable (true, true);
    setResizeLimits (600, 360, 1640, 984);
    getConstrainer()->setFixedAspectRatio (820.0 / 492.0);
    setSize (820, 492);

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
    k.slider.setTooltip (tip + "  (Double-click to reset. Scroll wheel works too.)");
    k.slider.setMouseDragSensitivity (220);
    k.slider.setScrollWheelEnabled (true);
    k.attachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment> (processor.apvts, paramId, k.slider);

    if (auto* param = processor.apvts.getParameter (paramId))
        k.slider.setDoubleClickReturnValue (true, param->convertFrom0to1 (param->getDefaultValue()));

    k.label.setText (title, juce::dontSendNotification);
    k.label.setJustificationType (juce::Justification::centred);
    k.label.setColour (juce::Label::textColourId, moyo::Colours::subtext);

    addAndMakeVisible (k.slider);
    addAndMakeVisible (k.label);
}

void MoyoVocalPolishEditor::setupToggle (juce::TextButton& b, const juce::String& text, const juce::String& tip)
{
    b.setButtonText (text);
    b.setClickingTogglesState (true);
    b.setTooltip (tip);
    addAndMakeVisible (b);
}

void MoyoVocalPolishEditor::refreshSlotButtons()
{
    slotA.setToggleState (processor.getActiveSlot() == 0, juce::dontSendNotification);
    slotB.setToggleState (processor.getActiveSlot() == 1, juce::dontSendNotification);
}

void MoyoVocalPolishEditor::timerCallback()
{
    inMeter.setValueDb (processor.inputPeakDb.load());
    compMeter.setValueDb (processor.compReductionDb.load());
    deessMeter.setValueDb (processor.deessReductionDb.load());
    outMeter.setValueDb (processor.outputPeakDb.load());

    const bool agOn = processor.apvts.getRawParameterValue ("autogain")->load() > 0.5f;
    const float ag = processor.autoGainDb.load();
    autoGainReadout.setText (agOn ? "Level match " + juce::String (ag >= 0 ? "+" : "") + juce::String (ag, 1) + " dB" : "",
                             juce::dontSendNotification);

    const int prog = processor.getCurrentProgram() + 1;
    if (presetBox.getSelectedId() != prog)
        presetBox.setSelectedId (prog, juce::dontSendNotification);
    refreshSlotButtons();
}

void MoyoVocalPolishEditor::paint (juce::Graphics& g)
{
    const float s = getWidth() / 820.0f;
    g.fillAll (moyo::Colours::bg);

    // Subtle lime glow behind the main knob.
    const auto glowCentre = juce::Point<float> (150 * s, 250 * s);
    g.setGradientFill (juce::ColourGradient (moyo::Colours::lime.withAlpha (0.07f), glowCentre,
                                             juce::Colours::transparentBlack, glowCentre.translated (200 * s, 0), true));
    g.fillRect (getLocalBounds());

    auto header = getLocalBounds().removeFromTop (juce::roundToInt (60 * s)).toFloat();
    g.setColour (moyo::Colours::lime);
    g.setFont (juce::FontOptions (28.0f * s, juce::Font::bold));
    g.drawText ("MOYO", header.withTrimmedLeft (22 * s), juce::Justification::centredLeft);
    g.setColour (moyo::Colours::text);
    g.setFont (juce::FontOptions (16.0f * s));
    g.drawText ("VOCAL POLISH", header.withTrimmedLeft (110 * s), juce::Justification::centredLeft);

    g.setColour (moyo::Colours::track);
    g.drawHorizontalLine (juce::roundToInt (header.getBottom()), 18 * s, getWidth() - 18 * s);
    g.drawHorizontalLine (getHeight() - juce::roundToInt (62 * s), 18 * s, getWidth() - 18 * s);

    g.setColour (moyo::Colours::subtext.withAlpha (0.6f));
    g.setFont (juce::FontOptions (11.0f * s));
    g.drawText ("v1.1", getLocalBounds().removeFromBottom (juce::roundToInt (18 * s)).withTrimmedRight (juce::roundToInt (14 * s)),
                juce::Justification::centredRight);
}

void MoyoVocalPolishEditor::resized()
{
    const float s = getWidth() / 820.0f;
    auto S = [s] (float v) { return juce::roundToInt (v * s); };

    auto area = getLocalBounds();
    auto header = area.removeFromTop (S (60));
    presetBox.setBounds (header.removeFromRight (S (250)).reduced (S (14), S (12)));
    auto slots = header.removeFromRight (S (210)).reduced (S (4), S (13));
    slotA.setBounds (slots.removeFromLeft (S (52)));
    slots.removeFromLeft (S (6));
    slotB.setBounds (slots.removeFromLeft (S (52)));
    slots.removeFromLeft (S (6));
    copySlot.setBounds (slots);

    auto footer = area.removeFromBottom (S (62)).reduced (S (18), S (12));
    hearOriginal.setBounds (footer.removeFromLeft (S (250)));
    footer.removeFromLeft (S (16));
    autoGain.setBounds (footer.removeFromLeft (S (130)));
    footer.removeFromLeft (S (10));
    clipGuard.setBounds (footer.removeFromLeft (S (130)));
    footer.removeFromLeft (S (12));
    autoGainReadout.setFont (juce::FontOptions (13.0f * s, juce::Font::bold));
    autoGainReadout.setBounds (footer.removeFromLeft (S (170)));

    area.reduce (S (16), S (10));

    auto meters = area.removeFromRight (S (176));
    const int mw = meters.getWidth() / 4;
    inMeter.setBounds (meters.removeFromLeft (mw));
    compMeter.setBounds (meters.removeFromLeft (mw));
    deessMeter.setBounds (meters.removeFromLeft (mw));
    outMeter.setBounds (meters);

    auto font = juce::FontOptions (14.0f * s, juce::Font::bold);
    const int textH = S (22);
    auto placeKnob = [&] (Knob& k, juce::Rectangle<int> r)
    {
        k.label.setFont (font);
        k.label.setBounds (r.removeFromTop (S (20)));
        k.slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, r.getWidth(), textH);
        k.slider.setBounds (r);
    };

    // Big POLISH knob on the left.
    auto big = area.removeFromLeft (S (260));
    polish.label.setFont (juce::FontOptions (19.0f * s, juce::Font::bold));
    polish.label.setColour (juce::Label::textColourId, moyo::Colours::lime);
    polish.label.setBounds (big.removeFromTop (S (26)));
    polish.slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, big.getWidth(), S (26));
    polish.slider.setBounds (big.reduced (S (6), 0));

    // Six smaller knobs: tone on top, levels underneath.
    area.removeFromLeft (S (8));
    auto top = area.removeFromTop (area.getHeight() / 2);
    auto bottom = area;
    const int tw = top.getWidth() / 3;
    placeKnob (warmth, top.removeFromLeft (tw).reduced (4));
    placeKnob (air,    top.removeFromLeft (tw).reduced (4));
    placeKnob (deess,  top.reduced (4));
    placeKnob (input,  bottom.removeFromLeft (tw).reduced (4));
    placeKnob (mix,    bottom.removeFromLeft (tw).reduced (4));
    placeKnob (output, bottom.reduced (4));
}
