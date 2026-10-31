"""Build ogx-ishango-1 from VO word timings + shot plan.

Stages (each reads/writes under work/):
  timing   : words.json (Scribe) + narration.txt -> timing/lines.json (per-line start/end)
  shots    : lines.json + plan.json -> render/shots.json (durations, subtitles, group cues)
  render   : renders every shot (parallel) via ogx_engine.py
  assemble : concat shots -> render/picture.mp4 (uses the shots list order, not a global timing.csv)
  mix      : vo + music bed + ambience -> stems + mix at about -14 LUFS, TP <= -1 dBTP
  export   : review/OGX_Ishango_v1.0_REVIEW.mp4 (1080p) + _720p, md5 + sha256
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.environ.get("OGX_WORK", os.path.join(ROOT, "work"))
FPS = 25
LEAD_IN = 1.2      # picture before first word
LEAD = 0.25        # cut this long before each line's first word
TAIL = 1.6         # hold after last word before the end card
END_DUR = 5.0

NUM = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
       "eleven": 11, "thirteen": 13, "seventeen": 17, "nineteen": 19, "twenty-one": 21}


def norm(w):
    return re.sub(r"[^a-z0-9\-]", "", w.lower().replace("’", "'"))


_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _under_1000(n):
    out = []
    if n >= 100:
        out += [_ONES[n // 100], "hundred"]
        n %= 100
        if n:
            out.append("and")
    if n >= 20:
        out.append(_TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else ""))
    elif n or not out:
        out.append(_ONES[n])
    return out


def num_words(tok):
    """'168' -> one hundred and sixty-eight; '20,000' -> twenty thousand; '1935' -> nineteen thirty-five."""
    raw = tok.replace(",", "")
    if not raw.isdigit():
        return [tok]
    n = int(raw)
    if 1100 <= n <= 1999 and "," not in tok:          # years as spoken
        hi, lo = divmod(n, 100)
        return _under_1000(hi) + (["hundred"] if lo == 0 else (["oh"] + _under_1000(lo) if lo < 10 else _under_1000(lo)))
    out = []
    if n >= 1000:
        out += _under_1000(n // 1000) + ["thousand"]
        n %= 1000
        if n and n < 100:
            out.append("and")
    if n or not out:
        out += _under_1000(n)
    return out


def expand(text_tokens):
    """Normalise tokens (numbers -> words, hyphenated words split) keeping a back-reference."""
    out, ref = [], []
    for i, t in enumerate(text_tokens):
        t = t.strip().strip(".,;:!?\"'()").lower()
        if not t:
            continue
        for w in num_words(t):
            for part in re.split(r"[-\s]+", w):
                n = norm(part)
                if n:
                    out.append(n)
                    ref.append(i)
    return out, ref


def stage_timing():
    import difflib
    words = [w for w in json.load(open(f"{WORK}/vo/words.json")) if w.get("type", "word") == "word"]
    lines = [l.split(" ", 1)[1] for l in open(f"{WORK}/narration_lock.txt").read().strip().splitlines()]
    s_tok, s_line = [], []
    for li, text in enumerate(lines):
        e, _ = expand(text.split())
        s_tok += e
        s_line += [li] * len(e)
    v_tok, v_ref = expand([w["text"] for w in words])
    sm = difflib.SequenceMatcher(None, s_tok, v_tok, autojunk=False)
    s2v = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            s2v[a + k] = v_ref[b + k]
    ratio = sm.ratio()
    out = []
    for li, text in enumerate(lines):
        idx = [k for k, l in enumerate(s_line) if l == li]
        hits = [s2v[k] for k in idx if k in s2v]
        if not hits:
            raise SystemExit(f"line {li + 1} not found in transcript")
        w0, w1 = min(hits), max(hits)
        out.append({"line": li + 1, "text": text, "start": words[w0]["start"], "end": words[w1]["end"],
                    "matched": round(len(hits) / max(1, len(idx)), 2),
                    "words": [{"w": w["text"], "s": w["start"], "e": w["end"]} for w in words[w0:w1 + 1]]})
    for a, b in zip(out, out[1:]):
        if b["start"] < a["end"]:
            raise SystemExit(f"overlap between lines {a['line']} and {b['line']}")
    os.makedirs(f"{WORK}/timing", exist_ok=True)
    json.dump(out, open(f"{WORK}/timing/lines.json", "w"), indent=1)
    low = [(o["line"], o["matched"]) for o in out if o["matched"] < 0.8]
    print("lines", len(out), "| match ratio", round(ratio, 3), "| vo end", out[-1]["end"], "| weak lines", low)


def stage_shots():
    lines = json.load(open(f"{WORK}/timing/lines.json"))
    plan = {p["line"]: p for p in json.load(open(f"{WORK}/plan.json"))}
    groups = json.load(open(f"{WORK}/plates/schematic_groups.json"))
    vo_off = LEAD_IN
    shots = []
    for i, L in enumerate(lines):
        p = dict(plan[L["line"]])
        t0 = 0.0 if i == 0 else vo_off + L["start"] - LEAD
        t1 = (vo_off + lines[i + 1]["start"] - LEAD) if i + 1 < len(lines) else vo_off + L["end"] + TAIL
        p["t0"], p["dur"] = round(t0, 3), round(t1 - t0, 3)
        p["id"] = f"L{L['line']:02d}"
        rel = lambda s: s + vo_off - t0
        # name subtitle: from the spoken name's first word, 2.6 s
        if p.get("subtitle_text"):
            first = norm(p.get("subtitle_cue", p["subtitle_text"].split()[0]))
            hit = next((w for w in L["words"] if norm(w["w"]).startswith(first)), L["words"][0])
            st = rel(hit["s"])
            en = min(p["dur"] - 0.2, st + 2.6)
            if en - st < 1.8:                       # short line: start earlier so it can be read
                st = max(0.25, en - 1.8)
            p["subtitle"] = {"text": p["subtitle_text"], "start": round(st, 2), "end": round(en, 2)}
        # schematic groups lit as their numbers are spoken
        if p.get("group_order"):
            col = groups[p["sch_col"]]["groups_left_to_right"]
            cues = [w for w in L["words"] if norm(w["w"]) in NUM]
            g = []
            for k, gi in enumerate(p["group_order"]):
                if k < len(cues):
                    g.append([col[gi][0], col[gi][1], round(rel(cues[k]["s"]), 2), round(rel(cues[k]["e"]) + 0.6, 2)])
            p["groups"] = g
        shots.append(p)
    end_t0 = shots[-1]["t0"] + shots[-1]["dur"]
    shots.append({"id": "L47_END", "type": "END", "dur": END_DUR, "t0": round(end_t0, 3),
                  "card_lines": ["OrigineX Human Archives"]})
    os.makedirs(f"{WORK}/render", exist_ok=True)
    json.dump(shots, open(f"{WORK}/render/shots.json", "w"), indent=1)
    total = end_t0 + END_DUR
    t26 = next(s["t0"] for s in shots if s["id"] == "L26")
    s36 = next(s for s in shots if s["id"] == "L36")
    json.dump({"vo_offset": vo_off, "total": round(total, 3), "thin0": t26, "thin1": round(s36["t0"] + s36["dur"], 3)},
              open(f"{WORK}/render/meta.json", "w"))
    print("shots", len(shots), "total", round(total, 2))


def stage_render(jobs=3):
    shots = json.load(open(f"{WORK}/render/shots.json"))
    ids = [s["id"] for s in shots]
    chunks = [ids[k::jobs] for k in range(jobs)]
    procs = [subprocess.Popen([sys.executable, f"{HERE}/ogx_engine.py", f"{WORK}/render/shots.json",
                               f"{WORK}/stills", f"{WORK}/render/shots", ",".join(c)],
                              stdout=open(f"{WORK}/render/render_{k}.log", "w"), stderr=subprocess.STDOUT)
             for k, c in enumerate(chunks) if c]
    for p in procs:
        p.wait()
    missing = [i for i in ids if not os.path.exists(f"{WORK}/render/shots/{i}.mp4")]
    print("render done; missing:", missing)


def stage_assemble():
    shots = json.load(open(f"{WORK}/render/shots.json"))
    with open(f"{WORK}/render/concat.txt", "w") as fh:
        for s in shots:
            fh.write(f"file 'shots/{s['id']}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                    f"{WORK}/render/concat.txt", "-c", "copy", f"{WORK}/render/picture.mp4"], check=True)
    # per-slice timing file (L16): one row per shot with its own in/out, not a full-film table
    with open(f"{WORK}/render/slice_timing.csv", "w") as fh:
        fh.write("shot,t0,dur,frames\n")
        for s in shots:
            fh.write(f"{s['id']},{s['t0']},{s['dur']},{int(round(s['dur'] * FPS))}\n")
    print("assembled")


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


def stage_mix():
    meta = json.load(open(f"{WORK}/render/meta.json"))
    total, off = meta["total"], meta["vo_offset"]
    A = f"{WORK}/audio"
    os.makedirs(A, exist_ok=True)
    subprocess.run([sys.executable, f"{HERE}/music.py", A, str(total),
                    str(meta.get("thin0", 0)), str(meta.get("thin1", 0))], check=True)
    # VO stem placed at the offset, padded to full length
    ff("-i", f"{WORK}/vo/vo_full.mp3", "-af",
       f"adelay={int(off * 1000)}|{int(off * 1000)},apad=whole_dur={total},aformat=sample_rates=48000:channel_layouts=stereo",
       "-t", str(total), f"{A}/stem_vo.wav")
    ff("-i", f"{A}/music_bed.wav", "-af", "volume=-17dB", "-t", str(total), f"{A}/stem_music.wav")
    ff("-i", f"{A}/ambience.wav", "-af", "volume=-26dB", "-t", str(total), f"{A}/stem_ambience.wav")
    # duck music + ambience under the voice, then mix and normalise
    ff("-i", f"{A}/stem_vo.wav", "-i", f"{A}/stem_music.wav", "-i", f"{A}/stem_ambience.wav",
       "-filter_complex",
       "[1:a][2:a]amix=inputs=2:normalize=0[bed];"
       "[0:a]asplit=2[vo][sc];"
       "[bed][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck];"
       "[vo][duck]amix=inputs=2:normalize=0[m]",
       "-map", "[m]", f"{A}/mix_pre.wav")
    # two-pass loudnorm to -14 LUFS / -1.5 dBTP
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{A}/mix_pre.wav", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    ff("-i", f"{A}/mix_pre.wav", "-af",
       f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
       f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,"
       "aresample=48000", f"{A}/mix.wav")
    print("mixed")


def stage_export(version="v1.0"):
    R = f"{ROOT}/review"
    os.makedirs(R, exist_ok=True)
    base = f"{R}/OGX_Ishango_{version}_REVIEW"
    ff("-i", f"{WORK}/render/picture.mp4", "-i", f"{WORK}/audio/mix.wav", "-map", "0:v", "-map", "1:a",
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{base}.mp4")
    ff("-i", f"{base}.mp4", "-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-preset", "slow",
       "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", f"{base}_720p.mp4")
    for f in (f"{base}.mp4", f"{base}_720p.mp4"):
        for algo in ("md5sum", "sha256sum"):
            out = subprocess.run([algo, f], capture_output=True, text=True).stdout
            open(f + "." + algo[:-3], "w").write(out.replace(R + "/", ""))
    print("exported", base)


def stage_srt():
    lines = json.load(open(f"{WORK}/timing/lines.json"))
    off = json.load(open(f"{WORK}/render/meta.json"))["vo_offset"]

    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(f"{ROOT}/review/OGX_Ishango_v1.0_REVIEW.srt", "w") as fh:
        for k, L in enumerate(lines, 1):
            fh.write(f"{k}\n{ts(L['start'] + off)} --> {ts(L['end'] + off + 0.2)}\n{L['text']}\n\n")
    print("srt")


if __name__ == "__main__":
    for st in sys.argv[1:]:
        globals()[f"stage_{st}"]()
