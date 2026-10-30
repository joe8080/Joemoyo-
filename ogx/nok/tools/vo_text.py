"""Derive spoken VO text from story/script.md: numbers to words, era labels, respellings."""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Respellings: pending the producer's verdict on pron_test_v2; edit here only.
RESPELL = {
    "Breunig": "Broy-nikh",
    "Franke": "Frahn-keh",
    "Goethe": "Gur-tuh",
}
SPOKEN = [
    ("500 BCE and 200 CE", "five hundred B C E and two hundred C E"),
    ("20 to 620 CE", "twenty to six hundred and twenty C E"),
    ("800 and 400 BC", "eight hundred and four hundred B C"),
    ("800 BC", "eight hundred B C"),
    ("1500 BC", "fifteen hundred B C"),
    ("ninth to the fourth century BC", "ninth to the fourth century B C"),
    ("1928", "nineteen twenty-eight"),
    ("1943", "nineteen forty-three"),
    ("2005", "two thousand and five"),
    ("2009", "two thousand and nine"),
    ("2011 and 2014", "two thousand and eleven and two thousand and fourteen"),
    ("2017", "twenty seventeen"),
]

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
