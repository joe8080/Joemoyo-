#!/usr/bin/env python3
"""Build SRT captions and a final transcript from the recorded VO timings.

Input is a segments JSON written by the VO step: one entry per recorded line,
placed where the edit puts it, with ElevenLabs character timestamps:

    [{"line_id": "L01", "start_s": 0.0, "text": "...",
      "alignment": {"characters": [...],
                    "character_start_times_seconds": [...],
                    "character_end_times_seconds": [...]}}, ...]

    python3 build_srt.py segments.json --narration SCRIPT_v1.5_clean_narration.md \
        --srt out/golden-stool-1900.en.srt --transcript out/transcript.md

Captions are the recorded words verbatim. The script refuses to write files if
the joined segment text differs from the locked narration (pass --allow-diff
only for a versioned, reviewed amendment, and record that in QC).
"""
import argparse
import json
import re
import sys
import unicodedata

MAX_LINE = 42
MAX_CUE_CHARS = 2 * MAX_LINE
MAX_CUE_S = 7.0
MIN_CUE_S = 1.0
MAX_CPS = 20.0


def norm(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", text).strip()


def narration_body(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith(">") or s == "---":
                continue
            s = re.sub(r"^\**\[?L\d+[a-z]?\]?\**[:.)\s-]+", "", s)  # drop line labels
            s = s.replace("**", "").replace("__", "")
            out.append(s)
    return norm(" ".join(out))


def words_from_alignment(seg):
    a = seg["alignment"]
    chars = a["characters"]
    starts = a["character_start_times_seconds"]
    ends = a["character_end_times_seconds"]
    words, cur, t0, t1 = [], "", None, None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                words.append((cur, t0, t1))
            cur, t0 = "", None
            continue
        if t0 is None:
            t0 = s
        cur += ch
        t1 = e
    if cur:
        words.append((cur, t0, t1))
    off = float(seg["start_s"])
    return [(w, off + s, off + e) for w, s, e in words]


def wrap(text):
    if len(text) <= MAX_LINE:
        return [text]
    best = None
    for i, ch in enumerate(text):
        if ch == " ":
            a, b = text[:i], text[i + 1:]
            if len(a) <= MAX_LINE and len(b) <= MAX_LINE:
                score = abs(len(a) - len(b))
                if best is None or score < best[0]:
                    best = (score, [a, b])
    return best[1] if best else [text[:MAX_LINE], text[MAX_LINE:]]


def cues_for(words):
    cues, cur = [], []
    for w in words:
        trial = " ".join(x[0] for x in cur + [w])
        too_long = len(trial) > MAX_CUE_CHARS or (cur and w[2] - cur[0][1] > MAX_CUE_S)
        if cur and too_long:
            cues.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.?!:;]\"?$", w[0]) and len(" ".join(x[0] for x in cur)) > 20:
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    return [(c[0][1], c[-1][2], " ".join(x[0] for x in c)) for c in cues]


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segments")
    ap.add_argument("--narration", required=True)
    ap.add_argument("--srt", required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--allow-diff", action="store_true")
    args = ap.parse_args()

    with open(args.segments, encoding="utf-8") as f:
        segments = sorted(json.load(f), key=lambda s: float(s["start_s"]))

    spoken = norm(" ".join(s["text"] for s in segments))
    locked = narration_body(args.narration)
    if spoken != locked:
        i = next((k for k, (a, b) in enumerate(zip(spoken, locked)) if a != b),
                 min(len(spoken), len(locked)))
        print(f"TEXT DIFF at char {i}:\n  recorded: ...{spoken[max(0, i - 40):i + 40]}...\n"
              f"  locked:   ...{locked[max(0, i - 40):i + 40]}...", file=sys.stderr)
        if not args.allow_diff:
            sys.exit(2)

    cues, warnings = [], []
    for seg in segments:
        for start, end, text in cues_for(words_from_alignment(seg)):
            cues.append([start, end, text, seg["line_id"]])
    for i, c in enumerate(cues):
        nxt = cues[i + 1][0] if i + 1 < len(cues) else c[1] + MIN_CUE_S
        if c[1] - c[0] < MIN_CUE_S:
            c[1] = min(c[0] + MIN_CUE_S, nxt - 0.04)
        if c[1] > nxt:
            warnings.append(f"overlap at {ts(c[0])} ({c[3]})")
            c[1] = nxt - 0.04
        cps = len(c[2]) / max(c[1] - c[0], 0.01)
        if cps > MAX_CPS:
            warnings.append(f"{ts(c[0])} {c[3]}: {cps:.1f} chars/s (> {MAX_CPS})")

    with open(args.srt, "w", encoding="utf-8") as f:
        for n, (s, e, text, _) in enumerate(cues, 1):
            f.write(f"{n}\n{ts(s)} --> {ts(e)}\n" + "\n".join(wrap(text)) + "\n\n")
    with open(args.transcript, "w", encoding="utf-8") as f:
        f.write("# Final transcript — The Golden Stool: Why the Asante Fought to Protect It\n\n")
        for seg in segments:
            f.write(f"[{ts(float(seg['start_s']))[:8]}] {seg['line_id']}  {norm(seg['text'])}\n\n")

    print(f"{len(cues)} cues written; text {'MATCHES' if spoken == locked else 'DIFFERS FROM'} locked narration")
    for w in warnings:
        print("WARN", w)


if __name__ == "__main__":
    main()
