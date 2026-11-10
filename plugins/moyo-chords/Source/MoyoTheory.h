#pragma once

// Music theory for MOYO Chords: scales, chord qualities, naming.
// Plain C++ with no JUCE dependency, so it can be unit-tested on its own.

#include <algorithm>
#include <array>
#include <cctype>
#include <string>
#include <vector>

namespace moyo
{
constexpr int kMaxSlots = 8;

struct ScaleDef
{
    const char* name;
    int pcs[7];        // semitones above the tonic
    bool minorish;     // has a minor third
    int parentOffset;  // semitones up to the parent major key (used to pick flats or sharps)
};

inline const std::array<ScaleDef, 10>& scales()
{
    static const std::array<ScaleDef, 10> s { {
        { "Major",             { 0, 2, 4, 5, 7, 9, 11 }, false, 0 },
        { "Minor",             { 0, 2, 3, 5, 7, 8, 10 }, true,  3 },
        { "Harmonic Minor",    { 0, 2, 3, 5, 7, 8, 11 }, true,  3 },
        { "Melodic Minor",     { 0, 2, 3, 5, 7, 9, 11 }, true,  3 },
        { "Dorian",            { 0, 2, 3, 5, 7, 9, 10 }, true,  10 },
        { "Phrygian",          { 0, 1, 3, 5, 7, 8, 10 }, true,  8 },
        { "Lydian",            { 0, 2, 4, 6, 7, 9, 11 }, false, 7 },
        { "Mixolydian",        { 0, 2, 4, 5, 7, 9, 10 }, false, 5 },
        { "Locrian",           { 0, 1, 3, 5, 6, 8, 10 }, true,  1 },
        { "Phrygian Dominant", { 0, 1, 4, 5, 7, 8, 10 }, false, 8 },
    } };
    return s;
}

enum ScaleIndex { ScMajor = 0, ScMinor, ScHarmonicMinor, ScMelodicMinor, ScDorian, ScPhrygian, ScLydian, ScMixolydian, ScLocrian, ScPhrygianDominant };

enum Quality
{
    Maj = 0, Min, Dim, Aug, Sus2, Sus4, Six, Min6, Add9, MinAdd9,
    Maj7, Min7, Dom7, Min7b5, Dim7, MinMaj7, Dom7sus4, Dom7s5,
    SixNine, Maj9, Min9, Dom9, Dom7b9, Dom7s9,
    Min11, Dom9sus4, Maj9s11, Dom13, Maj13, Min13,
    NumQualities
};

enum Family { FMaj, FMin, FDom, FDim, FAug, FSus };

struct QualityDef
{
    const char* suffix;          // "m7", "maj9", ...
    std::vector<int> intervals;  // semitones above the root, ascending
    int level;                   // 0 triad, 1 seventh / colour triad, 2 ninth, 3 eleventh / thirteenth
    int simpler;                 // the next plainer quality
    Family family;
};

inline const std::vector<QualityDef>& qualities()
{
    static const std::vector<QualityDef> q {
        /* Maj      */ { "",        { 0, 4, 7 },             0, Maj,      FMaj },
        /* Min      */ { "m",       { 0, 3, 7 },             0, Min,      FMin },
        /* Dim      */ { "dim",     { 0, 3, 6 },             0, Dim,      FDim },
        /* Aug      */ { "aug",     { 0, 4, 8 },             0, Aug,      FAug },
        /* Sus2     */ { "sus2",    { 0, 2, 7 },             0, Sus2,     FSus },
        /* Sus4     */ { "sus4",    { 0, 5, 7 },             0, Sus4,     FSus },
        /* Six      */ { "6",       { 0, 4, 7, 9 },          1, Maj,      FMaj },
        /* Min6     */ { "m6",      { 0, 3, 7, 9 },          1, Min,      FMin },
        /* Add9     */ { "add9",    { 0, 4, 7, 14 },         1, Maj,      FMaj },
        /* MinAdd9  */ { "madd9",   { 0, 3, 7, 14 },         1, Min,      FMin },
        /* Maj7     */ { "maj7",    { 0, 4, 7, 11 },         1, Maj,      FMaj },
        /* Min7     */ { "m7",      { 0, 3, 7, 10 },         1, Min,      FMin },
        /* Dom7     */ { "7",       { 0, 4, 7, 10 },         1, Maj,      FDom },
        /* Min7b5   */ { "m7b5",    { 0, 3, 6, 10 },         1, Dim,      FDim },
        /* Dim7     */ { "dim7",    { 0, 3, 6, 9 },          1, Dim,      FDim },
        /* MinMaj7  */ { "mMaj7",   { 0, 3, 7, 11 },         1, Min,      FMin },
        /* Dom7sus4 */ { "7sus4",   { 0, 5, 7, 10 },         1, Sus4,     FSus },
        /* Dom7s5   */ { "7#5",     { 0, 4, 8, 10 },         1, Aug,      FDom },
        /* SixNine  */ { "6/9",     { 0, 4, 7, 9, 14 },      2, Six,      FMaj },
        /* Maj9     */ { "maj9",    { 0, 4, 7, 11, 14 },     2, Maj7,     FMaj },
        /* Min9     */ { "m9",      { 0, 3, 7, 10, 14 },     2, Min7,     FMin },
        /* Dom9     */ { "9",       { 0, 4, 7, 10, 14 },     2, Dom7,     FDom },
        /* Dom7b9   */ { "7b9",     { 0, 4, 7, 10, 13 },     2, Dom7,     FDom },
        /* Dom7s9   */ { "7#9",     { 0, 4, 7, 10, 15 },     2, Dom7,     FDom },
        /* Min11    */ { "m11",     { 0, 3, 7, 10, 14, 17 }, 3, Min9,     FMin },
        /* Dom9sus4 */ { "9sus4",   { 0, 5, 7, 10, 14 },     2, Dom7sus4, FSus },
        /* Maj9s11  */ { "maj9#11", { 0, 4, 7, 11, 14, 18 }, 3, Maj9,     FMaj },
        /* Dom13    */ { "13",      { 0, 4, 7, 10, 14, 21 }, 3, Dom9,     FDom },
        /* Maj13    */ { "maj13",   { 0, 4, 7, 11, 14, 21 }, 3, Maj9,     FMaj },
        /* Min13    */ { "m13",     { 0, 3, 7, 10, 14, 21 }, 3, Min9,     FMin },
    };
    return q;
}

inline const QualityDef& quality (int q) { return qualities()[(size_t) std::clamp (q, 0, (int) NumQualities - 1)]; }

inline bool isMinorFamily (int q)
{
    const auto f = quality (q).family;
    return f == FMin || f == FDim;
}

// One chord in the progression. The root is stored relative to the key, so
// changing key transposes the whole progression.
struct Chord
{
    int root = 0;        // semitones above the tonic, 0-11
    int quality = Maj;
    int inversion = -1;  // -1 = automatic (voice-led), otherwise 0, 1, 2, 3
    int octave = 0;      // per-chord octave shift, -2..+2
    double beats = 4.0;
    bool locked = false;

    bool sameHarmony (const Chord& o) const { return root == o.root && quality == o.quality; }
};

struct Progression
{
    std::array<Chord, kMaxSlots> slots {};
    int count = 4;

    double totalBeats() const
    {
        double t = 0;
        for (int i = 0; i < count; ++i) t += slots[(size_t) i].beats;
        return t;
    }
};

inline int mod12 (int x) { return ((x % 12) + 12) % 12; }

inline bool inScale (int scaleIdx, int rootOffset)
{
    const auto& sc = scales()[(size_t) scaleIdx];
    return std::find (std::begin (sc.pcs), std::end (sc.pcs), mod12 (rootOffset)) != std::end (sc.pcs);
}

inline int degreeOf (int scaleIdx, int rootOffset)
{
    const auto& sc = scales()[(size_t) scaleIdx];
    for (int i = 0; i < 7; ++i)
        if (sc.pcs[i] == mod12 (rootOffset)) return i;
    return -1;
}

// True when every note of the chord belongs to the scale.
inline bool fitsScale (int scaleIdx, int rootOffset, int q)
{
    for (int iv : quality (q).intervals)
        if (! inScale (scaleIdx, rootOffset + iv)) return false;
    return true;
}

// The chord the scale itself builds on a degree, by stacking thirds.
// level: 0 triad, 1 seventh, 2 ninth, 3 eleventh / thirteenth.
inline int diatonicQuality (int scaleIdx, int rootOffset, int level)
{
    const int d = degreeOf (scaleIdx, rootOffset);
    if (d < 0) return Maj;
    const auto& sc = scales()[(size_t) scaleIdx];
    auto tone = [&] (int k) { return mod12 (sc.pcs[(d + 2 * k) % 7] - sc.pcs[d]); };
    const int third = tone (1), fifth = tone (2), seventh = tone (3), ninth = tone (4), eleventh = tone (5), thirteenth = tone (6);

    int q;
    if      (third == 4 && fifth == 8) q = Aug;
    else if (third == 3 && fifth == 6) q = Dim;
    else if (third == 4)               q = Maj;
    else                               q = Min;
    if (level < 1) return q;

    int q7 = q;
    if      (q == Maj && seventh == 11) q7 = Maj7;
    else if (q == Maj && seventh == 10) q7 = Dom7;
    else if (q == Min && seventh == 10) q7 = Min7;
    else if (q == Min && seventh == 11) q7 = level >= 3 ? MinMaj7 : Min;  // i(maj7) is harsh, keep it for high complexity
    else if (q == Dim && seventh == 10) q7 = Min7b5;
    else if (q == Dim && seventh == 9)  q7 = Dim7;
    else if (q == Aug && seventh == 10) q7 = Dom7s5;
    if (level < 2) return q7;

    int q9 = q7;
    if (ninth == 2)
    {
        if (q7 == Maj7) q9 = Maj9;
        else if (q7 == Dom7) q9 = Dom9;
        else if (q7 == Min7) q9 = Min9;
    }
    else if (ninth == 1 && q7 == Dom7)
        q9 = Dom7b9;
    if (level < 3) return q9;

    if (q9 == Min9 && eleventh == 5)   return Min11;
    if (q9 == Maj9 && eleventh == 6)   return Maj9s11;
    if (q9 == Maj9 && thirteenth == 9) return Maj13;
    if (q9 == Dom9 && thirteenth == 9) return Dom13;
    return q9;
}

// ---- Naming ----------------------------------------------------------------

inline bool preferFlats (int tonicPc, int scaleIdx)
{
    const int parent = mod12 (tonicPc + scales()[(size_t) scaleIdx].parentOffset);
    return parent == 5 || parent == 10 || parent == 3 || parent == 8 || parent == 1 || parent == 0;
}

inline std::string noteName (int pc, bool flats)
{
    static const char* sharp[] = { "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" };
    static const char* flat[]  = { "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B" };
    return flats ? flat[mod12 (pc)] : sharp[mod12 (pc)];
}

inline std::string rootName (int tonicPc, int scaleIdx, int rootOffset)
{
    const int pc = mod12 (tonicPc + rootOffset);
    const bool flats = preferFlats (tonicPc, scaleIdx);
    // In C (and its modes) the raised fourth reads better as F# than Gb.
    if (flats && pc == 6 && mod12 (tonicPc + scales()[(size_t) scaleIdx].parentOffset) == 0) return "F#";
    return noteName (pc, flats);
}

inline std::string chordName (int tonicPc, int scaleIdx, const Chord& c)
{
    return rootName (tonicPc, scaleIdx, c.root) + quality (c.quality).suffix;
}

inline std::string romanName (const Chord& c)
{
    static const char* numerals[] = { "I", "bII", "II", "bIII", "III", "IV", "#IV", "V", "bVI", "VI", "bVII", "VII" };
    std::string n = numerals[mod12 (c.root)];
    std::string suffix = quality (c.quality).suffix;

    if (isMinorFamily (c.quality))
    {
        for (auto& ch : n)
            if (ch == 'I' || ch == 'V') ch = (char) std::tolower ((unsigned char) ch);
        if      (c.quality == Dim)     suffix = "o";
        else if (c.quality == Dim7)    suffix = "o7";
        else if (c.quality == Min7b5)  suffix = "m7b5";
        else if (c.quality == MinMaj7) suffix = "(maj7)";
        else if (! suffix.empty() && suffix[0] == 'm') suffix = suffix.substr (1);  // "m7" -> "7": the case already says minor
    }
    return n + suffix;
}
} // namespace moyo
