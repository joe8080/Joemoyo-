"""Derive spoken VO text from story/script.md: numbers to words, era labels, respellings."""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Raw spellings passed the producer's Whisper check (30 Oct). Add an entry here
# only for a line the full-VO transcript mishears, then re-voice that line alone.
RESPELL = {}
SPOKEN = []  # same rule as RESPELL

def spoken(text):
    for a, b in SPOKEN:
        text = text.replace(a, b)
    for a, b in RESPELL.items():
        text = re.sub(rf"\b{a}\b", b, text)
    return text

rows = [l.split("|") for l in (ROOT / "story/script.md").read_text().splitlines()
        if re.match(r"\| L\d\d ", l)]
lines = [(r[1].strip(), r[3].strip()) for r in rows]
out = "\n".join(f"{i}\t{spoken(t)}" for i, t in lines)
(ROOT / "story/vo_lines.txt").write_text(out + "\n")
words = sum(len(t.split()) for _, t in lines)
print(f"{len(lines)} lines, {words} words; at 140-155 wpm = {words/155:.2f}-{words/140:.2f} min")
