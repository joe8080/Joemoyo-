#include "PluginProcessor.h"
#include "PluginEditor.h"

namespace
{
struct Preset
{
    const char* name;
    float polish, warmth, air, deess, mix, output;
};

// Factory presets. They show up in FL Studio's preset menu (the arrow at the
// top-left of the plugin window).
constexpr Preset presets[] = {
    { "Default",             50, 30, 30, 40, 100,  0.0f },
    { "Rap Lead",            75, 45, 35, 50, 100,  0.0f },
    { "Smooth R&B",          55, 55, 45, 45, 100,  0.0f },
    { "Bright Pop",          65, 20, 70, 60, 100,  0.0f },
    { "Voiceover / YouTube", 70, 25, 20, 55, 100,  0.0f },
    { "Gentle Touch",        25, 15, 15, 30, 100,  0.0f },
    { "Parallel Crush",     100, 70, 40, 60,  45,  0.0f },
};
constexpr int numPresets = (int) (sizeof (presets) / sizeof (presets[0]));

constexpr int smoothChunk = 32; // coefficients are refreshed every 32 oversampled samples

// Parameters that A/B slots store and recall ("original" is a listening switch, not a setting).
const char* const slotParams[] = { "polish", "warmth", "air", "deess", "mix", "input", "output", "autogain", "clipguard" };

// Soft ceiling: untouched below -1 dBFS, rounds peaks off so they never pass 0 dBFS.
inline float clipGuard (float x) noexcept
{
    constexpr float t = 0.8913f; // -1 dBFS
    const float a = std::abs (x);
    if (a <= t) return x;
    const float y = t + (1.0f - t) * std::tanh ((a - t) / (1.0f - t));
    return x < 0 ? -y : y;
}
} // namespace

juce::AudioProcessorValueTreeState::ParameterLayout MoyoVocalPolishProcessor::createLayout()
{
    using P = juce::AudioParameterFloat;
    using ID = juce::ParameterID;
    juce::AudioProcessorValueTreeState::ParameterLayout layout;

    auto pct = juce::AudioParameterFloatAttributes().withLabel ("%")
                   .withStringFromValueFunction ([] (float v, int) { return juce::String (juce::roundToInt (v)) + "%"; });
    auto db = juce::AudioParameterFloatAttributes().withLabel ("dB")
                  .withStringFromValueFunction ([] (float v, int) { return juce::String (v, 1) + " dB"; });

    layout.add (std::make_unique<P> (ID { "polish", 1 }, "Polish", juce::NormalisableRange<float> (0, 100, 0.1f), 50.0f, pct));
    layout.add (std::make_unique<P> (ID { "warmth", 1 }, "Warmth", juce::NormalisableRange<float> (0, 100, 0.1f), 30.0f, pct));
    layout.add (std::make_unique<P> (ID { "air",    1 }, "Air",    juce::NormalisableRange<float> (0, 100, 0.1f), 30.0f, pct));
    layout.add (std::make_unique<P> (ID { "deess",  1 }, "De-Ess", juce::NormalisableRange<float> (0, 100, 0.1f), 40.0f, pct));
    layout.add (std::make_unique<P> (ID { "mix",    1 }, "Mix",    juce::NormalisableRange<float> (0, 100, 0.1f), 100.0f, pct));
    layout.add (std::make_unique<P> (ID { "output", 1 }, "Output", juce::NormalisableRange<float> (-12, 12, 0.1f), 0.0f, db));
    layout.add (std::make_unique<P> (ID { "input",  1 }, "Input",  juce::NormalisableRange<float> (-24, 24, 0.1f), 0.0f, db));

    using B = juce::AudioParameterBool;
    layout.add (std::make_unique<B> (ID { "original",  1 }, "Hear Original", false));
    layout.add (std::make_unique<B> (ID { "autogain",  1 }, "Auto Gain",     true));
    layout.add (std::make_unique<B> (ID { "clipguard", 1 }, "Clip Guard",    true));
    return layout;
}

MoyoVocalPolishProcessor::MoyoVocalPolishProcessor()
    : AudioProcessor (BusesProperties()
                          .withInput  ("Input",  juce::AudioChannelSet::stereo(), true)
                          .withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, nullptr, "MoyoVocalPolish", createLayout())
{
    pPolish = apvts.getRawParameterValue ("polish");
    pWarmth = apvts.getRawParameterValue ("warmth");
    pAir    = apvts.getRawParameterValue ("air");
    pDeess  = apvts.getRawParameterValue ("deess");
    pMix    = apvts.getRawParameterValue ("mix");
    pOutput = apvts.getRawParameterValue ("output");
    pInput  = apvts.getRawParameterValue ("input");
    pOriginal  = apvts.getRawParameterValue ("original");
    pAutoGain  = apvts.getRawParameterValue ("autogain");
    pClipGuard = apvts.getRawParameterValue ("clipguard");
}

bool MoyoVocalPolishProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    const auto& out = layouts.getMainOutputChannelSet();
    if (out != juce::AudioChannelSet::mono() && out != juce::AudioChannelSet::stereo())
        return false;
    return out == layouts.getMainInputChannelSet();
}

void MoyoVocalPolishProcessor::prepareToPlay (double sampleRate, int samplesPerBlock)
{
    const int numCh = juce::jmax (1, getTotalNumOutputChannels());

    // 2x oversampling keeps the saturation clean and the air shelf natural.
    oversampler = std::make_unique<juce::dsp::Oversampling<float>> (
        (size_t) numCh, 1, juce::dsp::Oversampling<float>::filterHalfBandFIREquiripple, true, true);
    oversampler->initProcessing ((size_t) samplesPerBlock);
    osRate = sampleRate * 2.0;

    const int latency = (int) std::round (oversampler->getLatencyInSamples());
    setLatencySamples (latency);

    dryDelay.prepare ({ sampleRate, (juce::uint32) samplesPerBlock, (juce::uint32) numCh });
    dryDelay.setMaximumDelayInSamples (juce::jmax (latency + 1, 64));
    dryDelay.setDelay ((float) latency);
    dryDelay.reset();
    dryBuffer.setSize (numCh, samplesPerBlock);

    for (auto& c : channels) c.reset();
    compEnv.setTimes (osRate, 8.0, 140.0);
    deessEnv.setTimes (osRate, 0.5, 50.0);
    compEnv.reset();
    deessEnv.reset();

    auto initSmooth = [] (juce::SmoothedValue<float>& s, double rate, float v) { s.reset (rate, 0.05); s.setCurrentAndTargetValue (v); };
    initSmooth (polishS,  osRate, pPolish->load() * 0.01f);
    initSmooth (warmthS,  osRate, pWarmth->load() * 0.01f);
    initSmooth (airS,     osRate, pAir->load()    * 0.01f);
    initSmooth (deessS,   osRate, pDeess->load()  * 0.01f);
    initSmooth (mixS,     sampleRate, pMix->load() * 0.01f);
    initSmooth (outGainS, sampleRate, moyo::dbToGain (pOutput->load()));
    initSmooth (inGainS,  sampleRate, moyo::dbToGain (pInput->load()));
    originalS.reset (sampleRate, 0.02); // 20 ms crossfade for clickless A/B
    originalS.setCurrentAndTargetValue (pOriginal->load() > 0.5f ? 1.0f : 0.0f);
    autoGainS.reset (sampleRate, 0.3);
    autoGainS.setCurrentAndTargetValue (1.0f);
    inPower = outPower = 0.0f;
    powerCoef = (float) std::exp (-1.0 / (0.4 * sampleRate)); // ~400 ms loudness window

    updateFilters (polishS.getCurrentValue(), warmthS.getCurrentValue(), airS.getCurrentValue());
}

void MoyoVocalPolishProcessor::updateFilters (float p, float w, float a)
{
    for (auto& c : channels)
    {
        c.hpf.highPass       (osRate, 60.0 + 40.0 * p, 0.707);   // rumble / plosive cleanup
        c.mud.peak           (osRate, 300.0, 1.0, -4.5 * p);     // boxiness cut
        c.warmShelf.lowShelf (osRate, 180.0, 2.5 * w);           // body
        c.dcBlock.highPass   (osRate, 12.0, 0.707);              // removes DC from saturation
        c.deessDetect.bandPass (osRate, 7000.0, 1.2);            // sibilance detector
        c.deessLow.lowPass  (osRate, 4500.0, 0.707);            // everything above this is ducked
        c.presence.peak      (osRate, 3200.0, 0.9, 3.0 * p);     // clarity / forwardness
        c.air.highShelf      (osRate, 11000.0, 7.0 * a + 1.5 * p); // sheen
    }
}

void MoyoVocalPolishProcessor::processWet (juce::dsp::AudioBlock<float>& block)
{
    const int numCh = (int) block.getNumChannels();
    const int n = (int) block.getNumSamples();
    float maxComp = 0.0f, maxDeess = 0.0f;

    for (int start = 0; start < n; start += smoothChunk)
    {
        const int len = juce::jmin (smoothChunk, n - start);

        const float p = polishS.skip (len);
        const float w = warmthS.skip (len);
        const float a = airS.skip (len);
        const float d = deessS.skip (len);
        updateFilters (p, w, a);

        // Compressor settings follow POLISH: none at 0%, ~4:1 at 100%.
        const float thrDb = -10.0f - 14.0f * p;
        const float ratio = 1.0f + 3.0f * p;
        const float makeupDb = 0.4f * (-thrDb) * (1.0f - 1.0f / ratio);

        // Saturation follows WARMTH (gentle asymmetric tape-style curve).
        const float drive = 1.0f + 5.0f * w;
        const float bias = 0.15f * w;
        const float tb = std::tanh (bias);
        const float satNorm = 1.0f / (drive * (1.0f - tb * tb));
        const bool useSat = w > 0.001f;

        // De-esser follows DE-ESS.
        const float deThr = -12.0f - 24.0f * d;
        const float deMax = 14.0f * d;

        for (int i = start; i < start + len; ++i)
        {
            float x[2] = { 0, 0 };
            for (int ch = 0; ch < numCh; ++ch)
            {
                auto& c = channels[(size_t) ch];
                float s = block.getSample (ch, i);
                s = c.hpf.process (s);
                s = c.mud.process (s);
                s = c.warmShelf.process (s);
                x[ch] = s;
            }

            // Linked-stereo compressor.
            const float peak = numCh > 1 ? juce::jmax (std::abs (x[0]), std::abs (x[1])) : std::abs (x[0]);
            const float env = compEnv.process (peak);
            const float grDb = moyo::compressorGainDb (moyo::gainToDb (env), thrDb, ratio, 8.0f);
            const float compGain = moyo::dbToGain (grDb + makeupDb);
            maxComp = juce::jmax (maxComp, -grDb);

            for (int ch = 0; ch < numCh; ++ch)
            {
                auto& c = channels[(size_t) ch];
                float s = x[ch] * compGain;
                if (useSat)
                    s = c.dcBlock.process ((std::tanh (drive * s + bias) - tb) * satNorm);
                x[ch] = s;
            }

            // Linked-stereo de-esser: duck the top end only while "s" sounds are loud.
            float sib = 0.0f;
            for (int ch = 0; ch < numCh; ++ch)
                sib = juce::jmax (sib, std::abs (channels[(size_t) ch].deessDetect.process (x[ch])));
            const float sibDb = moyo::gainToDb (deessEnv.process (sib));
            const float deGr = d > 0.001f ? juce::jlimit (0.0f, deMax, (sibDb - deThr) * 0.75f) : 0.0f;
            const float duck = 1.0f - moyo::dbToGain (-deGr);
            maxDeess = juce::jmax (maxDeess, deGr);

            for (int ch = 0; ch < numCh; ++ch)
            {
                auto& c = channels[(size_t) ch];
                float s = x[ch];
                // Complementary split (low + high == input exactly), then duck the high part.
                const float hi = s - c.deessLow.process (s);
                s -= duck * hi;
                s = c.presence.process (s);
                s = c.air.process (s);
                block.setSample (ch, i, s);
            }
        }
    }

    compReductionDb.store (maxComp);
    deessReductionDb.store (maxDeess);
}

void MoyoVocalPolishProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;
    const int numCh = juce::jmin (buffer.getNumChannels(), 2);
    const int n = buffer.getNumSamples();
    if (numCh == 0 || n == 0 || oversampler == nullptr) return;

    for (int ch = getTotalNumInputChannels(); ch < buffer.getNumChannels(); ++ch)
        buffer.clear (ch, 0, n);

    polishS.setTargetValue (pPolish->load() * 0.01f);
    warmthS.setTargetValue (pWarmth->load() * 0.01f);
    airS.setTargetValue    (pAir->load()    * 0.01f);
    deessS.setTargetValue  (pDeess->load()  * 0.01f);
    mixS.setTargetValue    (pMix->load()    * 0.01f);
    inGainS.setTargetValue  (moyo::dbToGain (pInput->load()));
    outGainS.setTargetValue (moyo::dbToGain (pOutput->load()));
    originalS.setTargetValue (pOriginal->load() > 0.5f ? 1.0f : 0.0f);
    const bool autoGainOn = pAutoGain->load() > 0.5f;
    const bool guardOn = pClipGuard->load() > 0.5f;

    // 1. Input gain (drives the compressor harder or softer).
    float inPeak = 0.0f;
    for (int i = 0; i < n; ++i)
    {
        const float g = inGainS.getNextValue();
        for (int ch = 0; ch < numCh; ++ch)
        {
            float* d = buffer.getWritePointer (ch);
            d[i] *= g;
            inPeak = juce::jmax (inPeak, std::abs (d[i]));
        }
    }
    inputPeakDb.store (moyo::gainToDb (inPeak));

    // 2. Latency-aligned copy of the (input-gained) dry signal for MIX and HEAR ORIGINAL.
    if (dryBuffer.getNumSamples() < n) dryBuffer.setSize (numCh, n, false, false, true);
    for (int ch = 0; ch < numCh; ++ch)
    {
        const float* in = buffer.getReadPointer (ch);
        float* dry = dryBuffer.getWritePointer (ch);
        for (int i = 0; i < n; ++i)
        {
            dryDelay.pushSample (ch, in[i]);
            dry[i] = dryDelay.popSample (ch);
        }
    }

    // 3. The vocal chain, at 2x oversampling.
    juce::dsp::AudioBlock<float> block (buffer.getArrayOfWritePointers(), (size_t) numCh, (size_t) n);
    auto up = oversampler->processSamplesUp (block);
    processWet (up);
    oversampler->processSamplesDown (block);

    // 4. Mix, auto gain, original/processed crossfade, output, clip guard.
    const float chScale = 1.0f / (float) numCh;
    float peak = 0.0f;
    for (int i = 0; i < n; ++i)
    {
        const float mix = mixS.getNextValue();
        const float ag = autoGainS.getNextValue();
        const float orig = originalS.getNextValue();
        const float g = outGainS.getNextValue();

        float dryPow = 0.0f, wetPow = 0.0f;
        for (int ch = 0; ch < numCh; ++ch)
        {
            float* out = buffer.getWritePointer (ch);
            const float dry = dryBuffer.getSample (ch, i);
            const float processed = mix * out[i] + (1.0f - mix) * dry;
            dryPow += dry * dry;
            wetPow += processed * processed;

            float y = (orig * dry + (1.0f - orig) * processed * ag) * g;
            if (guardOn) y = clipGuard (y);
            out[i] = y;
            peak = juce::jmax (peak, std::abs (y));
        }
        inPower  = dryPow * chScale + powerCoef * (inPower  - dryPow * chScale);
        outPower = wetPow * chScale + powerCoef * (outPower - wetPow * chScale);
    }

    // Auto gain: match processed loudness to the input so louder never fools your ears.
    // Holds its value through silence so it doesn't pump between phrases.
    if (! autoGainOn)
        autoGainS.setTargetValue (1.0f);
    else if (inPower > 1.0e-6f && outPower > 1.0e-9f) // input above about -60 dBFS
        autoGainS.setTargetValue (juce::jlimit (0.25f, 4.0f, std::sqrt (inPower / outPower)));
    autoGainDb.store (moyo::gainToDb (autoGainS.getTargetValue()));

    outputPeakDb.store (moyo::gainToDb (peak));
}

int MoyoVocalPolishProcessor::getNumPrograms() { return numPresets; }

const juce::String MoyoVocalPolishProcessor::getProgramName (int index)
{
    return juce::isPositiveAndBelow (index, numPresets) ? presets[index].name : "";
}

void MoyoVocalPolishProcessor::setCurrentProgram (int index)
{
    if (! juce::isPositiveAndBelow (index, numPresets)) return;
    currentProgram = index;
    const auto& pr = presets[index];

    auto set = [this] (const char* id, float value)
    {
        if (auto* param = apvts.getParameter (id))
            param->setValueNotifyingHost (param->convertTo0to1 (value));
    };
    set ("polish", pr.polish);
    set ("warmth", pr.warmth);
    set ("air",    pr.air);
    set ("deess",  pr.deess);
    set ("mix",    pr.mix);
    set ("output", pr.output);
}

juce::var MoyoVocalPolishProcessor::captureSettings() const
{
    auto* obj = new juce::DynamicObject();
    for (auto* id : slotParams)
        if (auto* v = apvts.getRawParameterValue (id))
            obj->setProperty (id, v->load());
    return juce::var (obj);
}

void MoyoVocalPolishProcessor::applySettings (const juce::var& settings)
{
    for (auto* id : slotParams)
        if (settings.hasProperty (id))
            if (auto* param = apvts.getParameter (id))
                param->setValueNotifyingHost (param->convertTo0to1 ((float) settings[id]));
}

void MoyoVocalPolishProcessor::selectSlot (int slot)
{
    if (! juce::isPositiveAndBelow (slot, 2) || slot == activeSlot) return;
    slots[(size_t) activeSlot] = captureSettings();
    activeSlot = slot;
    if (slots[(size_t) slot].isVoid())
        slots[(size_t) slot] = captureSettings(); // first visit: start B as a copy of A
    else
        applySettings (slots[(size_t) slot]);
}

void MoyoVocalPolishProcessor::copyActiveSlotToOther()
{
    slots[(size_t) (1 - activeSlot)] = captureSettings();
}

void MoyoVocalPolishProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    slots[(size_t) activeSlot] = captureSettings();
    auto state = apvts.copyState();
    state.setProperty ("program", currentProgram, nullptr);
    state.setProperty ("activeSlot", activeSlot, nullptr);
    for (int i = 0; i < 2; ++i)
        if (! slots[(size_t) i].isVoid())
            state.setProperty (i == 0 ? "slotA" : "slotB", juce::JSON::toString (slots[(size_t) i], true), nullptr);
    if (auto xml = state.createXml())
        copyXmlToBinary (*xml, destData);
}

void MoyoVocalPolishProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    if (auto xml = getXmlFromBinary (data, sizeInBytes))
        if (xml->hasTagName (apvts.state.getType()))
        {
            auto state = juce::ValueTree::fromXml (*xml);
            currentProgram = state.getProperty ("program", 0);
            activeSlot = juce::jlimit (0, 1, (int) state.getProperty ("activeSlot", 0));
            for (int i = 0; i < 2; ++i)
            {
                const auto json = state.getProperty (i == 0 ? "slotA" : "slotB").toString();
                slots[(size_t) i] = json.isEmpty() ? juce::var() : juce::JSON::parse (json);
            }
            apvts.replaceState (state);
        }
}

juce::AudioProcessorEditor* MoyoVocalPolishProcessor::createEditor()
{
    return new MoyoVocalPolishEditor (*this);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new MoyoVocalPolishProcessor();
}
