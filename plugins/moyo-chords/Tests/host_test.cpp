// Host test for MOYO Chords: loads the built .vst3 the way a DAW does and checks that it
// starts, takes MIDI in, sends MIDI out, makes sound and restores its state.
//   MoyoChordsHostTest "<path to MOYO Chords.vst3>"

#include <cstdio>
#include <juce_audio_processors/juce_audio_processors.h>

static int failures = 0;
#define CHECK(cond, ...) do { if (!(cond)) { ++failures; std::printf ("FAIL: "); } else std::printf ("ok:   "); std::printf (__VA_ARGS__); std::printf ("\n"); } while (0)

int main (int argc, char* argv[])
{
    if (argc < 2) { std::printf ("usage: MoyoChordsHostTest <plugin.vst3>\n"); return 2; }
    juce::ScopedJuceInitialiser_GUI gui;
    const juce::String path = juce::File::getCurrentWorkingDirectory().getChildFile (juce::String (juce::CharPointer_UTF8 (argv[1]))).getFullPathName();

    juce::VST3PluginFormat format;
    juce::OwnedArray<juce::PluginDescription> found;
    format.findAllTypesForFile (found, path);
    CHECK (found.size() == 1, "the plugin file is a valid VST3 (%d plugin found in %s)", found.size(), path.toRawUTF8());
    if (found.isEmpty()) return 1;

    const auto& desc = *found[0];
    CHECK (desc.name == "MOYO Chords" && desc.manufacturerName == "Joe Moyo", "identifies as '%s' by '%s'", desc.name.toRawUTF8(), desc.manufacturerName.toRawUTF8());
    CHECK (desc.isInstrument, "registers as an instrument (so FL Studio loads it in the Channel Rack)");

    juce::String error;
    const double sr = 48000.0;
    const int block = 512;
    auto plugin = format.createInstanceFromDescription (desc, sr, block, error);
    CHECK (plugin != nullptr, "the host can start it %s", error.toRawUTF8());
    if (plugin == nullptr) return 1;

    CHECK (plugin->acceptsMidi() && plugin->producesMidi(), "takes MIDI in and sends MIDI out");
    CHECK (plugin->getTotalNumOutputChannels() == 2 && plugin->getTotalNumInputChannels() == 0, "stereo out, no audio in");
    CHECK (plugin->getParameters().size() >= 19 && plugin->getParameters().size() < 40, "exposes %d automatable controls (no clutter)", plugin->getParameters().size());

    plugin->prepareToPlay (sr, block);

    auto run = [&] (int blocks, juce::MidiBuffer first, int& notesOn, int& notesOff, float& peak)
    {
        for (int b = 0; b < blocks; ++b)
        {
            juce::AudioBuffer<float> audio (2, block);
            audio.clear();
            juce::MidiBuffer midi;
            if (b == 0) midi = first;
            plugin->processBlock (audio, midi);
            for (const auto meta : midi)
            {
                notesOn += meta.getMessage().isNoteOn();
                notesOff += meta.getMessage().isNoteOff();
            }
            peak = std::max (peak, audio.getMagnitude (0, block));
        }
    };

    int on = 0, off = 0;
    float peak = 0.0f;
    juce::MidiBuffer press, release;
    press.addEvent (juce::MidiMessage::noteOn (1, 60, (juce::uint8) 100), 0);
    release.addEvent (juce::MidiMessage::noteOff (1, 60), 0);
    run (40, press, on, off, peak);
    CHECK (on >= 3, "one key in -> a %d-note chord out of the plugin's MIDI output", on);
    CHECK (peak > 0.01f && peak <= 1.0f, "the built-in sound plays (peak %.2f)", peak);
    run (40, release, on, off, peak);
    CHECK (off == on, "key released -> all %d notes stop", off);

    // State round trip through the host.
    juce::MemoryBlock state;
    plugin->getStateInformation (state);
    CHECK (state.getSize() > 100, "the host can save its state (%d bytes)", (int) state.getSize());
    plugin->setStateInformation (state.getData(), (int) state.getSize());
    int on2 = 0, off2 = 0;
    run (40, press, on2, off2, peak);
    run (40, release, on2, off2, peak);
    CHECK (on2 == on && off2 == on2, "after reloading its state it plays the same chord (%d notes)", on2);

    // Open the window if this machine can show one.
    const char* skipEditor = std::getenv ("MOYO_SKIP_EDITOR");
    if ((skipEditor == nullptr || skipEditor[0] == 0) && plugin->hasEditor())
    {
        std::unique_ptr<juce::AudioProcessorEditor> editor (plugin->createEditor());
        CHECK (editor != nullptr && editor->getWidth() > 300 && editor->getHeight() > 200, "the window opens (%dx%d)",
               editor != nullptr ? editor->getWidth() : 0, editor != nullptr ? editor->getHeight() : 0);
    }

    plugin->releaseResources();
    plugin.reset();
    std::printf (failures ? "\n%d FAILURE(S)\n" : "\nHOST TEST PASSED\n", failures);
    return failures ? 1 : 0;
}
