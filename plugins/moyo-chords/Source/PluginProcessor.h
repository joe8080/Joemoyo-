#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <atomic>
#include "MoyoGenerator.h"
#include "MoyoPerformance.h"
#include "MoyoSynth.h"

// MOYO Chords: chord progression generator and player.
//
// Three ways to use the chords:
//   1. Drag the progression out as a MIDI file.
//   2. Play it: one key per chord, or one chord per scale note.
//   3. Let it play along with the host transport.
// Notes go to the built-in sound and to the plugin's MIDI output.
class MoyoChordsProcessor : public juce::AudioProcessor,
                            private juce::AudioProcessorValueTreeState::Listener,
                            private juce::Timer
{
public:
    enum KeysMode { KeysChords = 0, KeysDegrees, KeysOff };

    MoyoChordsProcessor();
    ~MoyoChordsProcessor() override;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    using AudioProcessor::processBlock;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return "MOYO Chords"; }
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return true; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 1.0; }

    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram (int) override {}
    const juce::String getProgramName (int) override { return {}; }
    void changeProgramName (int, const juce::String&) override {}

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    // ---- Used by the editor (message thread) -------------------------------
    moyo::Progression getProgression() const;
    juce::String getChordName (int slot) const;
    juce::String getRomanName (int slot) const;
    juce::String describeProgression() const;

    void generate();
    void vary();
    void rerollSlot (int slot);
    void setSlot (int slot, const moyo::Chord& chord);
    void toggleLock (int slot);
    bool canUndo() const;
    bool canRedo() const;
    void undo();
    void redo();
    void setStyleFromUser (int styleIndex);

    void auditionSlot (int slot) { auditionRequest.store (slot); }
    void setPreviewPlaying (bool shouldPlay) { previewPlaying.store (shouldPlay); }
    bool isPreviewPlaying() const { return previewPlaying.load(); }

    bool writeMidiFile (const juce::File& file) const;
    juce::String suggestedFileName() const;

    // Applies any parameter changes right now (normally done by a timer).
    void flushPendingChanges();

    juce::AudioProcessorValueTreeState apvts;

    std::atomic<int> uiVersion { 0 };     // bumps whenever the progression or its voicing changes
    std::atomic<int> playingSlot { -1 };  // chord currently sounding, for the display
    std::atomic<juce::uint64> litLow { 0 }, litHigh { 0 };  // notes currently held, one bit per MIDI note

    static juce::AudioProcessorValueTreeState::ParameterLayout createLayout();

    static constexpr int maxSeq = 2048;

private:
    struct VoicedFixed
    {
        int numUpper = 0, numBass = 0;
        int upper[8] {}, bass[2] {};
    };

    // Everything the audio thread needs, in one fixed-size block.
    struct Snapshot
    {
        int numSlots = 0;
        VoicedFixed slots[moyo::kMaxSlots];
        double slotStart[moyo::kMaxSlots + 1] {};
        VoicedFixed degrees[7];
        int scalePcs[7] { 0, 2, 4, 5, 7, 9, 11 };
        int tonic = 0;
        int seqCount = 0;
        double seqBeats = 0;
        moyo::NoteEvent seq[maxSeq];
        float strumMs = 0, humanise = 0;
    };

    static constexpr int numKeys = 128 + moyo::kMaxSlots;  // real keys plus one audition "key" per chord
    static constexpr int maxChordNotes = 10;

    struct Held
    {
        bool active = false;
        int count = 0;
        int notes[maxChordNotes] {};
        bool started[maxChordNotes] {};
    };
    struct Pending { bool used = false; int samples = 0, note = 0, velocity = 0, key = 0, index = 0; };
    struct SeqNote { bool used = false; int note = 0; double endPpq = 0; };

    // Keys, strums, auditions and song playback each ask for notes on and off during a block.
    // The requests are collected, sorted by time, and only then turned into MIDI, so that
    // two sources playing the same note can never leave it stuck or cut it short.
    struct Intent { int pos = 0, order = 0, note = 0, velocity = 0; };  // velocity 0 = off, note -1 = all notes off
    static constexpr int maxIntents = 4096;

    void parameterChanged (const juce::String&, float) override { dirty.store (true); }
    void timerCallback() override;
    void rebuildSnapshot();
    void pushHistory();
    static VoicedFixed toFixed (const moyo::Voiced&);

    // audio thread
    void pullSnapshot();
    void noteOnOut (int note, int velocity, int pos);
    void noteOffOut (int note, int pos);
    void pushIntent (int pos, int note, int velocity);
    void resolveIntents (int numSamples);
    void keyDown (int key, const VoicedFixed& chord, int shift, int velocity, int pos, bool exact = false);
    void keyUp (int key, int pos);
    void flushPendingNotes (int numSamples);
    void runSequence (double p0, double p1, int numSamples);
    void releaseSequence (int pos);
    void panic (int pos);

    // ---- message-thread state (guarded by progLock) -------------------------
    juce::CriticalSection progLock;
    moyo::Progression prog;
    std::vector<moyo::Progression> history;
    int historyPos = -1;
    moyo::Generator generator;
    juce::uint32 perfSeed = 1;
    std::vector<moyo::NoteEvent> lastSeq;
    double lastSeqBeats = 16.0;
    int cachedCount = -1, cachedChordLen = -1;
    double cachedBpm = 120.0;

    // ---- hand-over to the audio thread --------------------------------------
    juce::SpinLock snapLock;
    Snapshot pendingSnap;
    bool pendingDirty = false;
    std::atomic<bool> dirty { true };

    // ---- audio thread --------------------------------------------------------
    Snapshot live;
    juce::MidiBuffer out;
    juce::Synthesiser synth;
    int refCount[128] {};
    Intent intents[maxIntents];
    int numIntents = 0;
    bool intentOverflow = false;
    Held held[numKeys];
    Pending pending[256];
    SeqNote seqNotes[96];
    int auditionSamplesLeft[moyo::kMaxSlots] {};
    bool seqWasRunning = false;
    double lastPpqEnd = -1.0e9, previewPpq = 0.0;
    double sampleRate = 44100.0;
    float lastGain = 0.0f;
    int lastTriggeredSlot = -1;
    juce::Random audioRandom;

    std::atomic<int> auditionRequest { -1 };
    std::atomic<bool> previewPlaying { false };
    std::atomic<double> currentBpm { 120.0 };

    std::atomic<float>* pKey = nullptr; std::atomic<float>* pScale = nullptr; std::atomic<float>* pStyle = nullptr;
    std::atomic<float>* pCount = nullptr; std::atomic<float>* pChordLen = nullptr;
    std::atomic<float>* pComplexity = nullptr; std::atomic<float>* pColour = nullptr;
    std::atomic<float>* pVoicing = nullptr; std::atomic<float>* pRegister = nullptr; std::atomic<float>* pBass = nullptr;
    std::atomic<float>* pRhythm = nullptr; std::atomic<float>* pStrum = nullptr; std::atomic<float>* pHumanise = nullptr;
    std::atomic<float>* pSwing = nullptr; std::atomic<float>* pGate = nullptr;
    std::atomic<float>* pKeysMode = nullptr; std::atomic<float>* pHostSync = nullptr;
    std::atomic<float>* pSound = nullptr; std::atomic<float>* pVolume = nullptr;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MoyoChordsProcessor)
};
