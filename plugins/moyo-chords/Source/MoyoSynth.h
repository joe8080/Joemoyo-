#pragma once

// A small built-in instrument so MOYO Chords makes sound on its own.
// Three sounds: electric-piano style keys, a soft pad, and a pluck.

#include <atomic>
#include <juce_audio_basics/juce_audio_basics.h>

namespace moyo
{
enum SoundType { SoundKeys = 0, SoundPad, SoundPluck, SoundOff };

struct ChordSound : juce::SynthesiserSound
{
    bool appliesToNote (int) override { return true; }
    bool appliesToChannel (int) override { return true; }
};

class ChordVoice : public juce::SynthesiserVoice
{
public:
    explicit ChordVoice (std::atomic<float>* soundParam) : soundChoice (soundParam) {}

    bool canPlaySound (juce::SynthesiserSound* s) override { return dynamic_cast<ChordSound*> (s) != nullptr; }

    void startNote (int midiNote, float velocity, juce::SynthesiserSound*, int) override
    {
        type = (int) soundChoice->load();
        const double sr = getSampleRate();
        freq = juce::MidiMessage::getMidiNoteInHertz (midiNote);
        vel = velocity;
        age = 0.0;
        phaseL = phaseR = modPhase = 0.0;
        lpL = lpR = 0.0f;
        // Slight left/right detune gives width.
        const double cents = type == SoundPad ? 7.0 : 2.5;
        incL = freq * std::pow (2.0, -cents / 1200.0) / sr;
        incR = freq * std::pow (2.0, cents / 1200.0) / sr;

        juce::ADSR::Parameters p;
        switch (type)
        {
            case SoundPad:   p = { 0.30f, 1.0f, 0.80f, 0.90f }; break;
            case SoundPluck: p = { 0.002f, 0.70f, 0.0f, 0.25f }; break;
            default:         p = { 0.003f, 1.80f, 0.22f, 0.35f }; break;
        }
        adsr.setSampleRate (sr);
        adsr.setParameters (p);
        adsr.noteOn();
    }

    void stopNote (float, bool allowTailOff) override
    {
        if (allowTailOff) adsr.noteOff();
        else { adsr.reset(); clearCurrentNote(); }
    }

    void pitchWheelMoved (int) override {}
    void controllerMoved (int, int) override {}

    void renderNextBlock (juce::AudioBuffer<float>& out, int start, int num) override
    {
        if (! adsr.isActive()) return;
        const double sr = getSampleRate();
        const bool stereo = out.getNumChannels() > 1;
        float* l = out.getWritePointer (0, start);
        float* r = stereo ? out.getWritePointer (1, start) : nullptr;

        for (int i = 0; i < num; ++i)
        {
            const float env = adsr.getNextSample();
            float sl, sr2;

            if (type == SoundKeys)
            {
                // Two-operator FM: the modulation fades quickly, like a struck tine.
                const double index = (0.25 + 2.2 * vel) * std::exp (-age * 5.0) + 0.18;
                const double mod = std::sin (modPhase * juce::MathConstants<double>::twoPi) * index;
                sl = (float) std::sin (phaseL * juce::MathConstants<double>::twoPi + mod);
                sr2 = (float) std::sin (phaseR * juce::MathConstants<double>::twoPi + mod);
                modPhase += freq / sr;
                if (modPhase >= 1.0) modPhase -= 1.0;
            }
            else
            {
                sl = saw (phaseL, incL);
                sr2 = saw (phaseR, incR);
                // One-pole low-pass. The pluck's filter closes over about a third of a second.
                const double cutoff = type == SoundPad ? 700.0 + 2200.0 * vel
                                                       : 500.0 + (2500.0 + 5000.0 * vel) * std::exp (-age * 9.0);
                const float a = (float) (1.0 - std::exp (-juce::MathConstants<double>::twoPi * std::min (cutoff, sr * 0.45) / sr));
                lpL += a * (sl - lpL);
                lpR += a * (sr2 - lpR);
                sl = lpL;
                sr2 = lpR;
            }

            const float gain = env * (0.35f + 0.65f * vel) * 0.16f;
            l[i] += sl * gain;
            if (r != nullptr) r[i] += sr2 * gain;

            phaseL += incL; if (phaseL >= 1.0) phaseL -= 1.0;
            phaseR += incR; if (phaseR >= 1.0) phaseR -= 1.0;
            age += 1.0 / sr;

            if (! adsr.isActive()) { clearCurrentNote(); break; }
        }
    }

private:
    // Band-limited sawtooth (polyBLEP).
    static float saw (double phase, double inc)
    {
        double v = 2.0 * phase - 1.0;
        if (phase < inc) { const double t = phase / inc; v -= t + t - t * t - 1.0; }
        else if (phase > 1.0 - inc) { const double t = (phase - 1.0) / inc; v -= t * t + t + t + 1.0; }
        return (float) v;
    }

    std::atomic<float>* soundChoice;
    juce::ADSR adsr;
    int type = SoundKeys;
    double freq = 440.0, incL = 0.0, incR = 0.0, phaseL = 0.0, phaseR = 0.0, modPhase = 0.0, age = 0.0;
    float vel = 0.8f, lpL = 0.0f, lpR = 0.0f;
};
} // namespace moyo
