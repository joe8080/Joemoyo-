#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_dsp/juce_dsp.h>
#include <array>
#include <atomic>
#include "MoyoDSP.h"

// MOYO Vocal Polish: a one-knob vocal chain.
// POLISH drives cleanup EQ, compression and presence together; WARMTH, AIR,
// DE-ESS, INPUT, MIX and OUTPUT fine-tune it.
class MoyoVocalPolishProcessor : public juce::AudioProcessor
{
public:
    MoyoVocalPolishProcessor();
    ~MoyoVocalPolishProcessor() override = default;

    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    using AudioProcessor::processBlock;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return "MOYO Vocal Polish"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    int getNumPrograms() override;
    int getCurrentProgram() override { return currentProgram; }
    void setCurrentProgram (int index) override;
    const juce::String getProgramName (int index) override;
    void changeProgramName (int, const juce::String&) override {}

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    // A/B settings slots (message thread only).
    int  getActiveSlot() const noexcept { return activeSlot; }
    void selectSlot (int slot);
    void copyActiveSlotToOther();

    juce::AudioProcessorValueTreeState apvts;

    // Read by the editor for the meters.
    std::atomic<float> inputPeakDb      { -100.0f };
    std::atomic<float> compReductionDb  { 0.0f };
    std::atomic<float> deessReductionDb { 0.0f };
    std::atomic<float> outputPeakDb     { -100.0f };
    std::atomic<float> autoGainDb       { 0.0f };

    static juce::AudioProcessorValueTreeState::ParameterLayout createLayout();

private:
    struct ChannelState
    {
        moyo::Biquad hpf, mud, warmShelf, dcBlock, deessDetect, deessLow, presence, air;
        void reset()
        {
            for (auto* f : { &hpf, &mud, &warmShelf, &dcBlock, &deessDetect, &deessLow, &presence, &air })
                f->reset();
        }
    };

    void updateFilters (float polish, float warmth, float air);
    void processWet (juce::dsp::AudioBlock<float>& block);
    juce::var captureSettings() const;
    void applySettings (const juce::var& settings);

    std::array<ChannelState, 2> channels;
    moyo::Envelope compEnv, deessEnv;

    std::unique_ptr<juce::dsp::Oversampling<float>> oversampler;
    juce::dsp::DelayLine<float, juce::dsp::DelayLineInterpolationTypes::None> dryDelay { 4096 };
    juce::AudioBuffer<float> dryBuffer;

    juce::SmoothedValue<float> polishS, warmthS, airS, deessS, mixS, inGainS, outGainS, originalS, autoGainS;
    float inPower = 0.0f, outPower = 0.0f, powerCoef = 0.0f;

    double osRate = 88200.0;
    int currentProgram = 0;

    int activeSlot = 0;
    std::array<juce::var, 2> slots;

    std::atomic<float>* pPolish = nullptr;
    std::atomic<float>* pWarmth = nullptr;
    std::atomic<float>* pAir    = nullptr;
    std::atomic<float>* pDeess  = nullptr;
    std::atomic<float>* pMix    = nullptr;
    std::atomic<float>* pInput  = nullptr;
    std::atomic<float>* pOutput = nullptr;
    std::atomic<float>* pOriginal = nullptr;
    std::atomic<float>* pAutoGain = nullptr;
    std::atomic<float>* pClipGuard = nullptr;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (MoyoVocalPolishProcessor)
};
