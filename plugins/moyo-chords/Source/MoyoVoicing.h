#pragma once

// Voicing engine for MOYO Chords: turns a chord symbol into actual notes.
// Picks the inversion and octave that move least from the previous chord
// (voice leading), in one of five voicing styles, plus an optional bass part.

#include <cmath>
#include <cstdint>
#include <limits>
#include "MoyoTheory.h"

namespace moyo
{
enum VoicingType { VoiceClose = 0, VoiceOpen, VoiceWide, VoiceShell, VoiceRootless, NumVoicings };
enum BassMode { BassOff = 0, BassRoot, BassRootFifth, BassOctaves, NumBassModes };

struct Voiced
{
    std::vector<int> upper;  // chord notes, low to high
    std::vector<int> bass;   // bass notes, low to high
};

namespace voicing_detail
{
inline int findInterval (const std::vector<int>& iv, std::initializer_list<int> options)
{
    for (int o : options)
        if (std::find (iv.begin(), iv.end(), o) != iv.end()) return o;
    return -1;
}

// The notes of the chord as semitones above the root, arranged for the voicing style.
// `rotatable` says whether inversions make sense for this arrangement.
inline std::vector<int> toneStack (const std::vector<int>& iv, int type, bool hasBass, bool& rotatable)
{
    const int third = findInterval (iv, { 3, 4, 2, 5 });
    const int fifth = findInterval (iv, { 7, 6, 8 });
    const int seventh = findInterval (iv, { 10, 11, 9 });
    std::vector<int> ext;
    for (int x : iv)
        if (x >= 13) ext.push_back (x);
    const bool hasSeventh = seventh >= 0 && iv.size() >= 4;
    rotatable = true;

    if (type == VoiceWide)
    {
        // Root and fifth low, everything else an octave up: the classic open sound.
        rotatable = false;
        std::vector<int> t { 0 };
        const int anchor = fifth >= 0 ? fifth : seventh;
        if (anchor >= 0) t.push_back (anchor);
        for (int x : iv)
            if (x != 0 && x != anchor) t.push_back (x + 12);
        std::sort (t.begin(), t.end());
        return t;
    }

    if (type == VoiceShell && hasSeventh)
    {
        // Guide tones (3rd and 7th) plus the top extension.
        std::vector<int> t;
        if (hasBass)
        {
            t = { third, seventh };
            t.push_back (ext.empty() ? 12 : ext.back());  // root on top when there is no extension
        }
        else
        {
            rotatable = false;
            t = { 0, seventh, third + 12 };
            if (! ext.empty()) t.push_back (ext.back() > third + 12 ? ext.back() : ext.back() + 12);
        }
        std::sort (t.begin(), t.end());
        return t;
    }

    if (type == VoiceRootless && hasSeventh && hasBass)
    {
        // 3-5-7-9: the pianist's left-hand voicing. The bass part supplies the root.
        std::vector<int> t { third };
        if (fifth >= 0 && ext.size() < 2) t.push_back (fifth);
        t.push_back (seventh);
        if (ext.empty()) t.push_back (12);
        for (int x : ext) t.push_back (x);
        std::sort (t.begin(), t.end());
        return t;
    }

    // Close (and the starting point for Open): stacked as written, at most five notes.
    std::vector<int> t = iv;
    if (t.size() > 5 && fifth == 7) t.erase (std::find (t.begin(), t.end(), 7));
    while (t.size() > 5) t.erase (t.begin() + 3);
    return t;
}

inline double movement (const std::vector<int>& a, const std::vector<int>& b)
{
    auto oneWay = [] (const std::vector<int>& from, const std::vector<int>& to)
    {
        double sum = 0;
        for (int x : from)
        {
            int best = 127;
            for (int y : to) best = std::min (best, std::abs (x - y));
            sum += best;
        }
        return sum;
    };
    return (oneWay (a, b) + oneWay (b, a)) / (double) std::max<size_t> (1, a.size() + b.size()) * 2.0;
}
} // namespace voicing_detail

// rootPc is absolute (0 = C). centre is the MIDI note the voicing should sit around.
// prev is the previous chord's upper notes, or empty for the first chord.
inline std::vector<int> voiceUpper (int rootPc, int qualityIdx, int type, int centre,
                                    const std::vector<int>& prev, int inversion, bool hasBass)
{
    using namespace voicing_detail;
    bool rotatable = true;
    const auto stack = toneStack (quality (qualityIdx).intervals, type, hasBass, rotatable);
    const int n = (int) stack.size();
    const int rootNote = 48 + mod12 (rootPc);

    std::vector<int> best;
    double bestScore = std::numeric_limits<double>::max();
    const int rotations = rotatable ? n : 1;

    for (int r = 0; r < rotations; ++r)
    {
        if (inversion >= 0 && rotatable && r != inversion % n) continue;

        std::vector<int> notes;
        for (int i = 0; i < n; ++i)
            notes.push_back (rootNote + stack[(size_t) i] + (i < r ? 12 : 0));
        std::sort (notes.begin(), notes.end());

        if (type == VoiceOpen && n >= 3)
        {
            notes[(size_t) (n - 2)] -= 12;  // drop-2
            std::sort (notes.begin(), notes.end());
        }

        double mean = 0;
        for (int x : notes) mean += x;
        mean /= n;
        const int k = (int) std::lround ((centre - mean) / 12.0);

        for (int dk = -1; dk <= 1; ++dk)
        {
            std::vector<int> cand = notes;
            for (auto& x : cand) x += 12 * (k + dk);
            const double candMean = mean + 12.0 * (k + dk);

            double score = std::abs (candMean - centre) * 0.35;
            if (! prev.empty())
            {
                score += movement (prev, cand);
                score += std::abs (cand.back() - prev.back()) * 0.4;  // keep the top line smooth
            }
            else if (r == 0)
                score -= 1.0;  // start in root position when nothing else decides

            for (int i = 0; i + 1 < n; ++i)
            {
                const int gap = cand[(size_t) i + 1] - cand[(size_t) i];
                if (cand[(size_t) i] < 52 && gap <= 2) score += 6.0;  // seconds are muddy down low
                else if (cand[(size_t) i] < 45 && gap <= 4) score += 3.0;
            }
            if (cand.front() < 36 || cand.back() > 96) score += 20.0;

            if (score < bestScore) { bestScore = score; best = cand; }
        }
    }
    return best;
}

inline std::vector<int> voiceBass (int rootPc, int qualityIdx, int bassMode, int centre)
{
    if (bassMode == BassOff) return {};
    int note = centre - 24 + mod12 (rootPc);  // C2..B2 when centre is middle C
    if (note > centre - 18) note -= 12;        // keep it between G1 and F#2
    switch (bassMode)
    {
        case BassRootFifth:
        {
            const auto& iv = quality (qualityIdx).intervals;
            const int fifth = voicing_detail::findInterval (iv, { 7, 6, 8 });
            return { note, note + (fifth >= 0 ? fifth : 7) };
        }
        case BassOctaves: return { note, note + 12 };
        default:          return { note };
    }
}

// Voice a whole progression, each chord led from the one before.
inline std::vector<Voiced> voiceProgression (const Progression& prog, int tonicPc, int type, int centre, int bassMode)
{
    std::vector<Voiced> out;
    std::vector<int> prev;
    for (int i = 0; i < prog.count; ++i)
    {
        const auto& c = prog.slots[(size_t) i];
        Voiced v;
        v.upper = voiceUpper (tonicPc + c.root, c.quality, type, centre, prev, c.inversion, bassMode != BassOff);
        prev = v.upper;  // lead from the un-shifted voicing so one octave-shifted chord doesn't drag the rest
        for (auto& x : v.upper) x = std::clamp (x + 12 * c.octave, 0, 127);
        v.bass = voiceBass (tonicPc + c.root, c.quality, bassMode, centre);
        for (auto& x : v.bass) x = std::clamp (x, 0, 127);
        out.push_back (std::move (v));
    }
    return out;
}
} // namespace moyo
