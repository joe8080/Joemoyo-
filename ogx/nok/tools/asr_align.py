"""Transcribe the VO in pause-delimited chunks (local Whisper via sherpa-onnx), check every word
against the locked script, and write per-line timings (line_timing.csv)."""
import re, csv, json, subprocess, sys, difflib, pathlib, wave
import numpy as np, sherpa_onnx

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = pathlib.Path(sys.argv[1])
VO = ROOT / "audio/vo/VO_16k.wav"

def silences(path, db=-40, d=0.18):
    out = subprocess.run(["ffmpeg", "-i", str(path), "-af", f"silencedetect=n={db}dB:d={d}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(st, en))

w = wave.open(str(VO)); sr = w.getframerate()
audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
dur = len(audio) / sr
sil = silences(VO)
# speech chunks between silences
edges, t = [], 0.0
for s, e in sil:
    if s - t > 0.05: edges.append((t, s))
    t = e
if dur - t > 0.05: edges.append((t, dur))

rec = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=str(MODEL / "small.en-encoder.int8.onnx"), decoder=str(MODEL / "small.en-decoder.int8.onnx"),
    tokens=str(MODEL / "small.en-tokens.txt"), language="en", task="transcribe", num_threads=4)
CACHE = ROOT / "audio/vo/asr_chunks.json"
chunks = json.load(open(CACHE)) if CACHE.exists() else []
for a, b in ([] if chunks else edges):
    st = rec.create_stream()
    st.accept_waveform(sr, audio[int(a * sr):int(b * sr)])
    rec.decode_stream(st)
    chunks.append({"start": round(a, 3), "end": round(b, 3), "text": st.result.text.strip()})
json.dump(chunks, open(CACHE, "w"), indent=1)

norm = lambda s: re.findall(r"[a-z0-9]+", s.lower().replace("'", ""))
lines = [l.rstrip("\n").split("\t", 1) for l in open(ROOT / "story/vo_lines.txt")]
script_words, owner = [], []
for i, (lid, txt) in enumerate(lines):
    for wd in norm(txt): script_words.append(wd); owner.append(i)
asr_words, asr_chunk = [], []
for ci, c in enumerate(chunks):
    for wd in norm(c["text"]): asr_words.append(wd); asr_chunk.append(ci)

sm = difflib.SequenceMatcher(a=script_words, b=asr_words, autojunk=False)
# map each chunk to the line owning most of its matched words
votes = [dict() for _ in chunks]
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        li, ci = owner[blk.a + k], asr_chunk[blk.b + k]
        votes[ci][li] = votes[ci].get(li, 0) + 1
chunk_line, last = [], 0
for v in votes:
    li = max(v, key=v.get) if v else last
    li = max(li, last); chunk_line.append(li); last = li
diffs = [op for op in sm.get_opcodes() if op[0] != "equal"]
report = []
for tag, a0, a1, b0, b1 in diffs:
    report.append({"op": tag, "line": lines[owner[min(a0, len(owner) - 1)]][0],
                   "script": " ".join(script_words[a0:a1]), "heard": " ".join(asr_words[b0:b1])})

rows = []
for i, (lid, txt) in enumerate(lines):
    cs = [c for c, l in zip(chunks, chunk_line) if l == i]
    rows.append({"line": lid, "start": cs[0]["start"] if cs else None, "end": cs[-1]["end"] if cs else None,
                 "heard": " ".join(c["text"] for c in cs)})
empty = [r["line"] for r in rows if r["start"] is None]
if empty:
    print("UNASSIGNED LINES:", empty)
    for c, l in zip(chunks, chunk_line): print(l, c)
    sys.exit(1)
# cut points: midpoint of the pause between consecutive lines
for i, r in enumerate(rows):
    r["cut_in"] = 0.0 if i == 0 else round((rows[i - 1]["end"] + r["start"]) / 2, 3)
for i, r in enumerate(rows):
    r["cut_out"] = round(dur, 3) if i == len(rows) - 1 else rows[i + 1]["cut_in"]
    r["dur"] = round(r["cut_out"] - r["cut_in"], 3)
with open(ROOT / "audio/vo/line_timing.csv", "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=["line", "start", "end", "cut_in", "cut_out", "dur", "heard"]); wr.writeheader(); wr.writerows(rows)
json.dump({"chunks": chunks, "diffs": report, "ratio": sm.ratio()}, open(ROOT / "audio/vo/asr_check.json", "w"), indent=1)
print(f"chunks={len(chunks)} lines={len(rows)} match_ratio={sm.ratio():.4f} empty_lines={sum(r['start'] is None for r in rows)}")
for d in report: print(d)
