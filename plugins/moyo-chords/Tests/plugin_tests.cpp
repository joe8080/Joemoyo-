// Plugin tests for MOYO Chords: real-time MIDI handling, host sync, state and MIDI export.
// Built when configuring with -DMOYO_BUILD_TESTS=ON. Set SHOT=/path/file.png to also render the editor.

#include <cstdio>
#include <map>
#include <set>
#include "PluginEditor.h"
#include "PluginProcessor.h"

static int failures = 0;
#define CHECK(cond, ...) do { if (!(cond)) { ++failures; std::printf ("FAIL: "); } else std::printf ("ok:   "); std::printf (__VA_ARGS__); std::printf ("\n"); } while (0)

struct TestPlayHead : juce::AudioPlayHead
{
    bool playing = false;
    double ppq = 0.0, bpm = 120.0;
    juce::Optional<PositionInfo> getPosition() const override
    {
        PositionInfo p;
        p.setBpm (bpm);
        p.setPpqPosition (ppq);
        p.setIsPlaying (playing);
        return p;
    }
};

struct OutEvent { juce::int64 sample; double ppq; bool on; int note, velocity; };

// Runs the plugin block by block and keeps a record of everything it sends out.
struct Rig
{
    MoyoChordsProcessor proc;
    TestPlayHead head;
    double sr = 48000.0;
    int block = 256;
    juce::int64 clock = 0;
    std::vector<OutEvent> log;
    std::map<int, int> sounding;
    int unmatchedOffs = 0, doubleOns = 0;
    float peak = 0.0f;
    bool finite = true;

    Rig()
    {
        proc.setPlayHead (&head);
        proc.setPlayConfigDetails (0, 2, sr, block);
        proc.prepareToPlay (sr, block);
    }

    void set (const char* id, float value)
    {
        auto* p = proc.apvts.getParameter (id);
        p->setValueNotifyingHost (p->convertTo0to1 (value));
        proc.flushPendingChanges();
    }

    void run (int numBlocks, juce::MidiBuffer in = {})
    {
        for (int b = 0; b < numBlocks; ++b)
        {
            juce::AudioBuffer<float> audio (2, block);
            juce::MidiBuffer midi;
            if (b == 0) midi = in;
            const double startPpq = head.ppq;
            proc.processBlock (audio, midi);
            for (const auto meta : midi)
            {
                const auto m = meta.getMessage();
                if (! m.isNoteOnOrOff()) continue;
                const double ppq = startPpq + meta.samplePosition * head.bpm / (60.0 * sr);
                log.push_back ({ clock + meta.samplePosition, ppq, m.isNoteOn(), m.getNoteNumber(), m.getVelocity() });
                if (m.isNoteOn()) { if (sounding[m.getNoteNumber()]++ > 0) ++doubleOns; }
                else if (--sounding[m.getNoteNumber()] < 0) { ++unmatchedOffs; sounding[m.getNoteNumber()] = 0; }
            }
            for (int ch = 0; ch < 2; ++ch)
                for (int i = 0; i < block; ++i)
                {
                    const float v = audio.getSample (ch, i);
                    finite &= std::isfinite (v);
                    peak = std::max (peak, std::abs (v));
                }
            clock += block;
            if (head.playing) head.ppq += block * head.bpm / (60.0 * sr);
        }
    }

    int soundingCount() const
    {
        int n = 0;
        for (const auto& kv : sounding) n += kv.second > 0;
        return n;
    }
    std::set<int> soundingNotes() const
    {
        std::set<int> s;
        for (const auto& kv : sounding) if (kv.second > 0) s.insert (kv.first);
        return s;
    }
    static juce::MidiBuffer noteOn (int note, int vel = 100, int pos = 0) { juce::MidiBuffer b; b.addEvent (juce::MidiMessage::noteOn (1, note, (juce::uint8) vel), pos); return b; }
    static juce::MidiBuffer noteOff (int note, int pos = 0) { juce::MidiBuffer b; b.addEvent (juce::MidiMessage::noteOff (1, note), pos); return b; }
};

// The notes the plugin's own MIDI export contains: (start beat, note).
static std::vector<std::pair<double, int>> exportedNotes (MoyoChordsProcessor& p, double* lengthBeats = nullptr)
{
    const auto file = juce::File::getSpecialLocation (juce::File::tempDirectory).getChildFile ("moyo_chords_test_" + juce::String (juce::Random::getSystemRandom().nextInt (1000000)) + ".mid");
    std::vector<std::pair<double, int>> notes;
    if (! p.writeMidiFile (file)) return notes;
    juce::FileInputStream in (file);
    juce::MidiFile mf;
    if (in.openedOk() && mf.readFrom (in) && mf.getNumTracks() > 0)
    {
        const double tpq = mf.getTimeFormat();
        const auto* track = mf.getTrack (0);
        for (int i = 0; i < track->getNumEvents(); ++i)
        {
            const auto& m = track->getEventPointer (i)->message;
            if (m.isNoteOn()) notes.push_back ({ m.getTimeStamp() / tpq, m.getNoteNumber() });
            if (m.isEndOfTrackMetaEvent() && lengthBeats != nullptr) *lengthBeats = m.getTimeStamp() / tpq;
        }
    }
    file.deleteFile();
    return notes;
}

int main()
{
    juce::ScopedJuceInitialiser_GUI gui;

    // ---- 1. One chord per key ------------------------------------------------
    {
        Rig r;
        r.set ("strum", 0); r.set ("humanise", 0); r.set ("bass", 1);
        r.run (2, Rig::noteOn (60));
        const auto first = r.soundingNotes();
        CHECK (first.size() >= 4 && r.log.size() == first.size(), "middle C plays chord 1: %d notes sounding (%s)", (int) first.size(), r.proc.getChordName (0).toRawUTF8());
        bool sameBlockStart = true;
        for (const auto& e : r.log) sameBlockStart &= e.sample == 0;
        CHECK (sameBlockStart, "with strum at 0 every note starts together");
        r.run (2, Rig::noteOff (60));
        CHECK (r.soundingCount() == 0 && r.unmatchedOffs == 0, "releasing the key stops every note");

        // An octave of white keys up: with 4 chords, the next C (72) is chord 4, one octave higher.
        r.log.clear();
        r.run (2, Rig::noteOn (65));  // F = 4th white key = chord 4
        const auto chord4 = r.soundingNotes();
        r.run (2, Rig::noteOff (65));
        r.run (2, Rig::noteOn (72));
        const auto chord4up = r.soundingNotes();
        r.run (2, Rig::noteOff (72));
        std::set<int> shifted;
        for (int n : chord4) shifted.insert (n + 12);
        CHECK (! chord4.empty() && chord4up == shifted, "the next octave of keys plays the same chords an octave higher");

        r.log.clear();
        r.run (2, Rig::noteOn (61));
        CHECK (r.log.empty(), "black keys are ignored in one-chord-per-key mode");
        r.run (1, Rig::noteOff (61));

        // Strum: notes start one after another, low to high.
        r.set ("strum", 30);
        r.log.clear();
        r.run (40, Rig::noteOn (60));
        bool ascending = true, spaced = true;
        for (size_t i = 1; i < r.log.size(); ++i)
        {
            ascending &= r.log[i].note > r.log[i - 1].note;
            spaced &= std::abs ((double) (r.log[i].sample - r.log[i - 1].sample) - 0.030 * r.sr) < 2.0;
        }
        CHECK (r.log.size() == first.size() && ascending && spaced, "strum 30 ms: notes start low to high, 30 ms apart");
        r.run (2, Rig::noteOff (60));
        CHECK (r.soundingCount() == 0, "releasing a strummed chord stops every note");

        // Releasing mid-strum must not leave late notes behind.
        r.run (1, Rig::noteOn (62));
        r.run (1, Rig::noteOff (62));
        r.run (60);
        CHECK (r.soundingCount() == 0 && r.unmatchedOffs == 0, "a key released mid-strum leaves nothing hanging");
    }

    // ---- 2. Scale-degree mode and pass-through ---------------------------------
    {
        Rig r;
        r.set ("strum", 0); r.set ("humanise", 0); r.set ("keysMode", 1); r.set ("key", 0); r.set ("scale", 1); r.set ("complexity", 0); r.set ("bass", 0); r.set ("voicing", 0);
        bool inKey = true, rootsRight = true;
        const int cMinor[7] = { 0, 2, 3, 5, 7, 8, 10 };
        for (int d = 0; d < 7; ++d)
        {
            const int keyNote = 60 + cMinor[d];
            r.run (2, Rig::noteOn (keyNote));
            const auto notes = r.soundingNotes();
            std::set<int> pcs;
            for (int n : notes)
            {
                pcs.insert (n % 12);
                inKey &= std::find (std::begin (cMinor), std::end (cMinor), n % 12) != std::end (cMinor);
            }
            rootsRight &= notes.size() == 3 && *notes.begin() % 12 == cMinor[d];
            r.run (2, Rig::noteOff (keyNote));
        }
        CHECK (inKey && rootsRight, "scale mode: each C minor note plays its own in-key triad, root at the bottom");

        r.set ("keysMode", 2);
        r.log.clear();
        r.run (2, Rig::noteOn (61, 77));
        CHECK (r.log.size() == 1 && r.log[0].note == 61 && r.log[0].velocity == 77, "keys off: notes pass straight through");
        r.run (2, Rig::noteOff (61));
        CHECK (r.soundingCount() == 0, "keys off: note-offs pass through too");
    }

    // ---- 3. Playing along with the host ----------------------------------------
    {
        Rig r;
        r.set ("hostSync", 1); r.set ("humanise", 30); r.set ("strum", 15); r.set ("rhythm", 8); r.set ("swing", 30);
        double lengthBeats = 0;
        const auto expected = exportedNotes (r.proc, &lengthBeats);
        r.head.playing = true;
        const int blocksPerLoop = (int) std::ceil (lengthBeats * 60.0 / r.head.bpm * r.sr / r.block);
        r.run (blocksPerLoop * 2 + 3);

        // A note due exactly on the loop point is logged a fraction of a sample early, so split loops just before it.
        const double edge = 0.0005;
        std::vector<std::pair<double, int>> played;
        for (const auto& e : r.log)
            if (e.on && e.ppq < lengthBeats - edge) played.push_back ({ e.ppq, e.note });
        const double tolerance = r.block * r.head.bpm / (60.0 * r.sr) + 0.01;
        bool match = played.size() == expected.size();
        for (size_t i = 0; match && i < played.size(); ++i)
        {
            bool found = false;
            for (const auto& x : expected) found |= x.second == played[i].second && std::abs (x.first - played[i].first) < tolerance;
            match &= found;
        }
        CHECK (std::abs (lengthBeats - 16.0) < 1.0e-6 && ! expected.empty(), "exported MIDI: %d notes over %.0f beats", (int) expected.size(), lengthBeats);
        CHECK (match, "play-with-song output matches the exported MIDI note for note (%d vs %d notes)", (int) played.size(), (int) expected.size());

        int secondLoop = 0;
        for (const auto& e : r.log) secondLoop += e.on && e.ppq >= lengthBeats - edge && e.ppq < 2 * lengthBeats - edge;
        CHECK (secondLoop == (int) expected.size(), "the progression loops: second pass plays %d notes", secondLoop);

        r.head.playing = false;
        r.run (4);
        CHECK (r.soundingCount() == 0 && r.unmatchedOffs == 0, "stopping the song stops every note");

        // Jumping around the timeline must not leave notes stuck.
        r.head.playing = true;
        for (int j = 0; j < 30; ++j)
        {
            r.head.ppq = (j * 37) % 200 * 0.37;
            r.run (7);
        }
        r.head.playing = false;
        r.run (4);
        CHECK (r.soundingCount() == 0 && r.unmatchedOffs == 0, "30 timeline jumps leave no stuck notes");

        // With sync off, the song playing does nothing.
        r.set ("hostSync", 0);
        r.log.clear();
        r.head.playing = true;
        r.run (200);
        r.head.playing = false;
        CHECK (r.log.empty(), "play-with-song off: the plugin stays quiet while the song plays");
    }

    // ---- 4. Preview button and audition -----------------------------------------
    {
        Rig r;
        r.proc.setPreviewPlaying (true);
        r.run (800);
        int ons = 0;
        for (const auto& e : r.log) ons += e.on;
        CHECK (ons > 8, "PLAY button plays the progression without the host (%d notes)", ons);
        r.proc.setPreviewPlaying (false);
        r.run (4);
        CHECK (r.soundingCount() == 0, "STOP releases every note");

        r.log.clear();
        r.proc.auditionSlot (2);
        r.run (10);
        const int during = r.soundingCount();
        r.run ((int) (1.5 * r.sr / r.block));
        CHECK (during >= 3 && r.soundingCount() == 0, "clicking a chord plays it (%d notes) and it stops by itself", during);
    }

    // ---- 5. Built-in sound --------------------------------------------------------
    {
        Rig r;
        bool allSound = true;
        for (int snd = 0; snd < 3; ++snd)
        {
            r.set ("sound", (float) snd);
            r.peak = 0;
            r.run (60, Rig::noteOn (60));
            allSound &= r.peak > 0.02f && r.peak <= 1.0f;
            r.run (300, Rig::noteOff (60));
        }
        CHECK (allSound && r.finite, "Keys, Pad and Pluck all make sound and stay under full scale");
        r.set ("sound", 3);
        r.run (20);
        r.peak = 0; r.log.clear();
        r.run (40, Rig::noteOn (60));
        CHECK (r.peak == 0.0f && ! r.log.empty(), "'No sound' is silent but still sends MIDI out");
        r.run (2, Rig::noteOff (60));
    }

    // ---- 6. Editing: generate, vary, undo, count and length ----------------------
    {
        Rig r;
        const auto a = r.proc.describeProgression();
        std::set<juce::String> seen { a };
        for (int i = 0; i < 25; ++i) { r.proc.generate(); seen.insert (r.proc.describeProgression()); }
        CHECK (seen.size() > 15, "GENERATE gives variety: %d different progressions in 25 presses", (int) seen.size());

        const auto before = r.proc.describeProgression();
        r.proc.generate();
        const auto after = r.proc.describeProgression();
        r.proc.undo();
        const bool undone = r.proc.describeProgression() == before;
        r.proc.redo();
        CHECK (undone && r.proc.describeProgression() == after && ! r.proc.canRedo(), "undo and redo step through the history");

        r.set ("count", 1);
        const auto p8 = r.proc.getProgression();
        bool repeated = p8.count == 8;
        for (int i = 0; i < 4; ++i) repeated &= p8.slots[(size_t) i].sameHarmony (p8.slots[(size_t) i + 4]);
        CHECK (repeated, "switching to 8 chords repeats the first four as a starting point");

        r.set ("chordLen", 2);
        double len = 0;
        exportedNotes (r.proc, &len);
        CHECK (std::abs (len - 64.0) < 1.0e-6, "8 chords at 2 bars each = %.0f beats", len);

        auto c = r.proc.getProgression().slots[1];
        c.root = 8; c.quality = moyo::Maj9; c.beats = 2.0;
        r.proc.setSlot (1, c);
        r.set ("key", 0); r.set ("scale", 1);
        CHECK (r.proc.getChordName (1) == "Abmaj9" && r.proc.getRomanName (1) == "bVImaj9", "editing a chord by hand: %s (%s)", r.proc.getChordName (1).toRawUTF8(), r.proc.getRomanName (1).toRawUTF8());
        r.set ("key", 2);
        CHECK (r.proc.getChordName (1) == "Bbmaj9", "changing key transposes it: %s", r.proc.getChordName (1).toRawUTF8());

        r.proc.toggleLock (1);
        for (int i = 0; i < 20; ++i) r.proc.generate();
        CHECK (r.proc.getChordName (1) == "Bbmaj9", "a locked chord survives 20 generates");

        r.proc.setStyleFromUser (5);
        r.proc.flushPendingChanges();
        CHECK (std::abs (r.proc.apvts.getRawParameterValue ("complexity")->load() - 85.0f) < 0.5f && (int) r.proc.apvts.getRawParameterValue ("voicing")->load() == 4,
               "picking Lo-fi / Jazz loads its settings (complexity 85%%, rootless voicing)");
    }

    // ---- 7. State ------------------------------------------------------------------
    {
        Rig a;
        a.set ("key", 7); a.set ("scale", 4); a.set ("count", 1); a.set ("rhythm", 12); a.set ("strum", -25); a.set ("humanise", 40);
        for (int i = 0; i < 5; ++i) a.proc.generate();
        a.proc.toggleLock (3);
        juce::MemoryBlock mb;
        a.proc.getStateInformation (mb);

        Rig b;
        b.proc.setStateInformation (mb.getData(), (int) mb.getSize());
        b.proc.flushPendingChanges();
        const auto pa = a.proc.getProgression(), pb = b.proc.getProgression();
        bool same = pa.count == pb.count && a.proc.describeProgression() == b.proc.describeProgression() && pb.slots[3].locked;
        const auto ea = exportedNotes (a.proc), eb = exportedNotes (b.proc);
        same &= ea == eb && ! ea.empty();
        CHECK (same, "saving and reloading a project restores the progression and plays identically (%s)", b.proc.describeProgression().toRawUTF8());
        CHECK (a.proc.suggestedFileName().endsWith (".mid") && juce::File::createLegalFileName (a.proc.suggestedFileName()) == a.proc.suggestedFileName(),
               "MIDI file name is legal: %s", a.proc.suggestedFileName().toRawUTF8());
    }

    // ---- 8. Stress: everything at once ----------------------------------------------
    {
        Rig r;
        r.set ("hostSync", 1);
        juce::Random rnd (4242);
        std::set<int> down;
        const char* choiceParams[] = { "key", "scale", "voicing", "register", "bass", "rhythm", "keysMode", "sound", "count", "chordLen" };
        const char* floatParams[] = { "strum", "humanise", "swing", "gate", "complexity", "colour" };
        for (int step = 0; step < 4000; ++step)
        {
            juce::MidiBuffer in;
            const int events = rnd.nextInt (4);
            for (int e = 0; e < events; ++e)
            {
                const int note = 36 + rnd.nextInt (60);
                const int pos = rnd.nextInt (r.block);
                if (down.count (note)) { in.addEvent (juce::MidiMessage::noteOff (1, note), pos); down.erase (note); }
                else { in.addEvent (juce::MidiMessage::noteOn (1, note, (juce::uint8) (1 + rnd.nextInt (127))), pos); down.insert (note); }
            }
            const int action = rnd.nextInt (60);
            if (action == 0) r.proc.generate();
            else if (action == 1) r.proc.vary();
            else if (action == 2) r.proc.rerollSlot (rnd.nextInt (8));
            else if (action == 3) r.head.playing = ! r.head.playing;
            else if (action == 4) r.head.ppq = rnd.nextDouble() * 300.0;
            else if (action == 5) r.proc.auditionSlot (rnd.nextInt (8));
            else if (action == 6) r.proc.setPreviewPlaying (rnd.nextBool());
            else if (action == 7) r.head.bpm = 60.0 + rnd.nextInt (120);
            else if (action < 12)
            {
                auto* p = r.proc.apvts.getParameter (choiceParams[rnd.nextInt (10)]);
                p->setValueNotifyingHost (rnd.nextFloat());
            }
            else if (action < 16)
            {
                auto* p = r.proc.apvts.getParameter (floatParams[rnd.nextInt (6)]);
                p->setValueNotifyingHost (rnd.nextFloat());
            }
            r.proc.flushPendingChanges();
            r.run (1, in);
        }
        // Let go of everything and stop.
        juce::MidiBuffer release;
        for (int note : down) release.addEvent (juce::MidiMessage::noteOff (1, note), 0);
        r.head.playing = false;
        r.proc.setPreviewPlaying (false);
        r.set ("keysMode", 0);
        r.run ((int) (3.0 * r.sr / r.block), release);
        int ons = 0;
        for (const auto& e : r.log) ons += e.on;
        CHECK (r.soundingCount() == 0, "stress test (%d notes played, 4000 random steps): no stuck notes", ons);
        CHECK (r.unmatchedOffs == 0 && r.doubleOns == 0, "stress test: every note-on has exactly one note-off (%d stray offs, %d doubled ons)", r.unmatchedOffs, r.doubleOns);
        CHECK (r.finite && r.peak <= 1.0f, "stress test: audio stays clean (peak %.2f)", r.peak);
    }

    // ---- 9. The window (only when a screenshot path is given) ------------------------
    if (const char* shot = std::getenv ("SHOT"))
    {
        Rig r;
        r.set ("key", 0); r.set ("scale", 1);
        r.proc.setStyleFromUser (2);
        r.proc.flushPendingChanges();
        r.proc.generate();
        r.proc.toggleLock (1);
        std::unique_ptr<juce::AudioProcessorEditor> ed (r.proc.createEditor());
        ed->setSize (980, 650);
        r.run (60, Rig::noteOn (62));
        juce::MessageManager::getInstance()->runDispatchLoopUntil (300);
        auto img = ed->createComponentSnapshot (ed->getLocalBounds(), true, 2.0f);
        juce::File outFile { juce::String (shot) };
        outFile.deleteFile();
        juce::FileOutputStream os (outFile);
        juce::PNGImageFormat().writeImageToStream (img, os);
        CHECK (img.isValid(), "window renders (%dx%d)", img.getWidth(), img.getHeight());

        r.set ("count", 1);
        juce::MessageManager::getInstance()->runDispatchLoopUntil (200);
        auto img8 = ed->createComponentSnapshot (ed->getLocalBounds(), true, 2.0f);
        juce::File out8 = outFile.getSiblingFile (outFile.getFileNameWithoutExtension() + "-8.png");
        out8.deleteFile();
        juce::FileOutputStream os8 (out8);
        juce::PNGImageFormat().writeImageToStream (img8, os8);
    }

    std::printf (failures ? "\n%d FAILURE(S)\n" : "\nALL PLUGIN TESTS PASSED\n", failures);
    return failures ? 1 : 0;
}
