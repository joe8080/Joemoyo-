# Machine check of every narration line in the mixed master: forced alignment (are all words there, in order,
# inside the line's slot?) plus a free decode word-recall score. Not a substitute for listening.
import json, re, subprocess, sys
from difflib import SequenceMatcher
from pocketsphinx import Decoder
mix, tl = sys.argv[1], json.load(open(sys.argv[2]))
def norm(t): return re.sub(r"[^a-z' ]", " ", t.lower().replace("-", " ")).split()
rows = []
for s in tl:
    if not s.get("vo_file"): continue
    t0, t1 = s["vo_at"] - 0.25, s["vo_at"] + s["vo_dur"] + 0.35
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", mix, "-ac", "1", "-ar",
                          "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    d = Decoder(samprate=16000)
    words = norm(s["text"]); oov = [w for w in words if d.lookup_word(w) is None]
    kw = [w for w in words if w not in oov]
    d.set_align_text(" ".join(kw)); d.start_utt(); d.process_raw(raw, full_utt=True); d.end_utt()
    ok = d.hyp() is not None
    segs = [g for g in d.seg() if g.word not in ("<s>", "</s>", "<sil>")] if ok else []
    first = t0 + segs[0].start_frame / 100 if segs else None
    last = t0 + (segs[-1].end_frame + 1) / 100 if segs else None
    f = Decoder(samprate=16000); f.start_utt(); f.process_raw(raw, full_utt=True); f.end_utt()
    hyp = norm(re.sub(r"\(\d\)", "", f.hyp().hypstr)) if f.hyp() else []
    sm = SequenceMatcher(None, kw, hyp); recall = sum(b.size for b in sm.get_matching_blocks()) / max(1, len(kw))
    rows.append(dict(n=s["n"], L=s["src"], vo_at=s["vo_at"], vo_end=s["vo_at"] + s["vo_dur"], aligned=ok,
                     first=first, last=last, recall=round(recall, 2), oov=oov, hyp=" ".join(hyp), text=s["text"]))
    m = int(s["vo_at"] // 60)
    print(f"L{s['src']:>2} {m}:{s['vo_at']%60:04.1f} aligned={ok} words {first and round(first,2)}-{last and round(last,2)} "
          f"slot {s['vo_at']:.2f}-{s['vo_at']+s['vo_dur']:.2f} recall={recall:.2f} oov={oov}", flush=True)
json.dump(rows, open("align_all.json", "w"), indent=1)
