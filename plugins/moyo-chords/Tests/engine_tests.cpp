// Engine tests for MOYO Chords. Plain C++, no JUCE:
//   g++ -std=c++17 -O2 -I../Source engine_tests.cpp -o engine_tests && ./engine_tests

#include <cstdio>
#include <map>
#include <set>
#include "MoyoGenerator.h"
#include "MoyoPerformance.h"

using namespace moyo;

static int failures = 0;
#define CHECK(cond, ...) do { if (!(cond)) { ++failures; std::printf ("FAIL: "); } else std::printf ("ok:   "); std::printf (__VA_ARGS__); std::printf ("\n"); } while (0)

static std::string progText (const Progression& p, int tonic, int scale)
{
    std::string s;
    for (int i = 0; i < p.count; ++i)
        s += chordName (tonic, scale, p.slots[(size_t) i]) + " (" + romanName (p.slots[(size_t) i]) + ")  ";
    return s;
}

int main()
{
    // ---- Theory ------------------------------------------------------------
    CHECK (diatonicQuality (ScMajor, 0, 0) == Maj && diatonicQuality (ScMajor, 2, 0) == Min && diatonicQuality (ScMajor, 11, 0) == Dim,
           "C major triads: I major, ii minor, vii diminished");
    CHECK (diatonicQuality (ScMajor, 0, 1) == Maj7 && diatonicQuality (ScMajor, 7, 1) == Dom7 && diatonicQuality (ScMajor, 2, 1) == Min7 && diatonicQuality (ScMajor, 11, 1) == Min7b5,
           "C major sevenths: Imaj7, V7, ii7, vii m7b5");
    CHECK (diatonicQuality (ScMajor, 5, 3) == Maj9s11 && diatonicQuality (ScMajor, 7, 3) == Dom13 && diatonicQuality (ScMajor, 2, 3) == Min11,
           "C major extended: IVmaj9#11, V13, ii11");
    CHECK (diatonicQuality (ScHarmonicMinor, 7, 1) == Dom7 && diatonicQuality (ScHarmonicMinor, 11, 1) == Dim7,
           "harmonic minor: V7 and vii dim7");
    CHECK (diatonicQuality (ScDorian, 5, 0) == Maj && diatonicQuality (ScPhrygian, 1, 0) == Maj && diatonicQuality (ScLydian, 2, 0) == Maj,
           "mode signature chords: Dorian IV, Phrygian bII, Lydian II are major");

    Chord c; c.root = 8; c.quality = Maj7;
    CHECK (chordName (0, ScMinor, c) == "Abmaj7" && romanName (c) == "bVImaj7", "naming in C minor: %s = %s", chordName (0, ScMinor, c).c_str(), romanName (c).c_str());
    c.root = 2; c.quality = Min7;
    CHECK (chordName (4, ScMajor, c) == "F#m7" && romanName (c) == "ii7", "naming in E major: %s = %s", chordName (4, ScMajor, c).c_str(), romanName (c).c_str());
    c.root = 11; c.quality = Min7b5;
    CHECK (romanName (c) == "viim7b5", "half-diminished roman: %s", romanName (c).c_str());

    bool qualitiesOk = true;
    for (int q = 0; q < NumQualities; ++q)
    {
        const auto& d = quality (q);
        qualitiesOk &= d.intervals.size() >= 3 && d.intervals[0] == 0 && std::is_sorted (d.intervals.begin(), d.intervals.end());
        qualitiesOk &= quality (d.simpler).level <= d.level;
        qualitiesOk &= findQualityBySuffix (d.suffix) == q;  // suffixes are unique
    }
    CHECK (qualitiesOk && (int) qualities().size() == NumQualities, "all %d chord types are well-formed with unique names", (int) NumQualities);

    // ---- Token parsing -----------------------------------------------------
    auto t = parseToken ("bVImaj7");
    CHECK (t.root == 8 && t.quality == Maj7 && ! t.minorCase, "parse bVImaj7");
    t = parseToken ("ii7");
    CHECK (t.root == 2 && t.quality == Min7 && t.minorCase, "parse ii7 as minor seventh");
    t = parseToken ("#ivdim7");
    CHECK (t.root == 6 && t.quality == Dim7, "parse #ivdim7");
    t = parseToken ("iim7b5");
    CHECK (t.root == 2 && t.quality == Min7b5, "parse iim7b5");
    t = parseToken ("V");
    CHECK (t.root == 7 && t.quality == -1 && ! t.minorCase, "parse V with no suffix");

    bool listsOk = true;
    int progressionCount = 0;
    auto checkList = [&] (const std::vector<const char*>& list)
    {
        for (auto* text : list)
        {
            ++progressionCount;
            std::istringstream in (text);
            std::string w;
            int words = 0;
            while (in >> w)
            {
                ++words;
                const auto tok = parseToken (w);
                const size_t numeralEnd = w.find_first_not_of ("b#IViv");
                if (numeralEnd != std::string::npos && tok.quality < 0) { listsOk = false; std::printf ("      unknown suffix in '%s'\n", w.c_str()); }
            }
            if (words != 4) { listsOk = false; std::printf ("      '%s' is not 4 chords\n", text); }
        }
    };
    for (const auto& st : styles()) { checkList (st.major); checkList (st.minor); }
    for (int sc = 0; sc < (int) scales().size(); ++sc) checkList (modeProgressions (sc));
    CHECK (listsOk, "all %d built-in progressions parse and have 4 chords", progressionCount);

    // ---- Generator ---------------------------------------------------------
    Generator gen (12345);
    bool genOk = true;
    int total = 0;
    for (int style = 0; style < (int) styles().size(); ++style)
        for (int scale = 0; scale < (int) scales().size(); ++scale)
            for (int count : { 4, 8 })
                for (int rep = 0; rep < 20; ++rep)
                {
                    Progression p; p.count = count;
                    gen.generate (p, scale, style, rep / 19.0f, (rep % 5) / 4.0f);
                    for (int i = 0; i < count; ++i)
                    {
                        const auto& ch = p.slots[(size_t) i];
                        genOk &= ch.root >= 0 && ch.root < 12 && ch.quality >= 0 && ch.quality < NumQualities;
                    }
                    ++total;
                }
    CHECK (genOk, "%d generated progressions across every style, scale and length are valid", total);

    // Complexity 0 gives triads; complexity 1 gives rich chords.
    int triads = 0, rich = 0, n0 = 0, n1 = 0;
    for (int rep = 0; rep < 200; ++rep)
    {
        Progression p;
        gen.generate (p, ScMinor, 2, 0.0f, 0.0f);
        for (int i = 0; i < 4; ++i) { triads += quality (p.slots[(size_t) i].quality).level == 0; ++n0; }
        gen.generate (p, ScMinor, 2, 1.0f, 0.0f);
        for (int i = 0; i < 4; ++i) { rich += quality (p.slots[(size_t) i].quality).level >= 2; ++n1; }
    }
    CHECK (triads == n0, "complexity 0%%: %d of %d chords are plain triads", triads, n0);
    CHECK (rich > n1 * 0.7, "complexity 100%%: %d of %d chords are 9ths or richer", rich, n1);

    // Colour 0 with plain triads stays inside the key for diatonic styles (Pop).
    int outside = 0, n2 = 0, borrowed = 0, n3 = 0;
    for (int rep = 0; rep < 300; ++rep)
    {
        Progression p;
        gen.generate (p, ScMajor, 4, 0.0f, 0.0f);
        for (int i = 0; i < 4; ++i) { outside += ! fitsScale (ScMajor, p.slots[(size_t) i].root, p.slots[(size_t) i].quality); ++n2; }
        gen.generate (p, ScMajor, 4, 0.0f, 1.0f);
        for (int i = 0; i < 4; ++i) { borrowed += ! fitsScale (ScMajor, p.slots[(size_t) i].root, p.slots[(size_t) i].quality); ++n3; }
    }
    CHECK (outside == 0, "colour 0%% (Pop, C major): %d of %d chords leave the key", outside, n2);
    CHECK (borrowed > n3 * 0.05 && borrowed < n3 * 0.6, "colour 100%%: %d of %d chords are borrowed or substituted", borrowed, n3);

    // Chords built on scale notes stay in the scale at every complexity when colour is 0.
    {
        int drift = 0, n4 = 0;
        for (int rep = 0; rep < 400; ++rep)
        {
            Progression p;
            gen.generate (p, ScMajor, 2 + (rep % 2) * 3, rep / 399.0f, 0.0f);  // Neo-Soul and Lo-fi
            for (int i = 0; i < 4; ++i)
            {
                const auto& ch = p.slots[(size_t) i];
                if (! fitsScale (ScMajor, ch.root, quality (ch.quality).family == FDom ? Dom7 : (isMinorFamily (ch.quality) ? Min : Maj))) continue;  // a borrowed chord by design
                drift += ! fitsScale (ScMajor, ch.root, ch.quality); ++n4;
            }
        }
        CHECK (drift == 0, "extensions stay in key: %d of %d in-key chords gained an out-of-key note", drift, n4);
    }

    // Variety: many distinct progressions from one setting.
    std::set<std::string> distinct;
    for (int rep = 0; rep < 200; ++rep)
    {
        Progression p;
        gen.generate (p, ScMinor, 0, 0.5f, 0.4f);
        distinct.insert (progText (p, 0, ScMinor));
    }
    CHECK (distinct.size() > 80, "variety: %d different progressions out of 200 tries (Hip-Hop, C minor)", (int) distinct.size());

    // Locks are respected by generate, vary and reroll never returns the same chord.
    {
        Progression p; p.count = 8;
        gen.generate (p, ScMinor, 1, 0.3f, 0.3f);
        p.slots[2].locked = true; p.slots[5].locked = true;
        const Chord keep2 = p.slots[2], keep5 = p.slots[5];
        bool locksOk = true, rerollOk = true;
        for (int rep = 0; rep < 50; ++rep)
        {
            gen.generate (p, ScMinor, rep % 10, 0.6f, 0.8f);
            gen.vary (p, ScMinor, rep % 10, 0.9f, 0.8f);
            locksOk &= p.slots[2].sameHarmony (keep2) && p.slots[5].sameHarmony (keep5);
            const Chord before = p.slots[1];
            gen.reroll (p, 1, ScMinor, rep % 10, 0.5f, 0.5f);
            rerollOk &= p.slots[1].root != before.root;
        }
        CHECK (locksOk, "locked chords survive 50 generate + vary passes");
        CHECK (rerollOk, "re-rolling a chord always changes its root");

        // Vary keeps the roots.
        Progression q; gen.generate (q, ScMajor, 2, 0.5f, 0.3f);
        const Progression orig = q;
        bool rootsKept = true;
        for (int rep = 0; rep < 30; ++rep) { gen.vary (q, ScMajor, 2, rep / 29.0f, 0.5f); for (int i = 0; i < 4; ++i) rootsKept &= q.slots[(size_t) i].root == orig.slots[(size_t) i].root; }
        CHECK (rootsKept, "vary keeps every chord root");
    }

    // ---- Voicing -----------------------------------------------------------
    {
        bool notesOk = true, pcsOk = true;
        double ledMove = 0, rootPosMove = 0;
        int pairs = 0;
        for (int rep = 0; rep < 300; ++rep)
        {
            Progression p; p.count = 8;
            gen.generate (p, rep % 10, rep % 10, (rep % 7) / 6.0f, 0.5f);
            for (int type = 0; type < NumVoicings; ++type)
                for (int bass = 0; bass < NumBassModes; ++bass)
                {
                    const auto v = voiceProgression (p, rep % 12, type, 60, bass);
                    for (int i = 0; i < p.count; ++i)
                    {
                        const auto& ch = p.slots[(size_t) i];
                        const auto& vc = v[(size_t) i];
                        notesOk &= vc.upper.size() >= 3 && vc.upper.size() <= 6 && std::is_sorted (vc.upper.begin(), vc.upper.end());
                        notesOk &= vc.upper.front() >= 36 && vc.upper.back() <= 96;
                        notesOk &= (bass == BassOff) == vc.bass.empty();
                        // Every sounded note must be a chord tone.
                        std::set<int> allowed;
                        for (int iv : quality (ch.quality).intervals) allowed.insert (mod12 (rep % 12 + ch.root + iv));
                        for (int n : vc.upper) pcsOk &= allowed.count (mod12 (n)) > 0;
                        for (int n : vc.bass) pcsOk &= allowed.count (mod12 (n)) > 0;
                        // The chord's third (or sus tone) must be present so the chord is recognisable.
                        const int third = voicing_detail::findInterval (quality (ch.quality).intervals, { 3, 4, 2, 5 });
                        bool hasThird = false;
                        for (int n : vc.upper) hasThird |= mod12 (n) == mod12 (rep % 12 + ch.root + third);
                        pcsOk &= hasThird;
                    }
                    if (type == VoiceClose && bass == BassOff)
                    {
                        std::vector<int> prevRootPos;
                        for (int i = 0; i < p.count; ++i)
                        {
                            const auto& ch = p.slots[(size_t) i];
                            const auto rp = voiceUpper (rep % 12 + ch.root, ch.quality, VoiceClose, 60, {}, 0, false);
                            if (i > 0)
                            {
                                ledMove += voicing_detail::movement (v[(size_t) i - 1].upper, v[(size_t) i].upper);
                                rootPosMove += voicing_detail::movement (prevRootPos, rp);
                                ++pairs;
                            }
                            prevRootPos = rp;
                        }
                    }
                }
        }
        CHECK (notesOk, "voicings: 3-6 sorted notes in a sensible range, bass only when asked");
        CHECK (pcsOk, "voicings: only chord tones are played and the third is always present");
        CHECK (ledMove < rootPosMove * 0.75, "voice leading: average movement %.2f semitones vs %.2f for root-position chords", ledMove / pairs, rootPosMove / pairs);
    }

    // Inversion override.
    {
        const auto root = voiceUpper (0, Maj, VoiceClose, 60, {}, 0, false);
        const auto first = voiceUpper (0, Maj, VoiceClose, 60, {}, 1, false);
        const auto second = voiceUpper (0, Maj, VoiceClose, 60, {}, 2, false);
        CHECK (mod12 (root.front()) == 0 && mod12 (first.front()) == 4 && mod12 (second.front()) == 7, "inversions put C, E, G in the bass of a C chord");
        const auto wide = voiceUpper (0, Maj, VoiceWide, 60, {}, -1, false);
        CHECK (wide.size() == 3 && wide[2] - wide[0] == 16, "wide voicing spreads C-G-E over a tenth");
    }

    // ---- Performance -------------------------------------------------------
    {
        Progression p; p.count = 4;
        gen.generate (p, ScMinor, 2, 0.8f, 0.4f);
        const auto voiced = voiceProgression (p, 0, VoiceOpen, 60, BassRoot);
        std::vector<double> beats (4, 4.0);
        bool perfOk = true, overlapOk = true, deterministic = true;
        for (int pat = 0; pat < (int) patterns().size(); ++pat)
            for (int rep = 0; rep < 6; ++rep)
            {
                PerfParams pp;
                pp.pattern = pat; pp.strumMs = (rep - 2) * 20.0; pp.humanise = rep / 5.0; pp.swing = rep / 5.0; pp.gate = 0.3 + 0.14 * rep; pp.bpm = 70 + 25 * rep; pp.seed = 99;
                const auto ev = renderPerformance (voiced, beats, pp);
                perfOk &= ! ev.empty() && ev.size() < 2048;
                std::map<int, double> lastEnd;
                for (size_t i = 0; i < ev.size(); ++i)
                {
                    const auto& e = ev[i];
                    perfOk &= e.start >= 0 && e.length > 0 && e.start + e.length <= 16.0 + 1.0e-9 && e.velocity >= 1 && e.velocity <= 127;
                    perfOk &= i == 0 || ev[i - 1].start <= e.start;
                    // Each note stays inside its own chord's time slot.
                    const int slot = std::min (3, (int) (e.start / 4.0));
                    perfOk &= e.start + e.length <= (slot + 1) * 4.0 + 1.0e-9;
                }
                const auto again = renderPerformance (voiced, beats, pp);
                deterministic &= again.size() == ev.size();
                for (size_t i = 0; i < ev.size() && i < again.size(); ++i)
                    deterministic &= again[i].start == ev[i].start && again[i].note == ev[i].note && again[i].velocity == ev[i].velocity;
            }
        CHECK (perfOk, "all %d rhythm patterns render valid, sorted notes inside their chord's time", (int) patterns().size());
        CHECK (deterministic, "rendering is repeatable for the same seed (export matches playback)");
        (void) overlapOk;

        // Sustain pattern = one note-on per chord tone per chord, full length.
        PerfParams plain; plain.pattern = 0; plain.gate = 1.0;
        const auto ev = renderPerformance (voiced, beats, plain);
        size_t expected = 0;
        for (const auto& v : voiced) expected += v.upper.size() + v.bass.size();
        bool full = true;
        for (const auto& e : ev) full &= std::abs (e.length - 4.0) < 1.0e-9;
        CHECK (ev.size() == expected && full, "sustain pattern: %d notes, each a full bar", (int) ev.size());

        // Strum spreads the note starts.
        PerfParams strum = plain; strum.strumMs = 30;
        const auto sv = renderPerformance (voiced, beats, strum);
        std::set<double> starts;
        for (const auto& e : sv) if (e.start < 4.0) starts.insert (e.start);
        CHECK (starts.size() == voiced[0].upper.size() + voiced[0].bass.size(), "strum gives each of the %d notes its own start time", (int) starts.size());

        // Chord lengths are respected.
        std::vector<double> mixed { 2.0, 8.0, 4.0, 2.0 };
        const auto mv = renderPerformance (voiced, mixed, plain);
        double end = 0;
        for (const auto& e : mv) end = std::max (end, e.start + e.length);
        CHECK (std::abs (end - 16.0) < 1.0e-9, "mixed chord lengths (1/2, 2, 1, 1/2 bars) end at beat %.1f", end);
    }

    // ---- A few examples for the log ---------------------------------------
    std::printf ("\nExamples:\n");
    Generator demo (2026);
    const std::pair<int, int> demos[] = { { 0, ScMinor }, { 1, ScMinor }, { 2, ScMajor }, { 3, ScMajor }, { 5, ScMajor }, { 8, ScPhrygian }, { 9, ScDorian } };
    for (const auto& d : demos)
    {
        Progression p;
        const auto& st = styles()[(size_t) d.first];
        demo.generate (p, d.second, d.first, st.complexity, st.colour);
        std::printf ("  %-22s %-9s  %s\n", st.name, scales()[(size_t) d.second].name, progText (p, 0, d.second).c_str());
    }

    std::printf (failures ? "\n%d FAILURE(S)\n" : "\nALL ENGINE TESTS PASSED\n", failures);
    return failures ? 1 : 0;
}
