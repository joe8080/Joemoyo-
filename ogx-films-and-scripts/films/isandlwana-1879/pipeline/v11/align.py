# Forced alignment + free decode of a wav span with pocketsphinx's bundled en-us model.
# usage: align.py WAV START END "expected text"
import sys, subprocess, re
from pocketsphinx import Decoder
wav, t0, t1, text = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", wav, "-ac", "1", "-ar", "16000",
                      "-f", "s16le", "-"], capture_output=True, check=True).stdout
words = re.sub(r"[^a-z' ]", " ", text.lower().replace("-", " ")).split()
d = Decoder(samprate=16000)
miss = [w for w in words if d.lookup_word(w) is None]
words = [w for w in words if w not in miss]
d.set_align_text(" ".join(words))
d.start_utt(); d.process_raw(raw, full_utt=True); d.end_utt()
print(f"OOV skipped: {miss}")
print("aligned:", d.hyp().hypstr if d.hyp() else "FAILED")
for seg in d.seg():
    if seg.word in ("<s>", "</s>", "<sil>"): continue
    print(f"  {seg.word:14s} {t0 + seg.start_frame/100:7.2f} -> {t0 + (seg.end_frame+1)/100:7.2f}  ascore {seg.ascore}")
d2 = Decoder(samprate=16000)
d2.start_utt(); d2.process_raw(raw, full_utt=True); d2.end_utt()
print("free decode:", d2.hyp().hypstr if d2.hyp() else None)
