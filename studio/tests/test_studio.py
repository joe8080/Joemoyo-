"""Fast checks for the studio.  Run:  python -m unittest discover -s studio/tests -t ."""
import json
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from studio import captions as C, fix as F, layers as L, project as P, text as T, voice as V
from studio.brands import KITS, resolve
from studio.util import StudioError

HAVE_FFMPEG = shutil.which("ffmpeg") is not None


def write_wav(path, x, sr=48000):
    x = np.clip(np.asarray(x, dtype=np.float64), -1, 1)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def speechlike(seconds=8, sr=48000, seed=0):
    """Bursts of tone with real gaps of silence: enough structure to stand in for a voice."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * sr)) / sr
    x = np.zeros_like(t)
    for start in np.arange(0.2, seconds - 0.6, 0.55):
        seg = (t >= start) & (t < start + 0.38)
        f = rng.uniform(140, 320)
        x[seg] = 0.35 * np.sin(2 * np.pi * f * t[seg]) * np.hanning(seg.sum())
    return x


class TextTests(unittest.TestCase):
    def test_wrap_respects_width(self):
        f = T.font("Montserrat", 40, 700)
        lines = T.wrap("the quick brown fox jumps over the lazy dog again and again", f, 400)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(T.text_width(ln, f) <= 400 for ln in lines))

    def test_fit_shrinks_long_text(self):
        size, lines = T.fit("A very long headline that cannot possibly fit on one line at this size",
                            "Montserrat", 800, 600, 2, 120, 30)
        self.assertLess(size, 120)
        self.assertLessEqual(len(lines), 2)

    def test_every_kit_font_loads(self):
        for kit in KITS.values():
            for name, weight in kit["fonts"].values():
                self.assertIsNotNone(T.font(name, 40, weight))


class TimingTests(unittest.TestCase):
    def test_spread_is_ordered_and_bounded(self):
        words = "Boring wins. Start small, automate it.".split()
        out = V.spread(words, 1.0, 4.0)
        self.assertEqual([w["t"] for w in out], words)
        self.assertAlmostEqual(out[0]["s"], 1.0, places=2)
        self.assertLessEqual(out[-1]["e"], 4.001)
        self.assertTrue(all(a["s"] < b["s"] for a, b in zip(out, out[1:])))

    def test_map_times_keeps_script_spelling(self):
        script = "It grows to £610,000 in thirty years.".split()
        heard = [("it", 0.0, 0.2), ("grows", 0.2, 0.6), ("to", 0.6, 0.7), ("six", 0.7, 0.9),
                 ("hundred", 0.9, 1.2), ("ten", 1.2, 1.4), ("thousand", 1.4, 1.9), ("in", 1.9, 2.0),
                 ("thirty", 2.0, 2.4), ("years", 2.4, 2.9)]
        out = V.map_times(script, heard)
        self.assertEqual([w["t"] for w in out], script)
        money = out[3]
        self.assertAlmostEqual(money["s"], 0.7, places=1)       # the number spans what was spoken
        self.assertAlmostEqual(out[4]["s"], 1.9, places=1)
        self.assertTrue(all(a["s"] <= b["s"] for a, b in zip(out, out[1:])))

    def test_sentence_split(self):
        self.assertEqual(V.split_sentences("One. Two? Three!"), ["One.", "Two?", "Three!"])


class CaptionTests(unittest.TestCase):
    def setUp(self):
        self.words = V.spread("Most people think getting rich is about picking winners. It is not.".split(), 0, 5)

    def test_groups_fit_the_frame(self):
        for fmt in ("16:9", "9:16"):
            W, H = P.FORMATS[fmt]
            for style in C.STYLES:
                ctx = L.Ctx(W, H, 30, resolve("wealth"), True)
                cap = C.Captions({"style": style}, ctx, self.words)
                self.assertTrue(cap.groups)
                for g in cap.groups:
                    self.assertLessEqual(g["w"], W * 0.9, f"{style} {fmt}")
                    self.assertGreaterEqual(g["x"], 0)

    def test_srt_is_well_formed(self):
        s = C.srt(self.words)
        self.assertTrue(s.startswith("1\n00:00:00,000 --> "))
        self.assertIn("picking winners.", s)


class ProjectTests(unittest.TestCase):
    def _project(self, d, **over):
        pr = {"title": "T", "voice": {"provider": "none"}, "formats": ["1:1"],
              "scenes": [{"say": "Hello there, this is a test."}, {"say": "And a second scene.", "transition": "cut"}]}
        pr.update(over)
        (Path(d) / "project.json").write_text(json.dumps(pr))
        return P.load(d)

    def test_timeline_adds_up(self):
        with tempfile.TemporaryDirectory() as d:
            plan = P.prepare(self._project(d), lambda *_: None)
            total = sum(sc["frames"] for sc in plan["scenes"]) / plan["fps"]
            self.assertAlmostEqual(plan["total"], total, places=6)
            self.assertEqual(len(plan["words"]), 10)
            self.assertTrue(all(a["s"] <= b["s"] for a, b in zip(plan["words"], plan["words"][1:])))

    def test_problems_are_reported_together(self):
        with tempfile.TemporaryDirectory() as d:
            pr = self._project(d, scenes=[{"visual": "missing.jpg", "overlays": [{"type": "sparkle"}]},
                                          {"transition": "teleport"}])
            with self.assertRaises(StudioError) as cm:
                P.prepare(pr, lambda *_: None)
            msg = str(cm.exception)
            self.assertIn("missing.jpg", msg)
            self.assertIn("sparkle", msg)
            self.assertIn("teleport", msg)

    def test_bad_json_is_explained(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "project.json").write_text("{nope")
            with self.assertRaises(StudioError):
                P.load(d)

    @unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg")
    def test_render_makes_a_playable_file(self):
        from studio.render import render
        with tempfile.TemporaryDirectory() as d:
            self._project(d, captions="box", music="ambient", scenes=[
                {"say": "Hello there, this is a test.", "overlays": [{"type": "title", "text": "Test"}]},
                {"say": "And a second scene.", "transition": "slide_left", "visual": "grid",
                 "overlays": [{"type": "stat", "value": 42, "label": "answer"}]}])
            res = render(d, draft=True, jobs=1, log=lambda *_: None)
            out = res["outputs"][0]
            info = json.loads(subprocess.run(
                ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", out],
                stdout=subprocess.PIPE).stdout)
            v = next(s for s in info["streams"] if s["codec_type"] == "video")
            a = next(s for s in info["streams"] if s["codec_type"] == "audio")
            want = sum(sc["frames"] for sc in res["plan"]["scenes"])
            self.assertEqual(int(v["nb_read_frames"]), want)
            self.assertEqual((v["width"], v["height"]), (540, 540))
            self.assertEqual(a["codec_name"], "aac")
            self.assertTrue(Path(res["extras"]["srt"]).is_file())


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg")
class RepairTests(unittest.TestCase):
    def test_clean_audio_is_left_alone(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "clean.wav"
            write_wav(p, speechlike() * 1.9)
            m = F.measure_audio(p)
            self.assertIsNone(m["hum_hz"])
            self.assertIsNone(m["dead_channel"])
            self.assertLess(m["clipped_pct"], 0.01)
            finds, _ = F.plan_audio(m, target_lufs=m["lufs"])
            self.assertEqual(finds, [])

    def test_hum_noise_dead_channel_and_clipping_are_found(self):
        with tempfile.TemporaryDirectory() as d:
            sr = 48000
            x = speechlike(10)
            t = np.arange(len(x)) / sr
            rng = np.random.default_rng(3)
            x = x + 0.01 * rng.standard_normal(len(x)) + 0.02 * np.sin(2 * np.pi * 50 * t) \
                + 0.01 * np.sin(2 * np.pi * 100 * t)
            x[sr * 2: sr * 4] = np.clip(x[sr * 2: sr * 4] * 5, -0.3, 0.3)
            p = Path(d) / "bad.wav"
            write_wav(p, np.stack([x, np.zeros_like(x)], axis=1))
            m = F.measure_audio(p)
            self.assertEqual(m["hum_hz"], 50.0)
            self.assertEqual(m["dead_channel"], "right")
            self.assertGreater(m["clipped_pct"], 0.01)
            self.assertTrue(m["noise_steady"])
            res = F.fix(p, log=lambda *_: None)
            after = res["after"]["audio"]
            self.assertIsNone(after["dead_channel"])
            self.assertLess(after["hum_db"], m["hum_db"] - 8)
            self.assertGreater(after["snr_db"], m["snr_db"] + 5)
            self.assertAlmostEqual(after["lufs"], -16.0, delta=1.5)

    def test_dark_video_is_lifted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "dark.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=25:d=3",
                            "-vf", "eq=gamma=0.35", "-pix_fmt", "yuv420p", str(p)], check=True)
            res = F.fix(p, stabilize="off", log=lambda *_: None)
            self.assertTrue(any("dark" in f[1] for f in res["findings"]))
            self.assertGreater(res["after"]["video"]["luma"], res["before"]["video"]["luma"] + 15)


if __name__ == "__main__":
    unittest.main()


class PluginTests(unittest.TestCase):
    """The plugin maths, on synthetic audio where the right answer is known."""

    def _noise(self, seconds=6, seed=1):
        rng = np.random.default_rng(seed)
        return rng.standard_normal(int(seconds * 48000)).astype(np.float32) * 0.05

    def _band(self, x, lo, hi):
        f = np.fft.rfftfreq(len(x), 1 / 48000)
        X = np.fft.rfft(x)
        X[(f < lo) | (f > hi)] = 0
        return np.fft.irfft(X, len(x)).astype(np.float32)

    def test_matchtone_moves_a_harsh_recording_toward_the_target(self):
        from studio import plugins as PL
        n = self._noise()
        x = n + 5.0 * self._band(n, 5000, 9000)                              # full-range, far too much treble
        st = np.stack([x, x], axis=1)
        y, rep = PL.matchtone(st, 48000)
        self.assertLess(rep["error_after"], rep["error_before"] * 0.6)
        before = PL.third_octave(x)[14]                                      # the 8 kHz band
        after = PL.third_octave(y.mean(axis=1))[14]
        self.assertLess(after, before - 8)
        self.assertEqual(y.shape, st.shape)

    def test_matchtone_can_follow_a_reference_track(self):
        from studio import plugins as PL
        with tempfile.TemporaryDirectory() as d:
            n = self._noise(seed=2)
            dark = self._band(n, 100, 2000) + 0.05 * self._band(n, 2000, 12000)
            write_wav(Path(d) / "ref.wav", dark * 4)
            bright = self._band(n, 100, 2000) + 1.0 * self._band(n, 2000, 12000)
            y, rep = PL.matchtone(np.stack([bright, bright], axis=1), 48000, ref=str(Path(d) / "ref.wav"), amount=1.0)
            self.assertLess(rep["error_after"], rep["error_before"])

    def test_deharsh_only_acts_when_treble_flares(self):
        from studio import plugins as PL
        n = self._noise(8, seed=3)
        mids = self._band(n, 400, 2500)
        hiss = self._band(n, 5000, 9000)
        gate = np.zeros(len(n), dtype=np.float32)
        gate[48000 * 4:] = 1.0                                               # treble blast in the second half only
        x = mids + hiss * (0.05 + 4.0 * gate)
        y, rep = PL.deharsh(np.stack([x, x], axis=1), 48000)
        y = y.mean(axis=1)
        e = lambda v, a, b: float(np.sqrt(np.mean(self._band(v[a:b], 5000, 9000) ** 2)))
        quiet_in, quiet_out = e(x, 48000, 48000 * 3), e(y, 48000, 48000 * 3)
        loud_in, loud_out = e(x, 48000 * 5, 48000 * 7), e(y, 48000 * 5, 48000 * 7)
        self.assertGreater(quiet_out, quiet_in * 0.9)                        # calm passage left alone
        self.assertLess(loud_out, loud_in * 0.5)                             # flare pulled down by 6 dB or more
        self.assertGreater(rep["peak"], 6)

    def test_presence_lifts_only_the_vocal_range(self):
        from studio import plugins as PL
        n = self._noise(seed=5)
        y, _ = PL.presence(np.stack([n, n], axis=1), 48000, amount=3.0)
        y = y.mean(axis=1)
        lv = lambda v, a, b: 20 * np.log10(np.sqrt(np.mean(self._band(v, a, b) ** 2)))
        self.assertAlmostEqual(lv(y, 2500, 3100) - lv(n, 2500, 3100), 3.0, delta=0.5)
        self.assertAlmostEqual(lv(y, 100, 300) - lv(n, 100, 300), 0.0, delta=0.3)
        self.assertAlmostEqual(lv(y, 12000, 16000) - lv(n, 12000, 16000), 0.0, delta=0.3)

    def test_chain_settings_and_errors(self):
        from studio import plugins as PL
        steps = PL.resolve("gig", {"level.lufs": "-16", "deharsh.max_cut": "6"})
        self.assertEqual([p.name for p, _ in steps], ["matchtone", "deharsh", "presence", "level"])
        self.assertEqual(steps[3][1]["lufs"], -16.0)
        self.assertEqual(steps[0][1]["voice_guard"], 2.0)
        self.assertEqual(steps[1][1]["max_cut"], 6.0)
        with self.assertRaises(StudioError):
            PL.resolve("nonsense")
        with self.assertRaises(StudioError):
            PL.resolve("gig", {"level.volume": "3"})

    def test_your_own_plugins_folder_is_loaded(self):
        from studio import plugins as PL
        PL.load_user_plugins()
        self.assertIn("warmth", PL.REGISTRY)
        self.assertIn("joe-gig", PL.CHAINS)

    @unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg")
    def test_plug_keeps_the_picture_and_the_length(self):
        from studio import plugins as PL
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "clip.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=25:d=4",
                            "-f", "lavfi", "-i", "anoisesrc=d=4:c=pink:a=0.3", "-shortest", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", str(src)], check=True)
            res = PL.run(src, "gig", log=lambda *_: None)
            info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                                              res["output"]], stdout=subprocess.PIPE).stdout)
            kinds = sorted(s["codec_type"] for s in info["streams"])
            self.assertEqual(kinds, ["audio", "video"])
            self.assertAlmostEqual(float(info["format"]["duration"]), 4.0, delta=0.15)
            self.assertEqual(len(res["notes"]), 4)
