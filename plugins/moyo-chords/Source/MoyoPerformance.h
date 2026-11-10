#pragma once

// Performance engine for MOYO Chords: turns voiced chords into timed notes,
// using a rhythm pattern, strum, swing, humanise and gate. The same note list
// drives live playback and the exported MIDI file, so they always match.

#include "MoyoVoicing.h"

namespace moyo
{
struct NoteEvent
{
    double start = 0;   // in beats (quarter notes) from the start of the progression
    double length = 0;  // in beats
    int note = 60;
    int velocity = 96;
};

enum Part { PartAll, PartUpper, PartBass };
enum ArpOrder { ArpNone, ArpUp, ArpDown, ArpUpDown, ArpBroken, ArpRandom };

struct Hit { int step; int len; Part part; float vel; };  // step and len in 16th notes, within one 4/4 bar

struct PatternDef
{
    const char* name;
    std::vector<Hit> hits;
    ArpOrder arp = ArpNone;
    int arpRate = 2;  // 16th notes per arp step
};

inline const std::vector<PatternDef>& patterns()
{
    static const std::vector<PatternDef> p {
        { "Sustain",       { { 0, 16, PartAll, 1.0f } } },
        { "Half Notes",    { { 0, 8, PartAll, 1.0f }, { 8, 8, PartAll, 0.9f } } },
        { "Quarter Pulse", { { 0, 4, PartAll, 1.0f }, { 4, 4, PartUpper, 0.8f }, { 8, 4, PartAll, 0.9f }, { 12, 4, PartUpper, 0.8f } } },
        { "Offbeat Stabs", { { 0, 2, PartBass, 1.0f }, { 4, 2, PartBass, 0.9f }, { 8, 2, PartBass, 1.0f }, { 12, 2, PartBass, 0.9f },
                             { 2, 2, PartUpper, 0.9f }, { 6, 2, PartUpper, 0.85f }, { 10, 2, PartUpper, 0.9f }, { 14, 2, PartUpper, 0.85f } } },
        { "Push 3-3-2",    { { 0, 6, PartAll, 1.0f }, { 6, 6, PartUpper, 0.85f }, { 12, 4, PartAll, 0.9f } } },
        { "Bounce",        { { 0, 6, PartAll, 1.0f }, { 6, 2, PartUpper, 0.7f }, { 8, 4, PartAll, 0.9f }, { 12, 2, PartUpper, 0.75f }, { 14, 2, PartUpper, 0.7f } } },
        { "Laid Back",     { { 0, 7, PartAll, 1.0f }, { 7, 3, PartUpper, 0.6f }, { 10, 6, PartUpper, 0.85f } } },
        { "Ballad",        { { 0, 16, PartBass, 1.0f }, { 0, 8, PartUpper, 1.0f }, { 8, 6, PartUpper, 0.85f }, { 14, 2, PartUpper, 0.7f } } },
        { "Afro",          { { 0, 3, PartAll, 1.0f }, { 3, 3, PartUpper, 0.8f }, { 6, 4, PartUpper, 0.75f }, { 10, 2, PartAll, 0.85f }, { 12, 4, PartUpper, 0.8f } } },
        { "Boom Bap",      { { 0, 4, PartAll, 1.0f }, { 7, 1, PartUpper, 0.6f }, { 8, 6, PartAll, 0.9f }, { 14, 2, PartUpper, 0.65f } } },
        { "Arp Up 1/8",        {}, ArpUp, 2 },
        { "Arp Down 1/8",      {}, ArpDown, 2 },
        { "Arp Up-Down 1/16",  {}, ArpUpDown, 1 },
        { "Arp Broken 1/8",    {}, ArpBroken, 2 },
        { "Arp Random 1/16",   {}, ArpRandom, 1 },
    };
    return p;
}

struct PerfParams
{
    int pattern = 0;
    double strumMs = 0;     // positive strums low to high, negative high to low
    double humanise = 0;    // 0..1
    double swing = 0;       // 0..1
    double gate = 0.95;     // note length as a fraction of the pattern length
    double bpm = 120;
    uint32_t seed = 1;
};

namespace perf_detail
{
// Small deterministic hash -> -1..1, so humanise is repeatable for a given seed.
inline double jitter (uint32_t seed, uint32_t a, uint32_t b, uint32_t c)
{
    uint32_t h = seed * 0x9E3779B1u ^ (a + 0x7F4A7C15u) * 0x85EBCA6Bu ^ (b + 0x165667B1u) * 0xC2B2AE35u ^ (c + 0x27D4EB2Fu) * 0x9E3779B1u;
    h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12; h *= 0x297A2D39u; h ^= h >> 15;
    return (double) (h & 0xFFFFFF) / (double) 0x7FFFFF - 1.0;
}

inline std::vector<int> arpOrder (ArpOrder order, int n, int steps, uint32_t seed, uint32_t slot)
{
    std::vector<int> out;
    if (n <= 0) return out;
    for (int i = 0; i < steps; ++i)
    {
        int idx = 0;
        switch (order)
        {
            case ArpUp:   idx = i % n; break;
            case ArpDown: idx = n - 1 - (i % n); break;
            case ArpUpDown:
            {
                const int period = std::max (1, 2 * n - 2);
                const int k = i % period;
                idx = k < n ? k : period - k;
                break;
            }
            case ArpBroken: idx = (i % 2 == 0) ? (i / 2) % std::max (1, n - 1) : n - 1; break;  // low, top, next, top...
            case ArpRandom: idx = (int) ((jitter (seed, slot, (uint32_t) i, 77) + 1.0) * 0.4999 * n); break;
            case ArpNone: break;
        }
        out.push_back (std::clamp (idx, 0, n - 1));
    }
    return out;
}
} // namespace perf_detail

// Render the progression to a sorted list of notes. `beats[i]` is the length of chord i.
inline std::vector<NoteEvent> renderPerformance (const std::vector<Voiced>& chords, const std::vector<double>& beats, const PerfParams& p)
{
    using namespace perf_detail;
    std::vector<NoteEvent> out;
    const auto& pat = patterns()[(size_t) std::clamp (p.pattern, 0, (int) patterns().size() - 1)];
    const double beatsPerSecond = std::max (20.0, p.bpm) / 60.0;
    const double strumBeats = p.strumMs / 1000.0 * beatsPerSecond;
    const double humanBeats = p.humanise * 0.012 * beatsPerSecond;
    const double gate = std::clamp (p.gate, 0.1, 1.0);

    bool sixteenths = pat.arp != ArpNone ? pat.arpRate == 1 : false;
    for (const auto& h : pat.hits)
        if (h.step % 2 == 1) sixteenths = true;

    auto swingOffset = [&] (int step)
    {
        if (sixteenths) return step % 2 == 1 ? p.swing * 0.25 / 3.0 : 0.0;       // swing the 16ths
        return (step / 2) % 2 == 1 && step % 2 == 0 ? p.swing * 0.5 / 3.0 : 0.0;  // swing the 8ths
    };

    auto addNote = [&] (double slotStart, double slotEnd, double start, double length, int note, double vel, uint32_t slot, uint32_t hit, uint32_t idx)
    {
        start += jitter (p.seed, slot, hit, idx) * humanBeats;
        start = std::clamp (start, slotStart, std::max (slotStart, slotEnd - 0.03));
        length = std::max (0.03, std::min (length, slotEnd - start));
        vel += jitter (p.seed, slot, hit, idx + 100) * p.humanise * 14.0;
        out.push_back ({ start, length, std::clamp (note, 0, 127), std::clamp ((int) std::lround (vel), 1, 127) });
    };

    double slotStart = 0;
    for (size_t s = 0; s < chords.size() && s < beats.size(); ++s)
    {
        const auto& ch = chords[s];
        const double dur = beats[s];
        const double slotEnd = slotStart + dur;
        uint32_t hitCounter = 0;

        for (double bar = 0; bar < dur - 1.0e-9; bar += 4.0)
        {
            if (pat.arp != ArpNone)
            {
                // Bass holds under the arpeggio.
                const double barLen = std::min (4.0, dur - bar);
                for (size_t b = 0; b < ch.bass.size(); ++b)
                    addNote (slotStart, slotEnd, slotStart + bar, barLen * gate, ch.bass[b], 88, (uint32_t) s, hitCounter, (uint32_t) b);
                ++hitCounter;

                const int steps = (int) std::ceil (barLen * 4.0 / pat.arpRate - 1.0e-9);
                const auto order = arpOrder (pat.arp, (int) ch.upper.size(), steps, p.seed, (uint32_t) (s * 16 + (size_t) (bar / 4.0)));
                for (int i = 0; i < (int) order.size(); ++i)
                {
                    const int step = i * pat.arpRate;
                    const double t = bar + step * 0.25 + swingOffset (step);
                    if (t >= dur - 1.0e-9) break;
                    const double len = pat.arpRate * 0.25 * gate;
                    const double vel = (i == 0 ? 100 : 86) + (order[(size_t) i] == (int) ch.upper.size() - 1 ? 4 : 0);
                    addNote (slotStart, slotEnd, slotStart + t, len, ch.upper[(size_t) order[(size_t) i]], vel, (uint32_t) s, hitCounter++, 0);
                }
                continue;
            }

            for (const auto& h : pat.hits)
            {
                const double t = bar + h.step * 0.25 + swingOffset (h.step);
                if (t >= dur - 1.0e-9) continue;
                const double len = std::min (h.len * 0.25, dur - t) * gate;

                std::vector<std::pair<int, double>> notes;  // note, base velocity
                if (h.part != PartUpper)
                    for (int n : ch.bass) notes.push_back ({ n, 90.0 });
                if (h.part != PartBass)
                    for (size_t i = 0; i < ch.upper.size(); ++i)
                        notes.push_back ({ ch.upper[i], i + 1 == ch.upper.size() ? 99.0 : (i == 0 ? 94.0 : 88.0) });
                if (notes.empty()) continue;

                const double accent = (bar < 0.5 && h.step == 0) ? 6.0 : 0.0;
                const double maxStrum = len * 0.6;
                const int count = (int) notes.size();
                for (int i = 0; i < count; ++i)
                {
                    const int order = strumBeats >= 0 ? i : count - 1 - i;
                    const double off = std::min (std::abs (strumBeats) * order, maxStrum);
                    addNote (slotStart, slotEnd, slotStart + t + off, len - off,
                             notes[(size_t) i].first, notes[(size_t) i].second * h.vel + accent, (uint32_t) s, hitCounter, (uint32_t) i);
                }
                ++hitCounter;
            }
        }
        slotStart = slotEnd;
    }

    std::stable_sort (out.begin(), out.end(), [] (const NoteEvent& a, const NoteEvent& b) { return a.start < b.start; });
    return out;
}
} // namespace moyo
