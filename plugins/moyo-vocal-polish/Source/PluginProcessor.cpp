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
    { "Rap Lead",            75, 45, 35, 50, 100, -1.0f },
    { "Smooth R&B",          55, 55, 45, 45, 100,  0.0f },
    { "Bright Pop",          65, 20, 70, 60, 100, -1.0f },
    { "Voiceover / YouTube", 70, 25, 20, 55, 100,  0.0f },
    { "Gentle Touch",        25, 15, 15, 30, 100,  0.0f },
    { "Parallel Crush",     100, 70, 40, 60,  45,  0.0f },
};
constexpr int numPresets = (int) (sizeof (presets) / sizeof (presets[0]));

constexpr int smoothChunk = 32; // coefficients are refreshed every 32 oversampled samples
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
    outGainS.setTargetValue (moyo::dbToGain (pOutput->load()));

    // Keep a latency-aligned copy of the dry signal for the MIX knob.
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

    juce::dsp::AudioBlock<float> block (buffer.getArrayOfWritePointers(), (size_t) numCh, (size_t) n);
    auto up = oversampler->processSamplesUp (block);
    processWet (up);
    oversampler->processSamplesDown (block);

    float peak = 0.0f;
    for (int i = 0; i < n; ++i)
    {
        const float mix = mixS.getNextValue();
        const float g = outGainS.getNextValue();
        for (int ch = 0; ch < numCh; ++ch)
        {
            float* out = buffer.getWritePointer (ch);
            const float y = (mix * out[i] + (1.0f - mix) * dryBuffer.getSample (ch, i)) * g;
            out[i] = y;
            peak = juce::jmax (peak, std::abs (y));
        }
    }
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

void MoyoVocalPolishProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    auto state = apvts.copyState();
    state.setProperty ("program", currentProgram, nullptr);
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
