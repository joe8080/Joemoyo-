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
