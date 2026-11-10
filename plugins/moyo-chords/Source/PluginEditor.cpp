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
    const float radius = size * 0.5f - stroke * 0.85f;
    const auto c = r.getCentre();
    const float angle = startAngle + pos * (endAngle - startAngle);

    // Knobs whose range crosses zero (Strum) draw their arc from the centre.
    const bool bipolar = s.getMinimum() < 0.0 && s.getMaximum() > 0.0;
    const float zeroPos = bipolar ? (float) s.valueToProportionOfLength (0.0) : 0.0f;
    const float arcFrom = startAngle + zeroPos * (endAngle - startAngle);

    juce::Path trackArc, valueArc;
    trackArc.addCentredArc (c.x, c.y, radius, radius, 0, startAngle, endAngle, true);
    valueArc.addCentredArc (c.x, c.y, radius, radius, 0, juce::jmin (arcFrom, angle), juce::jmax (arcFrom, angle), true);
    const juce::PathStrokeType pst (stroke, juce::PathStrokeType::curved, juce::PathStrokeType::rounded);

    g.setColour (Colours::track);
    g.strokePath (trackArc, pst);
    g.setColour (Colours::lime.withAlpha (0.18f));
    g.strokePath (valueArc, juce::PathStrokeType (stroke * 1.7f, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
    g.setColour (Colours::lime);
    g.strokePath (valueArc, pst);

    const float bodyR = radius - stroke * 1.25f;
    g.setGradientFill (juce::ColourGradient (juce::Colour (0xff22261f), c.x, c.y - bodyR, juce::Colour (0xff0b0c0a), c.x, c.y + bodyR, false));
    g.fillEllipse (c.x - bodyR, c.y - bodyR, bodyR * 2, bodyR * 2);
    g.setColour (juce::Colour (0xff2e332a));
    g.drawEllipse (c.x - bodyR, c.y - bodyR, bodyR * 2, bodyR * 2, 1.0f);

    const float len = bodyR * 0.78f;
    const juce::Point<float> from (c.x + bodyR * 0.25f * std::sin (angle), c.y - bodyR * 0.25f * std::cos (angle));
    const juce::Point<float> tip (c.x + len * std::sin (angle), c.y - len * std::cos (angle));
    g.setColour (Colours::text);
    g.drawLine ({ from, tip }, juce::jmax (2.0f, stroke * 0.45f));
}

juce::Label* LookAndFeel::createSliderTextBox (juce::Slider& s)
{
    auto* l = LookAndFeel_V4::createSliderTextBox (s);
    l->setFont (juce::FontOptions (14.0f, juce::Font::bold));
    l->setJustificationType (juce::Justification::centred);
    return l;
}

void LookAndFeel::drawButtonBackground (juce::Graphics& g, juce::Button& b, const juce::Colour&, bool over, bool down)
{
    auto r = b.getLocalBounds().toFloat().reduced (1.0f);
    const float corner = juce::jmin (10.0f, r.getHeight() * 0.22f);
    const bool primary = b.getProperties()["primary"];
    const bool on = b.getToggleState() || primary;
    const float dim = b.isEnabled() ? 1.0f : 0.35f;

    g.setColour ((on ? (down ? Colours::lime.darker (0.25f) : (over ? Colours::lime.brighter (0.15f) : Colours::lime))
                     : (down ? Colours::track.brighter (0.2f) : (over ? Colours::track : Colours::panel))).withMultipliedAlpha (dim));
    g.fillRoundedRectangle (r, corner);
    g.setColour ((on ? Colours::lime : Colours::track.brighter (0.3f)).withMultipliedAlpha (dim));
    g.drawRoundedRectangle (r, corner, 1.5f);
}

void LookAndFeel::drawButtonText (juce::Graphics& g, juce::TextButton& b, bool, bool)
{
    const bool on = b.getToggleState() || (bool) b.getProperties()["primary"];
    g.setColour ((on ? Colours::bg : Colours::text).withMultipliedAlpha (b.isEnabled() ? 1.0f : 0.4f));
    const float maxSize = (bool) b.getProperties()["primary"] ? 26.0f : 18.0f;
    g.setFont (juce::FontOptions (juce::jlimit (10.0f, maxSize, b.getHeight() * 0.42f), juce::Font::bold));
    g.drawFittedText (b.getButtonText(), b.getLocalBounds().reduced (4, 0), juce::Justification::centred, 1);
}

juce::Font LookAndFeel::getComboBoxFont (juce::ComboBox& box)
{
    return juce::FontOptions (juce::jlimit (11.0f, 17.0f, box.getHeight() * 0.46f));
}

// ---- ChordCard ---------------------------------------------------------------

void ChordCard::setData (const juce::String& chordName, const juce::String& roman, const juce::String& lengthText,
                         bool isLocked, bool isSelected, bool isPlaying)
{
    if (name == chordName && numeral == roman && length == lengthText && locked == isLocked && selected == isSelected && playing == isPlaying)
        return;
    name = chordName; numeral = roman; length = lengthText;
    locked = isLocked; selected = isSelected; playing = isPlaying;
    repaint();
}

void ChordCard::paint (juce::Graphics& g)
{
    auto r = getLocalBounds().toFloat().reduced (2.0f);
    const float h = r.getHeight();

    g.setColour (playing ? Colours::lime.withAlpha (0.20f) : Colours::panel);
    g.fillRoundedRectangle (r, 10.0f);
    g.setColour (selected ? Colours::lime : Colours::track.brighter (0.2f));
    g.drawRoundedRectangle (r, 10.0f, selected ? 2.5f : 1.0f);

    auto strip = r.removeFromBottom (h * 0.22f);
    auto top = r.removeFromTop (h * 0.16f);

    g.setColour (Colours::subtext);
    g.setFont (juce::FontOptions (juce::jlimit (9.0f, 13.0f, h * 0.095f)));
    g.drawText (length, top.reduced (8.0f, 0), juce::Justification::centredRight);

    g.setColour (playing ? Colours::lime : Colours::text);
    g.setFont (juce::FontOptions (juce::jlimit (12.0f, 34.0f, juce::jmin (h * 0.27f, r.getWidth() * 0.23f)), juce::Font::bold));
    g.drawFittedText (name, r.removeFromTop (r.getHeight() * 0.62f).toNearestInt().reduced (4, 0), juce::Justification::centred, 1, 0.6f);

    g.setColour (Colours::subtext);
    g.setFont (juce::FontOptions (juce::jlimit (10.0f, 16.0f, h * 0.115f)));
    g.drawFittedText (numeral, r.toNearestInt().reduced (4, 0), juce::Justification::centredTop, 1, 0.7f);

    g.setColour (Colours::track.brighter (0.2f));
    g.drawHorizontalLine (juce::roundToInt (strip.getY()), strip.getX() + 6.0f, strip.getRight() - 6.0f);
    g.drawVerticalLine (juce::roundToInt (strip.getCentreX()), strip.getY() + 4.0f, strip.getBottom() - 4.0f);
    g.setFont (juce::FontOptions (juce::jlimit (9.0f, 13.0f, h * 0.095f), juce::Font::bold));
    g.setColour (locked ? Colours::lime : Colours::subtext);
    g.drawText (locked ? "LOCKED" : "LOCK", strip.withWidth (strip.getWidth() * 0.5f), juce::Justification::centred);
    g.setColour (Colours::subtext);
    g.drawText ("ROLL", strip.withTrimmedLeft (strip.getWidth() * 0.5f), juce::Justification::centred);
}

void ChordCard::mouseUp (const juce::MouseEvent& e)
{
    if (! getLocalBounds().contains (e.getPosition())) return;
    if (e.y > getHeight() * 0.78f)
    {
        if (e.x < getWidth() / 2) { if (onLock) onLock(); }
        else if (onRoll) onRoll();
    }
    else if (onSelect)
        onSelect();
}

// ---- KeyboardDisplay ---------------------------------------------------------

void KeyboardDisplay::setNotes (juce::uint64 low, juce::uint64 high)
{
    if (low == lo && high == hi) return;
    lo = low; hi = high;
    repaint();
}

void KeyboardDisplay::paint (juce::Graphics& g)
{
    static const bool black[12] = { false, true, false, true, false, false, true, false, true, false, true, false };
    int whites = 0;
    for (int n = firstNote; n <= lastNote; ++n) whites += ! black[n % 12];
    const auto area = getLocalBounds().toFloat();
    const float ww = area.getWidth() / (float) whites;

    int w = 0;
    for (int n = firstNote; n <= lastNote; ++n)
    {
        if (black[n % 12]) continue;
        auto key = juce::Rectangle<float> (area.getX() + w * ww, area.getY(), ww, area.getHeight()).reduced (0.6f, 0.0f);
        g.setColour (isLit (n) ? Colours::lime : (n % 12 == 0 ? juce::Colour (0xffd9ddd4) : juce::Colour (0xffc4c9bf)));
        g.fillRoundedRectangle (key, 2.0f);
        ++w;
    }
    w = 0;
    for (int n = firstNote; n <= lastNote; ++n)
    {
        if (! black[n % 12]) { ++w; continue; }
        auto key = juce::Rectangle<float> (area.getX() + w * ww - ww * 0.3f, area.getY(), ww * 0.6f, area.getHeight() * 0.62f);
        g.setColour (isLit (n) ? Colours::lime : Colours::bg);
        g.fillRoundedRectangle (key, 1.5f);
        if (isLit (n)) { g.setColour (Colours::bg); g.drawRoundedRectangle (key, 1.5f, 1.0f); }
    }
}

// ---- DragZone ----------------------------------------------------------------

void DragZone::paint (juce::Graphics& g)
{
    auto r = getLocalBounds().toFloat().reduced (1.5f);
    g.setColour (hover ? Colours::lime.withAlpha (0.16f) : Colours::panel);
    g.fillRoundedRectangle (r, 10.0f);

    juce::Path outline;
    outline.addRoundedRectangle (r, 10.0f);
    juce::Path dashed;
    const float dashes[] = { 7.0f, 5.0f };
    juce::PathStrokeType (2.0f).createDashedStroke (dashed, outline, dashes, 2);
    g.setColour (Colours::lime);
    g.fillPath (dashed);

    g.setFont (juce::FontOptions (juce::jlimit (11.0f, 19.0f, r.getHeight() * 0.27f), juce::Font::bold));
    g.drawFittedText ("DRAG MIDI", r.removeFromTop (r.getHeight() * 0.58f).toNearestInt(), juce::Justification::centredBottom, 1);
    g.setColour (Colours::subtext);
    g.setFont (juce::FontOptions (juce::jlimit (9.0f, 13.0f, getHeight() * 0.18f)));
    g.drawFittedText ("into the Piano Roll or Playlist", r.toNearestInt().reduced (4, 2), juce::Justification::centredTop, 1, 0.7f);
}

void DragZone::mouseDrag (const juce::MouseEvent& e)
{
    if (dragging || e.getDistanceFromDragStart() < 5 || ! makeFile) return;
    dragging = true;
    const auto file = makeFile();
    if (file.existsAsFile())
        juce::DragAndDropContainer::performExternalDragDropOfFiles ({ file.getFullPathName() }, false, this);
}
} // namespace moyo

// ==============================================================================

MoyoChordsEditor::MoyoChordsEditor (MoyoChordsProcessor& p)
    : AudioProcessorEditor (&p), processor (p)
{
    setLookAndFeel (&lnf);

    setupMenu (key, "key", "KEY", "The key of the song.");
    setupMenu (scale, "scale", "SCALE", "The scale the chords are built from.");
    setupMenu (count, "count", "", "How many chords in the progression.");
    setupMenu (chordLen, "chordLen", "", "How long each chord lasts. You can also set each chord's length separately below.");
    setupMenu (voicing, "voicing", "VOICING", "How the notes of each chord are spread out. Chords always move smoothly from one to the next.");
    setupMenu (registerMenu, "register", "REGISTER", "How high or low the chords sit.");
    setupMenu (bass, "bass", "BASS", "Adds a bass note under each chord.");
    setupMenu (rhythm, "rhythm", "RHYTHM", "How the chords are played: held, rhythmic, or as an arpeggio.");
    setupMenu (keysMode, "keysMode", "", "What your keyboard or Piano Roll notes do. One chord per key: white keys from middle C play chord 1, 2, 3...");
    setupMenu (sound, "sound", "", "The built-in sound. Choose 'No sound' when MOYO Chords is driving another instrument.");

    // Style is handled by hand: picking a style also loads that style's suggested settings.
    for (int i = 0; i < (int) moyo::styles().size(); ++i)
        styleBox.addItem (moyo::styles()[(size_t) i].name, i + 1);
    styleBox.setTooltip ("The genre. Picking one also sets Complexity, Colour, Voicing and Rhythm to suit it.");
    styleBox.onChange = [this]
    {
        if (styleBox.getSelectedId() > 0) processor.setStyleFromUser (styleBox.getSelectedId() - 1);
    };
    styleLabel.setText ("STYLE", juce::dontSendNotification);
    styleLabel.setColour (juce::Label::textColourId, moyo::Colours::subtext);
    addAndMakeVisible (styleBox);
    addAndMakeVisible (styleLabel);

    generateButton.getProperties().set ("primary", true);
    generateButton.setTooltip ("Writes a new chord progression. Locked chords are kept.");
    generateButton.onClick = [this] { processor.generate(); };
    varyButton.setTooltip ("Keeps the same chords but gives them new extensions and feel.");
    varyButton.onClick = [this] { processor.vary(); };
    undoButton.setTooltip ("Back to the previous progression.");
    undoButton.onClick = [this] { processor.undo(); };
    redoButton.setTooltip ("Forward again.");
    redoButton.onClick = [this] { processor.redo(); };
    playButton.setClickingTogglesState (true);
    playButton.setTooltip ("Plays the progression on a loop so you can hear it.");
    playButton.onClick = [this] { processor.setPreviewPlaying (playButton.getToggleState()); };
    syncButton.setClickingTogglesState (true);
    syncButton.setTooltip ("When on, the progression plays in time whenever your song plays.");
    syncAttachment = std::make_unique<juce::AudioProcessorValueTreeState::ButtonAttachment> (processor.apvts, "hostSync", syncButton);
    saveButton.setTooltip ("Saves the progression as a MIDI file.");
    saveButton.onClick = [this]
    {
        const auto folder = juce::File::getSpecialLocation (juce::File::userDocumentsDirectory).getChildFile ("MOYO Chords");
        folder.createDirectory();
        chooser = std::make_unique<juce::FileChooser> ("Save MIDI", folder.getChildFile (processor.suggestedFileName()), "*.mid");
        chooser->launchAsync (juce::FileBrowserComponent::saveMode | juce::FileBrowserComponent::canSelectFiles | juce::FileBrowserComponent::warnAboutOverwriting,
                              [this] (const juce::FileChooser& fc)
                              {
                                  const auto f = fc.getResult();
                                  if (f != juce::File()) processor.writeMidiFile (f.withFileExtension ("mid"));
                              });
    };
    for (auto* b : { &generateButton, &varyButton, &undoButton, &redoButton, &playButton, &syncButton, &saveButton })
        addAndMakeVisible (*b);

    for (int i = 0; i < moyo::kMaxSlots; ++i)
    {
        auto& c = cards[(size_t) i];
        c.onSelect = [this, i] { selectSlot (i, true); };
        c.onLock = [this, i] { processor.toggleLock (i); };
        c.onRoll = [this, i] { processor.rerollSlot (i); selectSlot (i, true); };
        c.setTooltip ("Click to hear this chord and edit it below. LOCK keeps it when you generate. ROLL swaps in a different chord.");
        addAndMakeVisible (c);
    }

    slotTitle.setColour (juce::Label::textColourId, moyo::Colours::lime);
    addAndMakeVisible (slotTitle);
    for (int q = 0; q < moyo::NumQualities; ++q)
        slotQuality.addItem (q == moyo::Maj ? "major" : juce::String (moyo::quality (q).suffix), q + 1);
    slotInversion.addItemList ({ "Inversion: auto", "Root position", "1st inversion", "2nd inversion", "3rd inversion" }, 1);
    slotOctave.addItemList ({ "Octave -2", "Octave -1", "Octave 0", "Octave +1", "Octave +2" }, 1);
    slotLength.addItemList ({ "1/2 bar", "1 bar", "2 bars", "4 bars" }, 1);
    slotRoot.setTooltip ("The selected chord's root note.");
    slotQuality.setTooltip ("The selected chord's type.");
    slotInversion.setTooltip ("Auto picks the inversion that moves least from the chord before.");
    slotOctave.setTooltip ("Moves just this chord up or down an octave.");
    slotLength.setTooltip ("How long this chord lasts.");
    for (auto* b : { &slotRoot, &slotQuality, &slotInversion, &slotOctave, &slotLength })
    {
        b->onChange = [this] { applySlotEditor(); };
        addAndMakeVisible (*b);
    }

    setupKnob (complexity, "complexity", "COMPLEXITY", "Low = simple three-note chords. High = rich 7ths, 9ths, 11ths and 13ths.");
    setupKnob (colour, "colour", "COLOUR", "How adventurous the chords are: borrowed chords, secondary dominants, sus and add9 flavours.");
    setupKnob (strum, "strum", "STRUM", "Spreads the notes of each chord like a strummed guitar. Right = low to high, left = high to low.");
    setupKnob (humanise, "humanise", "HUMANISE", "Small random changes in timing and loudness so it sounds played, not programmed.");
    setupKnob (swing, "swing", "SWING", "Delays the off-beats for a shuffled, laid-back feel.");
    setupKnob (gate, "gate", "LENGTH", "How long each note is held. Low = short and choppy, high = smooth and connected.");
    setupKnob (volume, "volume", "VOLUME", "Volume of the built-in sound.");

    addAndMakeVisible (keyboard);
    dragZone.setTooltip ("Drag from here and drop into FL Studio's Piano Roll, Playlist or Channel Rack.");
    dragZone.makeFile = [this]
    {
        const auto file = juce::File::getSpecialLocation (juce::File::tempDirectory).getChildFile ("MOYO Chords").getChildFile (processor.suggestedFileName());
        return processor.writeMidiFile (file) ? file : juce::File();
    };
    addAndMakeVisible (dragZone);

    setResizable (true, true);
    setResizeLimits (735, 487, 1960, 1300);
    getConstrainer()->setFixedAspectRatio (980.0 / 650.0);
    setSize (980, 650);

    timerCallback();
    startTimerHz (30);
}

MoyoChordsEditor::~MoyoChordsEditor()
{
    stopTimer();
    setLookAndFeel (nullptr);
}

void MoyoChordsEditor::setupKnob (Knob& k, const juce::String& paramId, const juce::String& title, const juce::String& tip)
{
    k.slider.setSliderStyle (juce::Slider::RotaryVerticalDrag);
    k.slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, 80, 20);
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

void MoyoChordsEditor::setupMenu (Menu& m, const juce::String& paramId, const juce::String& title, const juce::String& tip)
{
    if (auto* choice = dynamic_cast<juce::AudioParameterChoice*> (processor.apvts.getParameter (paramId)))
        m.box.addItemList (choice->choices, 1);
    m.box.setTooltip (tip);
    m.attachment = std::make_unique<juce::AudioProcessorValueTreeState::ComboBoxAttachment> (processor.apvts, paramId, m.box);
    m.label.setText (title, juce::dontSendNotification);
    m.label.setColour (juce::Label::textColourId, moyo::Colours::subtext);
    addAndMakeVisible (m.box);
    if (title.isNotEmpty()) addAndMakeVisible (m.label);
}

void MoyoChordsEditor::selectSlot (int slot, bool audition)
{
    selectedSlot = juce::jlimit (0, juce::jmax (0, processor.getProgression().count - 1), slot);
    if (audition) processor.auditionSlot (selectedSlot);
    refreshCards();
    refreshSlotEditor();
}

void MoyoChordsEditor::refreshCards()
{
    const auto prog = processor.getProgression();
    const int playing = processor.playingSlot.load();
    selectedSlot = juce::jmin (selectedSlot, prog.count - 1);
    for (int i = 0; i < moyo::kMaxSlots; ++i)
    {
        auto& card = cards[(size_t) i];
        card.setVisible (i < prog.count);
        if (i >= prog.count) continue;
        const double beats = prog.slots[(size_t) i].beats;
        const juce::String len = beats <= 2.0 ? "1/2 bar" : (beats <= 4.0 ? "1 bar" : (beats <= 8.0 ? "2 bars" : "4 bars"));
        card.setData (processor.getChordName (i), processor.getRomanName (i), len, prog.slots[(size_t) i].locked, i == selectedSlot, i == playing);
    }
    resized();
}

void MoyoChordsEditor::refreshSlotEditor()
{
    const auto prog = processor.getProgression();
    const auto& c = prog.slots[(size_t) selectedSlot];
    const int tonic = (int) processor.apvts.getRawParameterValue ("key")->load();
    const int scaleIdx = (int) processor.apvts.getRawParameterValue ("scale")->load();

    const juce::ScopedValueSetter<bool> guard (updatingSlotEditor, true);
    slotTitle.setText ("CHORD " + juce::String (selectedSlot + 1), juce::dontSendNotification);
    slotRoot.clear (juce::dontSendNotification);
    for (int r = 0; r < 12; ++r)
    {
        moyo::Chord probe;
        probe.root = r;
        slotRoot.addItem (juce::String (moyo::rootName (tonic, scaleIdx, r)) + "   (" + juce::String (moyo::romanName (probe)) + ")", r + 1);
    }
    slotRoot.setSelectedId (c.root + 1, juce::dontSendNotification);
    slotQuality.setSelectedId (c.quality + 1, juce::dontSendNotification);
    slotInversion.setSelectedId (c.inversion + 2, juce::dontSendNotification);
    slotOctave.setSelectedId (c.octave + 3, juce::dontSendNotification);
    slotLength.setSelectedId (c.beats <= 2.0 ? 1 : (c.beats <= 4.0 ? 2 : (c.beats <= 8.0 ? 3 : 4)), juce::dontSendNotification);
}

void MoyoChordsEditor::applySlotEditor()
{
    if (updatingSlotEditor) return;
    auto c = processor.getProgression().slots[(size_t) selectedSlot];
    if (slotRoot.getSelectedId() > 0)      c.root = slotRoot.getSelectedId() - 1;
    if (slotQuality.getSelectedId() > 0)   c.quality = slotQuality.getSelectedId() - 1;
    if (slotInversion.getSelectedId() > 0) c.inversion = slotInversion.getSelectedId() - 2;
    if (slotOctave.getSelectedId() > 0)    c.octave = slotOctave.getSelectedId() - 3;
    static const double lengths[] = { 2.0, 4.0, 8.0, 16.0 };
    if (slotLength.getSelectedId() > 0)    c.beats = lengths[slotLength.getSelectedId() - 1];
    processor.setSlot (selectedSlot, c);
    processor.auditionSlot (selectedSlot);
}

void MoyoChordsEditor::timerCallback()
{
    const int version = processor.uiVersion.load();
    const int playing = processor.playingSlot.load();
    const auto keyScale = processor.apvts.getParameter ("key")->getCurrentValueAsText() + processor.apvts.getParameter ("scale")->getCurrentValueAsText();

    if (version != seenVersion || keyScale != seenKeyScale)
    {
        seenVersion = version;
        seenKeyScale = keyScale;
        seenPlaying = playing;
        refreshCards();
        refreshSlotEditor();
    }
    else if (playing != seenPlaying)
    {
        seenPlaying = playing;
        refreshCards();
    }

    keyboard.setNotes (processor.litLow.load(), processor.litHigh.load());

    const int style = (int) processor.apvts.getRawParameterValue ("style")->load() + 1;
    if (styleBox.getSelectedId() != style) styleBox.setSelectedId (style, juce::dontSendNotification);
    if (playButton.getToggleState() != processor.isPreviewPlaying())
        playButton.setToggleState (processor.isPreviewPlaying(), juce::dontSendNotification);
    playButton.setButtonText (processor.isPreviewPlaying() ? "STOP" : "PLAY");
    undoButton.setEnabled (processor.canUndo());
    redoButton.setEnabled (processor.canRedo());
}

void MoyoChordsEditor::paint (juce::Graphics& g)
{
    const float s = getWidth() / 980.0f;
    g.fillAll (moyo::Colours::bg);

    const auto glow = juce::Point<float> (130 * s, 106 * s);
    g.setGradientFill (juce::ColourGradient (moyo::Colours::lime.withAlpha (0.08f), glow, juce::Colours::transparentBlack, glow.translated (260 * s, 0), true));
    g.fillRect (getLocalBounds());

    auto header = getLocalBounds().removeFromTop (juce::roundToInt (70 * s)).toFloat();
    g.setColour (moyo::Colours::lime);
    g.setFont (juce::FontOptions (30.0f * s, juce::Font::bold));
    g.drawText ("MOYO", header.withTrimmedLeft (20 * s), juce::Justification::centredLeft);
    g.setColour (moyo::Colours::text);
    g.setFont (juce::FontOptions (18.0f * s));
    g.drawText ("CHORDS", header.withTrimmedLeft (116 * s), juce::Justification::centredLeft);

    g.setColour (moyo::Colours::track);
    g.drawHorizontalLine (juce::roundToInt (70 * s), 18 * s, getWidth() - 18 * s);
    g.drawHorizontalLine (juce::roundToInt (344 * s), 18 * s, getWidth() - 18 * s);
    g.drawHorizontalLine (juce::roundToInt (496 * s), 18 * s, getWidth() - 18 * s);

    g.setColour (moyo::Colours::subtext.withAlpha (0.6f));
    g.setFont (juce::FontOptions (11.0f * s));
    g.drawText ("v1.0", getLocalBounds().removeFromBottom (juce::roundToInt (16 * s)).withTrimmedRight (juce::roundToInt (22 * s)), juce::Justification::centredRight);
}

void MoyoChordsEditor::resized()
{
    const float s = getWidth() / 980.0f;
    auto S = [s] (float v) { return juce::roundToInt (v * s); };
    auto R = [&] (float x, float y, float w, float h) { return juce::Rectangle<int> (S (x), S (y), S (w), S (h)); };
    const auto labelFont = juce::FontOptions (12.0f * s, juce::Font::bold);

    auto placeMenu = [&] (Menu& m, float x, float y, float w)
    {
        m.label.setFont (labelFont);
        m.label.setBounds (R (x, y, w, 16));
        m.box.setBounds (R (x, y + 17, w, 34));
    };

    // Header: key, scale, style.
    placeMenu (key, 322, 10, 118);
    placeMenu (scale, 450, 10, 190);
    styleLabel.setFont (labelFont);
    styleLabel.setBounds (R (650, 10, 312, 16));
    styleBox.setBounds (R (650, 27, 312, 34));

    // Actions.
    generateButton.setBounds (R (18, 82, 232, 52));
    varyButton.setBounds (R (258, 82, 118, 52));
    undoButton.setBounds (R (386, 82, 44, 52));
    redoButton.setBounds (R (434, 82, 44, 52));
    count.box.setBounds (R (490, 91, 104, 34));
    chordLen.box.setBounds (R (602, 91, 124, 34));
    playButton.setBounds (R (738, 82, 68, 52));
    syncButton.setBounds (R (814, 82, 148, 52));

    // Chord cards.
    const int n = juce::jmax (1, processor.getProgression().count);
    const float gap = 8.0f, total = 944.0f;
    const float cw = (total - gap * (n - 1)) / n;
    for (int i = 0; i < moyo::kMaxSlots; ++i)
        cards[(size_t) i].setBounds (R (18 + i * (cw + gap), 146, cw, 140));

    // Selected-chord editor.
    slotTitle.setFont (juce::FontOptions (15.0f * s, juce::Font::bold));
    slotTitle.setBounds (R (18, 298, 96, 34));
    slotRoot.setBounds (R (118, 298, 178, 34));
    slotQuality.setBounds (R (304, 298, 138, 34));
    slotInversion.setBounds (R (450, 298, 178, 34));
    slotOctave.setBounds (R (636, 298, 140, 34));
    slotLength.setBounds (R (784, 298, 178, 34));

    // Knobs.
    auto placeKnob = [&] (Knob& k, float x, float y, float w, float h)
    {
        k.label.setFont (labelFont);
        k.label.setBounds (R (x, y, w, 16));
        k.slider.setTextBoxStyle (juce::Slider::TextBoxBelow, false, S (w), S (20));
        k.slider.setBounds (R (x, y + 16, w, h - 16));
    };
    Knob* knobs[] = { &complexity, &colour, &strum, &humanise, &swing, &gate };
    for (int i = 0; i < 6; ++i)
        placeKnob (*knobs[i], 18 + i * 100.0f, 354, 96, 134);

    placeMenu (voicing, 632, 354, 160);
    placeMenu (registerMenu, 802, 354, 160);
    placeMenu (bass, 632, 420, 160);
    placeMenu (rhythm, 802, 420, 160);

    // Bottom: keyboard, keys mode, sound, export.
    keyboard.setBounds (R (18, 512, 566, 118));
    keysMode.box.setBounds (R (600, 508, 250, 34));
    sound.box.setBounds (R (858, 508, 104, 34));
    dragZone.setBounds (R (600, 554, 190, 76));
    saveButton.setBounds (R (798, 554, 84, 76));
    placeKnob (volume, 890, 550, 72, 84);
}
