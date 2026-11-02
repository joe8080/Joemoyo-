"""Kongo v1: build the narration track and timeline from 8 section MP3s.

- Lengthens sentence pauses slightly (the voice reads fast).
- Places sections on a global timeline with gaps for music.
- Maps ASR word times onto the script words (correct spellings for captions).
Outputs: build/vo.wav, build/timeline.json, build/captions.srt
"""
import json, re, subprocess, wave, difflib, os
import numpy as np

SR = 48000
B = "build"
os.makedirs(B, exist_ok=True)

SCRIPT = json.load(open("tts.json"))          # section -> text (as voiced)
WORDS = json.load(open("words.json"))         # section -> [[word, start, end], ...]

LEAD_IN = 2.0          # black + music before R1
GAPS = {"R1": 1.6, "R2": 5.5, "R3": 1.6, "R4": 1.8, "R5": 1.4, "R6": 1.8, "R7": 3.2, "R8": 0.0}
# R2 gap holds the title card; R7 gap is the silence after "the people who were taken"
TAIL = 9.0             # end card
PAUSE_MIN, PAUSE_ADD = 0.32, 0.28   # stretch sentence-level pauses


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().replace("ç", "c").replace("ã", "a"))


def stretch(sec):
    """Insert extra silence into sentence pauses; return audio and remapped word list."""
    a = load(f"vo/{sec}.mp3")
    words = WORDS[sec]
    cuts = []   # (sample_index, extra_seconds)
    for i in range(1, len(words)):
        gap = words[i][1] - words[i - 1][2]
        if gap >= PAUSE_MIN:
            mid = (words[i - 1][2] + words[i][1]) / 2
            cuts.append((mid, PAUSE_ADD))
    out, last, shift_marks = [], 0, []
    for t, extra in cuts:
        idx = int(t * SR)
        out.append(a[last:idx]); out.append(np.zeros(int(extra * SR), np.float32))
        last = idx; shift_marks.append((t, extra))
    out.append(a[last:])
    audio = np.concatenate(out)

    def remap(t):
        return t + sum(e for (m, e) in shift_marks if m <= t)
    new_words = [[w, remap(s), remap(e)] for w, s, e in words]
    return audio, new_words


def align(script_text, asr_words):
    """Give each script token a time from the matched ASR word."""
    toks = script_text.split()
    a = [norm(t) for t in toks]
    b = [norm(w[0]) for w in asr_words]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    times = [None] * len(toks)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w = asr_words[blk.b + k]
            times[blk.a + k] = (w[1], w[2])
    # interpolate gaps
    for i in range(len(times)):
        if times[i] is None:
            prev = next((times[j] for j in range(i - 1, -1, -1) if times[j]), (0.0, 0.0))
            nxt = next((times[j] for j in range(i + 1, len(times)) if times[j]), (prev[1] + 0.3, prev[1] + 0.6))
            times[i] = (prev[1], max(prev[1] + 0.05, nxt[0]))
    return [[t, s, e] for t, (s, e) in zip(toks, times)]


def main():
    order = [f"R{i}" for i in range(1, 9)]
    t = LEAD_IN
    track = [np.zeros(int(LEAD_IN * SR), np.float32)]
    timeline = {"sections": {}, "lead_in": LEAD_IN}
    for sec in order:
        audio, words = stretch(sec)
        dur = len(audio) / SR
        aligned = align(SCRIPT[sec], words)
        timeline["sections"][sec] = {
            "start": round(t, 3), "dur": round(dur, 3),
            "words": [[w, round(t + s, 3), round(t + e, 3)] for w, s, e in aligned]}
        track.append(audio)
        t += dur
        g = GAPS[sec]
        track.append(np.zeros(int(g * SR), np.float32))
        timeline["sections"][sec]["gap_after"] = g
        t += g
    timeline["end_card"] = round(t, 3)
    track.append(np.zeros(int(TAIL * SR), np.float32))
    t += TAIL
    timeline["total"] = round(t, 3)
    vo = np.concatenate(track)
    with wave.open(f"{B}/vo.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(vo, -1, 1) * 32767).astype(np.int16).tobytes())
    json.dump(timeline, open(f"{B}/timeline.json", "w"), indent=1, ensure_ascii=False)
    write_srt(timeline)
    print("total", timeline["total"], "end_card", timeline["end_card"])


def fmt(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"


def write_srt(tl):
    cues = []
    for sec, d in tl["sections"].items():
        line, st = [], None
        for i, (w, s, e) in enumerate(d["words"]):
            if st is None:
                st = s
            line.append(w)
            text = " ".join(line)
            end_sentence = w.endswith((".", "?", "!", ".\"", "?\"", ".”"))
            nxt_long = len(text) > 34
            if end_sentence or nxt_long or i == len(d["words"]) - 1:
                cues.append((st, e + 0.15, text))
                line, st = [], None
    for n in range(len(cues) - 1):
        s0, e0, tx = cues[n]
        cues[n] = (s0, min(e0, cues[n + 1][0] - 0.04), tx)
    with open(f"{B}/captions.srt", "w") as f:
        for n, (s, e, text) in enumerate(cues, 1):
            f.write(f"{n}\n{fmt(s)} --> {fmt(e)}\n{text}\n\n")


if __name__ == "__main__":
    main()
