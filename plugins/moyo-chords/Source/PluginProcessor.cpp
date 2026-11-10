#include "PluginProcessor.h"
#include "PluginEditor.h"

namespace
{
const char* const paramIds[] = { "key", "scale", "style", "count", "chordLen", "complexity", "colour", "voicing", "register", "bass",
                                 "rhythm", "strum", "humanise", "swing", "gate", "keysMode", "hostSync", "sound", "volume" };

juce::uint32 randomSeed()
{
    return (juce::uint32) juce::Random::getSystemRandom().nextInt() ^ (juce::uint32) juce::Time::getMillisecondCounter();
}

double beatsForLengthChoice (int choice) { return choice == 0 ? 2.0 : (choice == 1 ? 4.0 : 8.0); }
} // namespace

juce::AudioProcessorValueTreeState::ParameterLayout MoyoChordsProcessor::createLayout()
{
    using Choice = juce::AudioParameterChoice;
    using Float = juce::AudioParameterFloat;
    using ID = juce::ParameterID;
    juce::AudioProcessorValueTreeState::ParameterLayout layout;

    juce::StringArray scaleNames, styleNames, rhythmNames;
    for (const auto& s : moyo::scales()) scaleNames.add (s.name);
    for (const auto& s : moyo::styles()) styleNames.add (s.name);
    for (const auto& p : moyo::patterns()) rhythmNames.add (p.name);

    auto pct = juce::AudioParameterFloatAttributes().withStringFromValueFunction ([] (float v, int) { return juce::String (juce::roundToInt (v)) + "%"; });
    auto ms = juce::AudioParameterFloatAttributes().withStringFromValueFunction ([] (float v, int) { return juce::String (juce::roundToInt (v)) + " ms"; });
    auto db = juce::AudioParameterFloatAttributes().withStringFromValueFunction ([] (float v, int) { return juce::String (v, 1) + " dB"; });

    layout.add (std::make_unique<Choice> (ID { "key", 1 }, "Key", juce::StringArray { "C", "C# / Db", "D", "D# / Eb", "E", "F", "F# / Gb", "G", "G# / Ab", "A", "A# / Bb", "B" }, 0));
    layout.add (std::make_unique<Choice> (ID { "scale", 1 }, "Scale", scaleNames, 1));
    layout.add (std::make_unique<Choice> (ID { "style", 1 }, "Style", styleNames, 0));
    layout.add (std::make_unique<Choice> (ID { "count", 1 }, "Chords", juce::StringArray { "4 chords", "8 chords" }, 0));
    layout.add (std::make_unique<Choice> (ID { "chordLen", 1 }, "Chord Length", juce::StringArray { "1/2 bar each", "1 bar each", "2 bars each" }, 1));
    layout.add (std::make_unique<Float> (ID { "complexity", 1 }, "Complexity", juce::NormalisableRange<float> (0, 100, 1), 50.0f, pct));
    layout.add (std::make_unique<Float> (ID { "colour", 1 }, "Colour", juce::NormalisableRange<float> (0, 100, 1), 35.0f, pct));
    layout.add (std::make_unique<Choice> (ID { "voicing", 1 }, "Voicing", juce::StringArray { "Close", "Open", "Wide", "Shell", "Rootless" }, 1));
    layout.add (std::make_unique<Choice> (ID { "register", 1 }, "Register", juce::StringArray { "Very Low", "Low", "Middle", "High", "Very High" }, 2));
    layout.add (std::make_unique<Choice> (ID { "bass", 1 }, "Bass", juce::StringArray { "No Bass", "Root", "Root + 5th", "Octaves" }, 1));
    layout.add (std::make_unique<Choice> (ID { "rhythm", 1 }, "Rhythm", rhythmNames, 0));
    layout.add (std::make_unique<Float> (ID { "strum", 1 }, "Strum", juce::NormalisableRange<float> (-60, 60, 1), 10.0f, ms));
    layout.add (std::make_unique<Float> (ID { "humanise", 1 }, "Humanise", juce::NormalisableRange<float> (0, 100, 1), 20.0f, pct));
    layout.add (std::make_unique<Float> (ID { "swing", 1 }, "Swing", juce::NormalisableRange<float> (0, 100, 1), 0.0f, pct));
    layout.add (std::make_unique<Float> (ID { "gate", 1 }, "Note Length", juce::NormalisableRange<float> (20, 100, 1), 95.0f, pct));
    layout.add (std::make_unique<Choice> (ID { "keysMode", 1 }, "Keyboard", juce::StringArray { "Keys: one chord per key", "Keys: scale notes play chords", "Keys: off (play through)" }, 0));
    layout.add (std::make_unique<juce::AudioParameterBool> (ID { "hostSync", 1 }, "Play With Song", false));
    layout.add (std::make_unique<Choice> (ID { "sound", 1 }, "Sound", juce::StringArray { "Keys", "Pad", "Pluck", "No sound" }, 0));
    layout.add (std::make_unique<Float> (ID { "volume", 1 }, "Volume", juce::NormalisableRange<float> (-40, 0, 0.1f), -8.0f, db));
    return layout;
}

MoyoChordsProcessor::MoyoChordsProcessor()
    : AudioProcessor (BusesProperties().withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, nullptr, "MoyoChords", createLayout()),
      generator (randomSeed())
{
    pKey = apvts.getRawParameterValue ("key");           pScale = apvts.getRawParameterValue ("scale");
    pStyle = apvts.getRawParameterValue ("style");       pCount = apvts.getRawParameterValue ("count");
    pChordLen = apvts.getRawParameterValue ("chordLen"); pComplexity = apvts.getRawParameterValue ("complexity");
    pColour = apvts.getRawParameterValue ("colour");     pVoicing = apvts.getRawParameterValue ("voicing");
    pRegister = apvts.getRawParameterValue ("register"); pBass = apvts.getRawParameterValue ("bass");
    pRhythm = apvts.getRawParameterValue ("rhythm");     pStrum = apvts.getRawParameterValue ("strum");
    pHumanise = apvts.getRawParameterValue ("humanise"); pSwing = apvts.getRawParameterValue ("swing");
    pGate = apvts.getRawParameterValue ("gate");         pKeysMode = apvts.getRawParameterValue ("keysMode");
    pHostSync = apvts.getRawParameterValue ("hostSync"); pSound = apvts.getRawParameterValue ("sound");
    pVolume = apvts.getRawParameterValue ("volume");

    for (auto* id : paramIds) apvts.addParameterListener (id, this);

    for (int i = 0; i < 16; ++i) synth.addVoice (new moyo::ChordVoice (pSound));
    synth.addSound (new moyo::ChordSound());

    perfSeed = randomSeed();
    generator.generate (prog, (int) pScale->load(), (int) pStyle->load(), pComplexity->load() * 0.01f, pColour->load() * 0.01f);
    pushHistory();
    rebuildSnapshot();
    startTimerHz (30);
}

MoyoChordsProcessor::~MoyoChordsProcessor()
{
    stopTimer();
    for (auto* id : paramIds) apvts.removeParameterListener (id, this);
}

bool MoyoChordsProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    const auto& set = layouts.getMainOutputChannelSet();
    return set == juce::AudioChannelSet::mono() || set == juce::AudioChannelSet::stereo();
}

void MoyoChordsProcessor::prepareToPlay (double sr, int samplesPerBlock)
{
    sampleRate = sr;
    synth.setCurrentPlaybackSampleRate (sr);
    out.ensureSize (4096);
    juce::ignoreUnused (samplesPerBlock);

    synth.allNotesOff (0, false);
    std::fill (std::begin (refCount), std::end (refCount), 0);
    for (auto& h : held) h = {};
    for (auto& p : pending) p = {};
    for (auto& s : seqNotes) s = {};
    numIntents = 0;
    intentOverflow = false;
    std::fill (std::begin (auditionSamplesLeft), std::end (auditionSamplesLeft), 0);
    seqWasRunning = false;
    lastPpqEnd = -1.0e9;
    previewPpq = 0.0;
    lastGain = juce::Decibels::decibelsToGain (pVolume->load());
}

// ============================================================================
// Message thread: progression editing
// ============================================================================

void MoyoChordsProcessor::timerCallback() { flushPendingChanges(); }

void MoyoChordsProcessor::flushPendingChanges()
{
    if (std::abs (currentBpm.load() - cachedBpm) > 0.5) dirty.store (true);
    if (dirty.exchange (false)) rebuildSnapshot();
}

MoyoChordsProcessor::VoicedFixed MoyoChordsProcessor::toFixed (const moyo::Voiced& v)
{
    VoicedFixed f;
    f.numUpper = juce::jmin (8, (int) v.upper.size());
    f.numBass = juce::jmin (2, (int) v.bass.size());
    for (int i = 0; i < f.numUpper; ++i) f.upper[i] = v.upper[(size_t) i];
    for (int i = 0; i < f.numBass; ++i) f.bass[i] = v.bass[(size_t) i];
    return f;
}

void MoyoChordsProcessor::rebuildSnapshot()
{
    const juce::ScopedLock sl (progLock);

    // Chord count and default chord length follow their parameters.
    const int count = pCount->load() > 0.5f ? 8 : 4;
    if (count != cachedCount)
    {
        if (cachedCount >= 0 && count > prog.count)
            for (int i = prog.count; i < count; ++i)
            {
                prog.slots[(size_t) i] = prog.slots[(size_t) (i - 4)];  // repeat the first half
                prog.slots[(size_t) i].locked = false;
            }
        prog.count = count;
        cachedCount = count;
    }
    const int lenChoice = (int) pChordLen->load();
    if (lenChoice != cachedChordLen)
    {
        if (cachedChordLen >= 0)
            for (auto& s : prog.slots) s.beats = beatsForLengthChoice (lenChoice);
        cachedChordLen = lenChoice;
    }

    const int tonic = (int) pKey->load();
    const int scale = (int) pScale->load();
    const int voicing = (int) pVoicing->load();
    const int centre = 60 + 12 * ((int) pRegister->load() - 2);
    const int bass = (int) pBass->load();
    cachedBpm = currentBpm.load();

    const auto voiced = moyo::voiceProgression (prog, tonic, voicing, centre, bass);
    std::vector<double> beats;
    for (int i = 0; i < prog.count; ++i) beats.push_back (prog.slots[(size_t) i].beats);

    moyo::PerfParams pp;
    pp.pattern = (int) pRhythm->load();
    pp.strumMs = pStrum->load();
    pp.humanise = pHumanise->load() * 0.01;
    pp.swing = pSwing->load() * 0.01;
    pp.gate = pGate->load() * 0.01;
    pp.bpm = cachedBpm;
    pp.seed = perfSeed;
    lastSeq = moyo::renderPerformance (voiced, beats, pp);
    lastSeqBeats = prog.totalBeats();

    {
        const juce::SpinLock::ScopedLockType lock (snapLock);
        auto& s = pendingSnap;
        s.numSlots = prog.count;
        double t = 0;
        for (int i = 0; i < prog.count; ++i)
        {
            s.slots[i] = toFixed (voiced[(size_t) i]);
            s.slotStart[i] = t;
            t += prog.slots[(size_t) i].beats;
        }
        s.slotStart[prog.count] = t;
        s.seqBeats = t;

        const auto& sc = moyo::scales()[(size_t) scale];
        const int level = juce::roundToInt (pComplexity->load() * 0.03f);
        for (int d = 0; d < 7; ++d)
        {
            s.scalePcs[d] = sc.pcs[d];
            const int q = moyo::diatonicQuality (scale, sc.pcs[d], level);
            moyo::Voiced v;
            v.upper = moyo::voiceUpper (tonic + sc.pcs[d], q, voicing, centre, {}, 0, bass != moyo::BassOff);
            v.bass = moyo::voiceBass (tonic + sc.pcs[d], q, bass, centre);
            s.degrees[d] = toFixed (v);
        }
        s.tonic = tonic;
        s.seqCount = juce::jmin (maxSeq, (int) lastSeq.size());
        std::copy (lastSeq.begin(), lastSeq.begin() + s.seqCount, s.seq);
        s.strumMs = pStrum->load();
        s.humanise = pHumanise->load() * 0.01f;
        pendingDirty = true;
    }
    uiVersion.fetch_add (1);
}

void MoyoChordsProcessor::pushHistory()
{
    if (historyPos + 1 < (int) history.size()) history.resize ((size_t) (historyPos + 1));
    history.push_back (prog);
    if (history.size() > 60) history.erase (history.begin());
    historyPos = (int) history.size() - 1;
}

moyo::Progression MoyoChordsProcessor::getProgression() const
{
    const juce::ScopedLock sl (progLock);
    return prog;
}

juce::String MoyoChordsProcessor::getChordName (int slot) const
{
    const juce::ScopedLock sl (progLock);
    return moyo::chordName ((int) pKey->load(), (int) pScale->load(), prog.slots[(size_t) juce::jlimit (0, moyo::kMaxSlots - 1, slot)]);
}

juce::String MoyoChordsProcessor::getRomanName (int slot) const
{
    const juce::ScopedLock sl (progLock);
    return moyo::romanName (prog.slots[(size_t) juce::jlimit (0, moyo::kMaxSlots - 1, slot)]);
}

juce::String MoyoChordsProcessor::describeProgression() const
{
    const juce::ScopedLock sl (progLock);
    juce::StringArray names;
    for (int i = 0; i < prog.count; ++i)
        names.add (moyo::chordName ((int) pKey->load(), (int) pScale->load(), prog.slots[(size_t) i]));
    return names.joinIntoString (" ");
}

void MoyoChordsProcessor::generate()
{
    const juce::ScopedLock sl (progLock);
    generator.generate (prog, (int) pScale->load(), (int) pStyle->load(), pComplexity->load() * 0.01f, pColour->load() * 0.01f);
    perfSeed = randomSeed();
    pushHistory();
    rebuildSnapshot();
}

void MoyoChordsProcessor::vary()
{
    const juce::ScopedLock sl (progLock);
    generator.vary (prog, (int) pScale->load(), (int) pStyle->load(), pComplexity->load() * 0.01f, pColour->load() * 0.01f);
    perfSeed = randomSeed();
    pushHistory();
    rebuildSnapshot();
}

void MoyoChordsProcessor::rerollSlot (int slot)
{
    const juce::ScopedLock sl (progLock);
    generator.reroll (prog, slot, (int) pScale->load(), (int) pStyle->load(), pComplexity->load() * 0.01f, pColour->load() * 0.01f);
    pushHistory();
    rebuildSnapshot();
}

void MoyoChordsProcessor::setSlot (int slot, const moyo::Chord& chord)
{
    if (! juce::isPositiveAndBelow (slot, moyo::kMaxSlots)) return;
    const juce::ScopedLock sl (progLock);
    auto c = chord;
    c.root = moyo::mod12 (c.root);
    c.quality = juce::jlimit (0, (int) moyo::NumQualities - 1, c.quality);
    c.inversion = juce::jlimit (-1, 3, c.inversion);
    c.octave = juce::jlimit (-2, 2, c.octave);
    c.beats = juce::jlimit (1.0, 16.0, c.beats);
    prog.slots[(size_t) slot] = c;
    pushHistory();
    rebuildSnapshot();
}

void MoyoChordsProcessor::toggleLock (int slot)
{
    if (! juce::isPositiveAndBelow (slot, moyo::kMaxSlots)) return;
    const juce::ScopedLock sl (progLock);
    prog.slots[(size_t) slot].locked = ! prog.slots[(size_t) slot].locked;
    history[(size_t) historyPos] = prog;  // locks are not an undo step
    uiVersion.fetch_add (1);
}

bool MoyoChordsProcessor::canUndo() const { const juce::ScopedLock sl (progLock); return historyPos > 0; }
bool MoyoChordsProcessor::canRedo() const { const juce::ScopedLock sl (progLock); return historyPos + 1 < (int) history.size(); }

void MoyoChordsProcessor::undo()
{
    const juce::ScopedLock sl (progLock);
    if (historyPos <= 0) return;
    prog = history[(size_t) --historyPos];
    prog.count = cachedCount;
    rebuildSnapshot();
}

void MoyoChordsProcessor::redo()
{
    const juce::ScopedLock sl (progLock);
    if (historyPos + 1 >= (int) history.size()) return;
    prog = history[(size_t) ++historyPos];
    prog.count = cachedCount;
    rebuildSnapshot();
}

void MoyoChordsProcessor::setStyleFromUser (int styleIndex)
{
    styleIndex = juce::jlimit (0, (int) moyo::styles().size() - 1, styleIndex);
    const auto& st = moyo::styles()[(size_t) styleIndex];
    auto set = [this] (const char* id, float value)
    {
        if (auto* p = apvts.getParameter (id))
            p->setValueNotifyingHost (p->convertTo0to1 (value));
    };
    set ("style", (float) styleIndex);
    set ("complexity", st.complexity * 100.0f);
    set ("colour", st.colour * 100.0f);
    set ("voicing", (float) st.voicing);
    set ("rhythm", (float) st.rhythm);
    set ("bass", (float) st.bass);
    set ("swing", st.swing * 100.0f);
    set ("strum", st.strumMs);
}

juce::String MoyoChordsProcessor::suggestedFileName() const
{
    const auto key = apvts.getParameter ("key")->getCurrentValueAsText().upToFirstOccurrenceOf (" ", false, false);
    const auto scale = apvts.getParameter ("scale")->getCurrentValueAsText();
    auto name = "MOYO Chords - " + key + " " + scale + " - " + describeProgression();
    name = name.replaceCharacter ('#', 's').replaceCharacter ('/', '-');
    return juce::File::createLegalFileName (name.substring (0, 90)) + ".mid";
}

bool MoyoChordsProcessor::writeMidiFile (const juce::File& file) const
{
    const juce::ScopedLock sl (progLock);
    constexpr int ppq = 480;
    juce::MidiMessageSequence track;
    track.addEvent (juce::MidiMessage::textMetaEvent (3, "MOYO Chords"), 0.0);
    for (const auto& e : lastSeq)
    {
        const double on = std::round (e.start * ppq);
        const double off = std::max (on + 1.0, std::round ((e.start + e.length) * ppq));
        track.addEvent (juce::MidiMessage::noteOn (1, e.note, (juce::uint8) e.velocity), on);
        track.addEvent (juce::MidiMessage::noteOff (1, e.note), off);
    }
    track.addEvent (juce::MidiMessage::endOfTrack(), std::round (lastSeqBeats * ppq));
    track.sort();
    track.updateMatchedPairs();

    juce::MidiFile mf;
    mf.setTicksPerQuarterNote (ppq);
    mf.addTrack (track);

    file.getParentDirectory().createDirectory();
    file.deleteFile();
    juce::FileOutputStream stream (file);
    return stream.openedOk() && mf.writeTo (stream, 1);
}

// ============================================================================
// State
// ============================================================================

void MoyoChordsProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    auto state = apvts.copyState();
    state.removeChild (state.getChildWithName ("Progression"), nullptr);
    juce::ValueTree p ("Progression");
    {
        const juce::ScopedLock sl (progLock);
        p.setProperty ("count", prog.count, nullptr);
        p.setProperty ("seed", (juce::int64) perfSeed, nullptr);
        for (const auto& c : prog.slots)
        {
            juce::ValueTree ch ("Chord");
            ch.setProperty ("root", c.root, nullptr);
            ch.setProperty ("quality", c.quality, nullptr);
            ch.setProperty ("inversion", c.inversion, nullptr);
            ch.setProperty ("octave", c.octave, nullptr);
            ch.setProperty ("beats", c.beats, nullptr);
            ch.setProperty ("locked", c.locked, nullptr);
            p.appendChild (ch, nullptr);
        }
    }
    state.appendChild (p, nullptr);
    if (auto xml = state.createXml())
        copyXmlToBinary (*xml, destData);
}

void MoyoChordsProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    auto xml = getXmlFromBinary (data, sizeInBytes);
    if (xml == nullptr || ! xml->hasTagName (apvts.state.getType())) return;
    auto state = juce::ValueTree::fromXml (*xml);
    const auto p = state.getChildWithName ("Progression");
    state.removeChild (p, nullptr);
    apvts.replaceState (state);

    const juce::ScopedLock sl (progLock);
    if (p.isValid())
    {
        prog.count = juce::jlimit (1, moyo::kMaxSlots, (int) p.getProperty ("count", 4)) > 4 ? 8 : 4;
        perfSeed = (juce::uint32) (juce::int64) p.getProperty ("seed", 1);
        for (int i = 0; i < juce::jmin (moyo::kMaxSlots, p.getNumChildren()); ++i)
        {
            const auto ch = p.getChild (i);
            auto& c = prog.slots[(size_t) i];
            c.root = moyo::mod12 ((int) ch.getProperty ("root", 0));
            c.quality = juce::jlimit (0, (int) moyo::NumQualities - 1, (int) ch.getProperty ("quality", 0));
            c.inversion = juce::jlimit (-1, 3, (int) ch.getProperty ("inversion", -1));
            c.octave = juce::jlimit (-2, 2, (int) ch.getProperty ("octave", 0));
            c.beats = juce::jlimit (1.0, 16.0, (double) ch.getProperty ("beats", 4.0));
            c.locked = (bool) ch.getProperty ("locked", false);
        }
    }
    // Adopt the restored count / length choices without rewriting the restored chords.
    cachedCount = -1;
    cachedChordLen = -1;
    history.clear();
    historyPos = -1;
    pushHistory();
    rebuildSnapshot();
}

// ============================================================================
// Audio thread
// ============================================================================

void MoyoChordsProcessor::pullSnapshot()
{
    const juce::SpinLock::ScopedTryLockType lock (snapLock);
    if (lock.isLocked() && pendingDirty)
    {
        live = pendingSnap;
        pendingDirty = false;
    }
}

void MoyoChordsProcessor::pushIntent (int pos, int note, int velocity)
{
    if (numIntents >= maxIntents) { intentOverflow = true; return; }
    intents[numIntents] = { pos, numIntents, note, velocity };
    ++numIntents;
}

void MoyoChordsProcessor::noteOnOut (int note, int velocity, int pos)
{
    if (juce::isPositiveAndBelow (note, 128)) pushIntent (pos, note, juce::jlimit (1, 127, velocity));
}

void MoyoChordsProcessor::noteOffOut (int note, int pos)
{
    if (juce::isPositiveAndBelow (note, 128)) pushIntent (pos, note, 0);
}

void MoyoChordsProcessor::resolveIntents (int numSamples)
{
    std::sort (intents, intents + numIntents, [] (const Intent& a, const Intent& b) { return a.pos != b.pos ? a.pos < b.pos : a.order < b.order; });

    for (int i = 0; i < numIntents; ++i)
    {
        const auto& in = intents[i];
        const int pos = juce::jlimit (0, juce::jmax (0, numSamples - 1), in.pos);
        if (in.note < 0)
        {
            for (int n = 0; n < 128; ++n)
                if (refCount[n] > 0) { refCount[n] = 0; out.addEvent (juce::MidiMessage::noteOff (1, n), pos); }
        }
        else if (in.velocity > 0)
        {
            if (refCount[in.note] > 0) out.addEvent (juce::MidiMessage::noteOff (1, in.note), pos);  // retrigger cleanly
            ++refCount[in.note];
            out.addEvent (juce::MidiMessage::noteOn (1, in.note, (juce::uint8) in.velocity), pos);
        }
        else if (refCount[in.note] > 0 && --refCount[in.note] == 0)
            out.addEvent (juce::MidiMessage::noteOff (1, in.note), pos);
    }
    numIntents = 0;

    if (intentOverflow)
    {
        // Far more notes than any real use produces: stop everything rather than risk a stuck note.
        intentOverflow = false;
        for (int n = 0; n < 128; ++n)
            if (refCount[n] > 0) { refCount[n] = 0; out.addEvent (juce::MidiMessage::noteOff (1, n), juce::jmax (0, numSamples - 1)); }
        for (auto& h : held) h.active = false;
        for (auto& p : pending) p.used = false;
        for (auto& sn : seqNotes) sn.used = false;
    }
}

void MoyoChordsProcessor::keyDown (int key, const VoicedFixed& chord, int shift, int velocity, int pos, bool exact)
{
    keyUp (key, pos);
    auto& h = held[key];
    h = {};
    h.active = true;

    int notes[maxChordNotes];
    int total = 0;
    for (int i = 0; i < chord.numBass && total < maxChordNotes; ++i) notes[total++] = chord.bass[i] + shift;
    const int firstUpper = total;
    for (int i = 0; i < chord.numUpper && total < maxChordNotes; ++i) notes[total++] = chord.upper[i] + shift;

    const int strumSamples = (int) (std::abs (live.strumMs) * 0.001 * sampleRate);
    for (int i = 0; i < total; ++i)
    {
        const int note = notes[i];
        if (note < 0 || note > 127) continue;
        const int order = live.strumMs >= 0 ? i : total - 1 - i;
        int delay = 0, vel = velocity;
        if (! exact)
        {
            delay = order * strumSamples + (int) (audioRandom.nextFloat() * live.humanise * 0.010f * (float) sampleRate);
            vel += i == total - 1 ? 5 : (i < firstUpper ? -4 : 0);
            vel += (int) ((audioRandom.nextFloat() * 2.0f - 1.0f) * live.humanise * 12.0f);
        }

        const int k = h.count++;
        h.notes[k] = note;
        if (delay <= 0)
        {
            noteOnOut (note, vel, pos);
            h.started[k] = true;
            continue;
        }
        Pending* slot = nullptr;
        for (auto& p : pending)
            if (! p.used) { slot = &p; break; }
        if (slot == nullptr)
        {
            noteOnOut (note, vel, pos);
            h.started[k] = true;
        }
        else
            *slot = { true, pos + delay, note, juce::jlimit (1, 127, vel), key, k };
    }
}

void MoyoChordsProcessor::keyUp (int key, int pos)
{
    auto& h = held[key];
    if (! h.active) return;
    for (int i = 0; i < h.count; ++i)
        if (h.started[i]) noteOffOut (h.notes[i], pos);
    for (auto& p : pending)
        if (p.used && p.key == key) p.used = false;
    h.active = false;
}

void MoyoChordsProcessor::flushPendingNotes (int numSamples)
{
    for (auto& p : pending)
    {
        if (! p.used) continue;
        if (p.samples < numSamples)
        {
            noteOnOut (p.note, p.velocity, juce::jmax (0, p.samples));
            held[p.key].started[p.index] = true;
            p.used = false;
        }
        else
            p.samples -= numSamples;
    }
}

void MoyoChordsProcessor::releaseSequence (int pos)
{
    for (auto& s : seqNotes)
        if (s.used) { noteOffOut (s.note, pos); s.used = false; }
}

void MoyoChordsProcessor::runSequence (double p0, double p1, int numSamples)
{
    if (std::abs (p0 - lastPpqEnd) > 0.02) releaseSequence (0);  // the transport jumped or looped
    lastPpqEnd = p1;
    const double span = p1 - p0;
    if (span <= 0 || live.seqCount == 0 || live.seqBeats <= 0) return;
    auto toSample = [&] (double ppq) { return juce::jlimit (0, numSamples - 1, (int) ((ppq - p0) / span * numSamples)); };

    for (auto& s : seqNotes)
        if (s.used && s.endPpq < p1)
        {
            noteOffOut (s.note, toSample (s.endPpq));
            s.used = false;
        }

    const double loop = live.seqBeats;
    const double firstLoop = std::floor (p0 / loop);
    for (int k = 0; k < 2; ++k)
    {
        const double base = (firstLoop + k) * loop;
        if (base >= p1) break;
        for (int i = 0; i < live.seqCount; ++i)
        {
            const auto& e = live.seq[i];
            const double t = base + e.start;
            if (t >= p1) break;  // sorted by start
            if (t < p0) continue;
            const int pos = toSample (t);
            const double end = t + e.length;

            SeqNote* slot = nullptr;
            for (auto& s : seqNotes)
            {
                if (s.used && s.note == e.note) { noteOffOut (s.note, pos); s.used = false; }  // same note again: end the old one
                if (! s.used && slot == nullptr) slot = &s;
            }
            if (slot == nullptr) continue;  // more simultaneous notes than we track: skip rather than risk a stuck note
            noteOnOut (e.note, e.velocity, pos);
            if (end < p1)
                noteOffOut (e.note, juce::jmax (pos + 1 < numSamples ? pos + 1 : pos, toSample (end)));
            else
                *slot = { true, e.note, end };
        }
    }
}

void MoyoChordsProcessor::panic (int pos)
{
    pushIntent (pos, -1, 0);
    for (auto& h : held) h.active = false;
    for (auto& p : pending) p.used = false;
    for (auto& s : seqNotes) s.used = false;
    std::fill (std::begin (auditionSamplesLeft), std::end (auditionSamplesLeft), 0);
}

void MoyoChordsProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi)
{
    juce::ScopedNoDenormals noDenormals;
    const int n = buffer.getNumSamples();
    buffer.clear();
    out.clear();
    pullSnapshot();

    double bpm = 120.0, hostPpq = 0.0;
    bool hostPlaying = false;
    if (auto* ph = getPlayHead())
        if (auto pos = ph->getPosition())
        {
            if (auto b = pos->getBpm()) bpm = *b;
            if (auto p = pos->getPpqPosition()) hostPpq = *p;
            hostPlaying = pos->getIsPlaying();
        }
    if (bpm < 20.0 || bpm > 999.0) bpm = 120.0;
    currentBpm.store (bpm);

    const int mode = (int) pKeysMode->load();

    // 1. Incoming MIDI: keys become chords.
    for (const auto meta : midi)
    {
        const auto msg = meta.getMessage();
        const int pos = juce::jlimit (0, juce::jmax (0, n - 1), meta.samplePosition);

        if (msg.isNoteOn())
        {
            const int key = msg.getNoteNumber();
            if (mode == KeysOff)
            {
                // Play through: the key itself, exactly as played.
                VoicedFixed single;
                single.numUpper = 1;
                single.upper[0] = key;
                keyDown (key, single, 0, msg.getVelocity(), pos, true);
                continue;
            }

            if (mode == KeysChords)
            {
                // White keys from middle C step through the chords; each further run of keys is an octave higher.
                static const int whiteIndex[12] = { 0, -1, 1, -1, 2, 3, -1, 4, -1, 5, -1, 6 };
                const int w = whiteIndex[key % 12];
                if (w < 0 || live.numSlots <= 0) continue;
                const int white = (key / 12 - 5) * 7 + w;
                const int slot = ((white % live.numSlots) + live.numSlots) % live.numSlots;
                const int octave = (int) std::floor ((double) white / live.numSlots);
                keyDown (key, live.slots[slot], 12 * octave, msg.getVelocity(), pos);
                lastTriggeredSlot = slot;
            }
            else
            {
                const int rel = moyo::mod12 (key - live.tonic);
                int degree = 0;
                for (int d = 0; d < 7; ++d)
                    if (live.scalePcs[d] <= rel) degree = d;
                keyDown (key, live.degrees[degree], 12 * (int) std::floor ((key - 60) / 12.0), msg.getVelocity(), pos);
                lastTriggeredSlot = -1;
            }
        }
        else if (msg.isNoteOff())
        {
            keyUp (msg.getNoteNumber(), pos);
        }
        else if (msg.isAllNotesOff() || msg.isAllSoundOff())
        {
            panic (pos);
            out.addEvent (msg, pos);
        }
        else
            out.addEvent (msg, pos);
    }

    // 2. Clicking a chord in the window auditions it for a moment.
    const int audition = auditionRequest.exchange (-1);
    if (juce::isPositiveAndBelow (audition, live.numSlots))
    {
        keyDown (128 + audition, live.slots[audition], 0, 96, 0);
        auditionSamplesLeft[audition] = (int) (sampleRate * 1.3);
        lastTriggeredSlot = audition;
    }
    for (int i = 0; i < moyo::kMaxSlots; ++i)
        if (auditionSamplesLeft[i] > 0 && (auditionSamplesLeft[i] -= n) <= 0)
            keyUp (128 + i, juce::jmax (0, n - 1));

    // 3. The progression itself, following the song or the Play button.
    const bool syncToHost = hostPlaying && pHostSync->load() > 0.5f;
    if (syncToHost) previewPlaying.store (false);
    const bool preview = previewPlaying.load();
    const double beatsPerSample = bpm / (60.0 * sampleRate);
    int slotNow = -1;

    if (syncToHost || preview)
    {
        const double p0 = syncToHost ? hostPpq : previewPpq;
        runSequence (p0, p0 + n * beatsPerSample, n);
        if (preview) previewPpq += n * beatsPerSample;
        if (live.seqBeats > 0)
        {
            const double beat = p0 - std::floor (p0 / live.seqBeats) * live.seqBeats;
            for (int i = 0; i < live.numSlots; ++i)
                if (beat >= live.slotStart[i]) slotNow = i;
        }
        seqWasRunning = true;
    }
    else if (seqWasRunning)
    {
        releaseSequence (0);
        seqWasRunning = false;
        lastPpqEnd = -1.0e9;
    }
    if (! preview) previewPpq = 0.0;

    // 4. Strummed notes that are due in this block, then turn all the requests into MIDI in time order.
    flushPendingNotes (n);
    resolveIntents (n);

    // 5. Display state.
    juce::uint64 lo = 0, hi = 0;
    for (int i = 0; i < 64; ++i)
    {
        if (refCount[i] > 0) lo |= (juce::uint64) 1 << i;
        if (refCount[i + 64] > 0) hi |= (juce::uint64) 1 << i;
    }
    litLow.store (lo);
    litHigh.store (hi);
    if (lo == 0 && hi == 0 && slotNow < 0) lastTriggeredSlot = -1;
    playingSlot.store (slotNow >= 0 ? slotNow : lastTriggeredSlot);

    // 6. Built-in sound.
    if ((int) pSound->load() != moyo::SoundOff)
    {
        synth.renderNextBlock (buffer, out, 0, n);
        const float gain = juce::Decibels::decibelsToGain (pVolume->load());
        buffer.applyGainRamp (0, n, lastGain, gain);
        lastGain = gain;
        for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
        {
            float* d = buffer.getWritePointer (ch);
            for (int i = 0; i < n; ++i) d[i] = std::tanh (d[i]);  // gentle safety limit for big chords
        }
    }
    else
        synth.allNotesOff (0, false);

    midi.swapWith (out);
}

juce::AudioProcessorEditor* MoyoChordsProcessor::createEditor()
{
    return new MoyoChordsEditor (*this);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new MoyoChordsProcessor();
}
