#pragma once

// Progression generator for MOYO Chords.
// Starts from curated progressions per style, then varies them with borrowed
// chords, secondary dominants, tritone substitutions and chord extensions,
// controlled by the Complexity and Colour settings.

#include <cstdint>
#include <initializer_list>
#include <random>
#include <sstream>
#include "MoyoTheory.h"

namespace moyo
{
struct StyleDef
{
    const char* name;
    std::vector<const char*> major;  // progressions for major-type scales
    std::vector<const char*> minor;  // progressions for minor-type scales
    float complexity, colour;        // suggested knob positions, 0..1
    int voicing, rhythm, bass;       // suggested menu choices
    float swing, strumMs;
    float jazz;                      // how readily it uses dominants and substitutions, 0..1
};

// Roman numerals are written relative to the major scale, the usual way of
// writing pop and jazz progressions: in a minor key the chords are
// i, bIII, iv, v, bVI, bVII. Lower case means minor. A suffix fixes the
// chord type ("V7", "IVmaj7", "iim7b5"); without one the chord follows the
// scale and the Complexity setting.
inline const std::vector<StyleDef>& styles()
{
    static const std::vector<StyleDef> s {
        { "Hip-Hop / Boom Bap",
          { "I vi ii V", "ii V I vi", "IVmaj7 iii vi ii", "I iii IV iv", "vi ii V I", "IV iii ii I" },
          { "i iv i v", "i bVI iv V7", "iim7b5 V7 i i", "i bVII bVI V7", "i iv bVII bIII", "bVImaj7 V7 i i", "i bIII iv bVI", "i v iv bVI" },
          0.50f, 0.35f, 1, 9, 1, 0.18f, 10.0f, 0.5f },
        { "Trap / Dark",
          { "vi IV I V", "I V vi IV", "vi IV vi V", "IV vi I V" },
          { "i bVI bIII bVII", "i bVI i bVII", "i i bVI v", "i bII i bVII", "i iv bVI v", "i bVI iv i", "bVI bVII i i", "i v bVI bVI" },
          0.15f, 0.20f, 0, 0, 1, 0.0f, 0.0f, 0.1f },
        { "R&B / Neo-Soul",
          { "IVmaj7 iii7 ii7 Imaj7", "ii7 V7 Imaj7 vi7", "Imaj7 iii7 vi7 ii7", "IVmaj7 V7 iii7 vi7", "ii7 iii7 IVmaj7 V7", "Imaj7 IVmaj7 iii7 VI7", "vi7 ii7 V7 Imaj7" },
          { "i iv bVII bIII", "iv bVII bIII bVI", "bVImaj7 V7 i i", "i v iv bVII", "bVImaj7 bVII i i", "i bVI iim7b5 V7", "iv v i i" },
          0.80f, 0.50f, 1, 6, 1, 0.22f, 18.0f, 0.8f },
        { "Gospel",
          { "I I7 IV iv", "IV V iii vi", "ii V7 I IV", "I iii7 IV V", "IV #ivdim7 I VI7", "vi ii V I", "I vi ii V7" },
          { "i iv V7 i", "i bVI iim7b5 V7", "iv V7 i bVI", "i bVII bVI V7", "bVI bVII i V7" },
          0.75f, 0.60f, 2, 7, 3, 0.10f, 25.0f, 0.9f },
        { "Pop",
          { "I V vi IV", "vi IV I V", "I vi IV V", "IV I V vi", "I IV vi V", "ii IV I V", "I iii IV V" },
          { "i bVI bIII bVII", "i bVII bVI bVII", "i bIII bVII bVI", "bVI bIII bVII i", "i iv bVI bVII" },
          0.15f, 0.25f, 0, 1, 1, 0.0f, 0.0f, 0.2f },
        { "Lo-fi / Jazz",
          { "ii7 V7 Imaj7 Imaj7", "Imaj7 vi7 ii7 V7", "IVmaj7 iii7 ii7 V7", "ii7 V7 iii7 VI7", "Imaj7 IVmaj7 iii7 vi7", "ii7 bII7 Imaj7 vi7" },
          { "i iv bVII bIII", "iim7b5 V7 i i", "i bVI iim7b5 V7", "iv bVII bIII bVI", "i iv iim7b5 V7" },
          0.85f, 0.55f, 4, 0, 1, 0.25f, 30.0f, 1.0f },
        { "Afrobeats / Amapiano",
          { "I vi IV V", "IV V vi I", "vi IV I V", "ii V I vi", "I IV V IV", "IV I V vi" },
          { "i bVII bVI bVII", "i bVI bVII v", "i iv bVII bIII", "bVI bVII i i", "i v bVI bVII" },
          0.45f, 0.30f, 1, 8, 1, 0.08f, 6.0f, 0.4f },
        { "House / Deep House",
          { "vi7 IVmaj7 Imaj7 V", "IVmaj7 I V vi", "ii7 Imaj7 ii7 Imaj7", "I vi IV V" },
          { "i bVI bIII bVII", "i bIII bVII iv", "i iv bVI bVII", "iv i bVI bVII", "i bVII bVI bVII", "i v iv iv" },
          0.60f, 0.30f, 0, 3, 0, 0.0f, 0.0f, 0.4f },
        { "Drill",
          { "vi IV vi V", "vi iii IV V" },
          { "i bVI i bVII", "i bII i bVII", "i iv i bII", "i v bVI bII", "i i bVI bVII", "i bVI bII V7" },
          0.10f, 0.30f, 0, 0, 1, 0.0f, 0.0f, 0.2f },
        { "Cinematic",
          { "I V vi iii", "I iii vi IV", "IV V vi vi", "I bVII IV I", "I bVI bVII I", "vi IV I V" },
          { "i bVI bIII bVII", "i bVI iv V", "bVI bVII i i", "i bIII bVII IV", "i v bVI IV", "i iv i V7" },
          0.10f, 0.35f, 2, 0, 3, 0.0f, 0.0f, 0.2f },
    };
    return s;
}

// Progressions that show off each mode's signature chord.
inline const std::vector<const char*>& modeProgressions (int scaleIdx)
{
    static const std::vector<const char*> none {};
    static const std::vector<const char*> harmonic   { "i iv V7 i", "i bVI V7 i", "i bVI iv V7", "i V7 bVI V7" };
    static const std::vector<const char*> melodic    { "i IV V7 i", "i ii V7 i", "i IV i V7" };
    static const std::vector<const char*> dorian     { "i IV i IV", "i bVII IV i", "i bIII IV i", "i IV v IV" };
    static const std::vector<const char*> phrygian   { "i bII i bvii", "i bII bIII bII", "i bvii bVI bII" };
    static const std::vector<const char*> lydian     { "I II I II", "I II I vii", "I II iii II" };
    static const std::vector<const char*> mixolydian { "I bVII IV I", "I bVII I IV", "I v IV I", "I IV bVII IV" };
    static const std::vector<const char*> locrian    { "idim bVI bvii bII", "idim bII biii bII" };
    static const std::vector<const char*> phrygDom   { "I bII I bvii", "I bII bvii I", "I iv bII I" };
    switch (scaleIdx)
    {
        case ScHarmonicMinor:    return harmonic;
        case ScMelodicMinor:     return melodic;
        case ScDorian:           return dorian;
        case ScPhrygian:         return phrygian;
        case ScLydian:           return lydian;
        case ScMixolydian:       return mixolydian;
        case ScLocrian:          return locrian;
        case ScPhrygianDominant: return phrygDom;
        default:                 return none;
    }
}

struct Token
{
    int root = 0;
    int quality = -1;        // -1 = decide from the scale and the Complexity setting
    bool minorCase = false;
};

inline int findQualityBySuffix (const std::string& suffix)
{
    const auto& q = qualities();
    for (size_t i = 0; i < q.size(); ++i)
        if (suffix == q[i].suffix) return (int) i;
    return -1;
}

inline Token parseToken (const std::string& s)
{
    Token t;
    size_t i = 0;
    int accidental = 0;
    if (i < s.size() && s[i] == 'b') { accidental = -1; ++i; }
    else if (i < s.size() && s[i] == '#') { accidental = 1; ++i; }

    std::string numeral;
    while (i < s.size() && (s[i] == 'I' || s[i] == 'V' || s[i] == 'i' || s[i] == 'v'))
        numeral += s[i++];
    t.minorCase = ! numeral.empty() && std::islower ((unsigned char) numeral[0]);
    for (auto& ch : numeral) ch = (char) std::toupper ((unsigned char) ch);

    static const std::pair<const char*, int> table[] = { { "I", 0 }, { "II", 2 }, { "III", 4 }, { "IV", 5 }, { "V", 7 }, { "VI", 9 }, { "VII", 11 } };
    int semis = 0;
    for (const auto& e : table)
        if (numeral == e.first) semis = e.second;
    t.root = mod12 (semis + accidental);

    const std::string suffix = s.substr (i);
    if (! suffix.empty())
    {
        int q = t.minorCase ? findQualityBySuffix ("m" + suffix) : -1;  // "ii7" means m7
        if (q < 0) q = findQualityBySuffix (suffix);
        t.quality = q;  // stays -1 if unknown
    }
    return t;
}

inline std::vector<Token> parseProgression (const char* text)
{
    std::vector<Token> out;
    std::istringstream in (text);
    std::string word;
    while (in >> word) out.push_back (parseToken (word));
    return out;
}

class Generator
{
public:
    explicit Generator (uint32_t seed = 1) : rng (seed) {}
    void reseed (uint32_t seed) { rng.seed (seed); }

    // Fill every unlocked slot with a new progression. Slot count, lengths and locks are kept.
    void generate (Progression& prog, int scaleIdx, int styleIdx, float complexity, float colour)
    {
        const auto& style = styles()[(size_t) styleIdx];
        auto tokens = pickTokens (prog.count, scaleIdx, style);
        substitute (tokens, prog, scaleIdx, colour, style);
        for (int i = 0; i < prog.count; ++i)
        {
            auto& slot = prog.slots[(size_t) i];
            if (slot.locked) continue;
            slot.root = tokens[(size_t) i].root;
            slot.quality = resolve (tokens[(size_t) i], scaleIdx, complexity, colour, style);
            slot.inversion = -1;
            slot.octave = 0;
        }
    }

    // Same chord roots and families, new extensions and colours.
    void vary (Progression& prog, int scaleIdx, int styleIdx, float complexity, float colour)
    {
        const auto& style = styles()[(size_t) styleIdx];
        for (int i = 0; i < prog.count; ++i)
        {
            auto& slot = prog.slots[(size_t) i];
            if (slot.locked) continue;
            slot.quality = resolve (tokenFromChord (slot, scaleIdx), scaleIdx, complexity, colour, style);
            slot.inversion = -1;
        }
    }

    // Replace one chord with a different one that still leads well from its neighbour.
    void reroll (Progression& prog, int index, int scaleIdx, int styleIdx, float complexity, float colour)
    {
        if (index < 0 || index >= prog.count) return;
        const auto& style = styles()[(size_t) styleIdx];
        const auto& sc = scales()[(size_t) scaleIdx];
        auto& slot = prog.slots[(size_t) index];

        std::vector<Token> pool;
        for (int pc : sc.pcs)
            pool.push_back ({ pc, -1, isMinorFamily (diatonicQuality (scaleIdx, pc, 0)) });
        if (sc.minorish)
        {
            pool.push_back ({ 1, Maj, false });   // bII
            pool.push_back ({ 5, Maj, false });   // IV (Dorian colour)
            pool.push_back ({ 7, Dom7, false });  // V7
        }
        else
        {
            pool.push_back ({ 10, Maj, false });  // bVII
            pool.push_back ({ 8, Maj, false });   // bVI
            pool.push_back ({ 5, Min, true });    // iv
            pool.push_back ({ 4, Dom7, false });  // V7 of vi
            pool.push_back ({ 9, Dom7, false });  // V7 of ii
        }

        const int prevRoot = prog.slots[(size_t) ((index + prog.count - 1) % prog.count)].root;
        const int nextRoot = prog.slots[(size_t) ((index + 1) % prog.count)].root;
        std::vector<double> weights;
        for (const auto& t : pool)
        {
            double w;
            switch (mod12 (t.root - prevRoot))
            {
                case 5: case 7:                   w = 3.0; break;  // fourth / fifth
                case 1: case 2: case 10: case 11: w = 2.0; break;  // step
                case 3: case 4: case 8: case 9:   w = 2.0; break;  // third
                case 0:                           w = 0.3; break;
                default:                          w = 0.5; break;  // tritone
            }
            if (t.root == nextRoot) w *= 0.3;
            if (t.root == slot.root) w = 0.0;
            if (t.quality >= 0) w *= 0.25 + 0.75 * colour;  // borrowed chords need some Colour
            weights.push_back (w);
        }
        std::discrete_distribution<int> pick (weights.begin(), weights.end());
        const auto& chosen = pool[(size_t) pick (rng)];
        slot.root = chosen.root;
        slot.quality = resolve (chosen, scaleIdx, complexity, colour, style);
        slot.inversion = -1;
    }

    // Exposed for tests.
    int resolve (const Token& t, int scaleIdx, float complexity, float colour, const StyleDef& style)
    {
        const float x = std::clamp (complexity, 0.0f, 1.0f) * 3.0f;
        const int level = std::clamp ((int) x + (chance (x - (float) (int) x) ? 1 : 0), 0, 3);

        // The style lists are written for plain major and minor, where upper/lower case is exact.
        // In other modes a chord whose root is in the scale takes the scale's own quality.
        const bool plainScale = scaleIdx == ScMajor || scaleIdx == ScMinor;
        const bool diatonicRoot = inScale (scaleIdx, t.root);
        const bool caseMatches = diatonicRoot && isMinorFamily (diatonicQuality (scaleIdx, t.root, 0)) == t.minorCase;

        int q;
        if (t.quality >= 0)                                   q = fit (t.quality, level, style, scaleIdx, t.root);
        else if (diatonicRoot && (caseMatches || ! plainScale)) q = diatonicQuality (scaleIdx, t.root, level);
        else                                                  q = fit (t.minorCase ? Min : Maj, level, style, scaleIdx, t.root);

        // Colour: swap a plain chord for a sus / add9 / 6 flavour now and then.
        if (chance (colour * 0.45f))
        {
            int cand = q;
            if      (q == Maj)  cand = pickOf ({ Add9, Sus2, Six, Sus4 });
            else if (q == Min)  cand = pickOf ({ MinAdd9, Min6 });
            else if (q == Maj7) cand = SixNine;
            else if (q == Dom7) cand = Dom7sus4;
            const bool ok = diatonicRoot ? fitsScale (scaleIdx, t.root, cand) : (cand == Add9 || cand == Sus2 || cand == MinAdd9);
            if (ok) q = cand;
        }
        return q;
    }

private:
    bool chance (float p) { return std::uniform_real_distribution<float> (0.0f, 1.0f) (rng) < p; }
    int pickOf (std::initializer_list<int> options)
    {
        std::uniform_int_distribution<size_t> d (0, options.size() - 1);
        return *(options.begin() + (std::ptrdiff_t) d (rng));
    }
    const char* pickFrom (const std::vector<const char*>& list)
    {
        std::uniform_int_distribution<size_t> d (0, list.size() - 1);
        return list[d (rng)];
    }

    static int stepUp (int q, bool altered, bool coin)
    {
        switch (q)
        {
            case Maj:      return Maj7;
            case Maj7:     return Maj9;
            case Maj9:     return coin ? Maj13 : Maj9s11;
            case Min:      return Min7;
            case Min7:     return Min9;
            case Min9:     return Min11;
            case Dom7:     return altered ? (coin ? Dom7s9 : Dom7b9) : Dom9;
            case Dom9:     return Dom13;
            case Dim:      return Dim7;
            case Sus4:     return Dom7sus4;
            case Dom7sus4: return Dom9sus4;
            case Aug:      return Dom7s5;
            default:       return q;
        }
    }

    // Bring a chord type to the requested complexity level. A chord that sits inside the
    // scale only gains extensions that also sit inside it (so iii7 never becomes iii9 in major).
    int fit (int q, int level, const StyleDef& style, int scaleIdx, int root)
    {
        while (quality (q).level > level && quality (q).simpler != q) q = quality (q).simpler;
        const bool stayInScale = fitsScale (scaleIdx, root, q);
        while (quality (q).level < level)
        {
            const bool altered = chance (style.jazz * 0.4f), coin = chance (0.5f);
            int next = stepUp (q, altered, coin);
            if (stayInScale && ! fitsScale (scaleIdx, root, next)) next = stepUp (q, false, ! coin);
            if (stayInScale && ! fitsScale (scaleIdx, root, next)) next = stepUp (q, true, coin);
            if (next == q || (stayInScale && ! fitsScale (scaleIdx, root, next))) break;
            q = next;
        }
        return q;
    }

    Token tokenFromChord (const Chord& c, int scaleIdx)
    {
        const auto fam = quality (c.quality).family;
        const bool minor = isMinorFamily (c.quality);
        if (inScale (scaleIdx, c.root) && fam != FDom && fam != FSus
            && isMinorFamily (diatonicQuality (scaleIdx, c.root, 0)) == minor
            && (fam == FMaj || fam == FMin))
            return { c.root, -1, minor };
        if (fam == FDom) return { c.root, Dom7, false };
        if (fam == FMaj) return { c.root, Maj, false };
        if (fam == FMin) return { c.root, Min, true };
        return { c.root, c.quality, minor };  // dim, aug and sus chords keep their type
    }

    std::vector<Token> pickTokens (int count, int scaleIdx, const StyleDef& style)
    {
        const auto& sc = scales()[(size_t) scaleIdx];
        const auto& styleList = sc.minorish ? style.minor : style.major;
        const auto& modeList = modeProgressions (scaleIdx);
        auto pickOne = [&] { return parseProgression (! modeList.empty() && chance (0.6f) ? pickFrom (modeList) : pickFrom (styleList)); };

        auto a = pickOne();
        if (count <= 4)
        {
            a.resize ((size_t) count, a.empty() ? Token {} : a.back());
            return a;
        }

        std::vector<Token> b;
        if (chance (0.6f))
        {
            // A then A again with a turnaround on the last chord.
            b = a;
            Token turn { 7, Dom7, false };
            if (b.back().root == 7) turn = sc.minorish ? Token { 10, -1, false } : Token { 10, Maj, false };
            b.back() = turn;
        }
        else
        {
            for (int tries = 0; tries < 6; ++tries)
            {
                b = pickOne();
                if (b[0].root != a[0].root || b[1].root != a[1].root) break;
            }
        }
        a.insert (a.end(), b.begin(), b.end());
        a.resize ((size_t) count, a.back());
        return a;
    }

    void substitute (std::vector<Token>& t, const Progression& prog, int scaleIdx, float colour, const StyleDef& style)
    {
        const int n = (int) t.size();
        auto unlocked = [&] (int i) { return ! prog.slots[(size_t) i].locked; };

        for (int i = 1; i < n; ++i)
        {
            if (! unlocked (i)) continue;
            auto& c = t[(size_t) i];
            if (scaleIdx == ScMajor)
            {
                if      (c.root == 5 && ! c.minorCase && c.quality < 0 && chance (colour * 0.22f)) c = { 5, Min, true };   // IV -> iv
                else if (c.root == 7 && chance (colour * 0.12f)) c = { 10, Maj, false };                                  // V -> bVII
                else if (c.root == 9 && chance (colour * 0.10f)) c = { 8, Maj, false };                                   // vi -> bVI
                else if (c.root == 0 && chance (colour * 0.15f)) c = { 9, -1, true };                                     // I -> vi
                else if (c.root == 5 && chance (colour * 0.15f)) c = { 2, -1, true };                                     // IV -> ii
            }
            else if (scaleIdx == ScMinor)
            {
                if      (c.root == 7 && c.minorCase && c.quality < 0 && chance (colour * 0.35f)) c = { 7, Dom7, false };  // v -> V7
                else if (c.root == 5 && c.minorCase && c.quality < 0 && chance (colour * 0.12f)) c = { 5, Maj, false };   // iv -> IV
                else if ((c.root == 5 || c.root == 8) && chance (colour * 0.10f)) c = { 1, Maj, false };                  // -> bII
                else if (c.root == 10 && chance (colour * 0.10f)) c = { 7, Dom7, false };                                 // bVII -> V7
            }
        }

        // Secondary dominants: approach the next chord from its own V7.
        for (int i = 1; i < n; ++i)
        {
            if (! unlocked (i)) continue;
            const auto& target = t[(size_t) ((i + 1) % n)];
            if (target.root == t[(size_t) i].root) continue;
            if (target.quality >= 0 && quality (target.quality).family == FDim) continue;
            if (chance (colour * 0.18f * (0.5f + style.jazz)))
                t[(size_t) i] = { mod12 (target.root + 7), Dom7, false };
        }

        // Tritone substitution of dominants.
        for (int i = 1; i < n; ++i)
            if (unlocked (i) && t[(size_t) i].quality == Dom7 && chance (colour * 0.2f * style.jazz))
                t[(size_t) i].root = mod12 (t[(size_t) i].root + 6);
    }

    std::mt19937 rng;
};
} // namespace moyo
