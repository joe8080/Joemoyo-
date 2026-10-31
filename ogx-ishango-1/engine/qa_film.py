"""QA on the RENDERED export (L4, L18, L19, L22). Never from config.

1. OCR text inventory: a grab every ~30 s + the middle of every real-image (credited) shot and
   every name-subtitle moment; text found is classified against the allowed list.
2. Credit read-back: OCR of the credit band vs credits.md (middle dot and '.' treated as equal).
3. freezedetect at -50 dB (noise=0.003 ~ -50 dB), d=2 s.
4. Loudness (ebur128 integrated, true peak) and runtime.
Writes qc/QA_REPORT.md.
"""
import difflib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.path.join(ROOT, "work")
QC = os.path.join(ROOT, "qc")

ALLOWED_PATTERNS = [r"reconstruction", r"\(ai\)", r"wikimedia", r"commons", r"cc by", r"public domain",
                    r"joeykentin", r"albert1ls", r"nasa", r"landsat", r"origine", r"human", r"archives",
                    r"ishango", r"bone", r"heinzelin", r"jean", r"hubert", r"damas", r"pletser",
                    r"huylebrouck", r"marshack", r"olivier", r"keller", r"brooks", r"smith", r"the"]


def probe_dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "csv=p=0", f], capture_output=True, text=True).stdout.strip())


def grab(f, t, out, crop=None):
    vf = ["-vf", crop] if crop else []
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", f, "-frames:v", "1", *vf, out])


def ocr(img, psm="11", conf_min=70):
    r = subprocess.run(["tesseract", img, "-", "--psm", psm, "tsv"], capture_output=True, text=True)
    words = []
    for ln in r.stdout.splitlines()[1:]:
        c = ln.split("\t")
        if len(c) == 12 and c[11].strip():
            try:
                conf = float(c[10])
            except ValueError:
                continue
            w = c[11].strip()
            if conf >= conf_min and sum(ch.isalnum() for ch in w) >= 2:
                words.append(w)
    return words


def classify(words):
    bad = [w for w in words if not any(re.search(p, w.lower()) for p in ALLOWED_PATTERNS)
           and sum(ch.isalpha() for ch in w) >= 3]
    return bad


def norm_credit(s):
    return re.sub(r"\s+", " ", s.replace("·", ".").replace("•", ".")).strip().lower()


def main(video):
    os.makedirs(QC, exist_ok=True)
    G = os.path.join(QC, "grabs")
    os.makedirs(G, exist_ok=True)
    shots = json.load(open(f"{WORK}/render/shots.json"))
    dur = probe_dur(video)
    rep = [f"# QA report — {os.path.basename(video)}", "", f"Runtime: **{dur:.2f} s ({int(dur // 60)}:{dur % 60:04.1f})** — target 4:30–5:30 → {'PASS' if 270 <= dur <= 330 else 'FAIL'}", ""]
    # 1. OCR inventory
    times = [(round(t, 1), "30s-grid") for t in [k * 30 + 2 for k in range(int(dur // 30) + 1)] if t < dur - 0.5]
    for s in shots:
        mid = s["t0"] + s["dur"] / 2
        if s.get("credit"):
            times.append((round(mid, 1), f"credit {s['id']}"))
        if s.get("subtitle"):
            times.append((round(s["t0"] + (s["subtitle"]["start"] + s["subtitle"]["end"]) / 2, 1), f"name {s['id']}"))
        if s["type"] in ("TITLE", "END"):
            times.append((round(mid, 1), f"card {s['id']}"))
    times.sort()
    rep += ["## 1. OCR text inventory (rendered frames)", "", "| t (s) | why | shot | text read (conf ≥ 70) | unexpected |", "|---|---|---|---|---|"]
    unexpected_total = 0
    for t, why in times:
        sid = next((s["id"] for s in shots if s["t0"] <= t < s["t0"] + s["dur"]), "?")
        img = os.path.join(G, f"g_{t:07.1f}.png")
        grab(video, t, img)
        words = ocr(img)
        bad = classify(words)
        stype = next((s["type"] for s in shots if s["id"] == sid), "")
        note = ", ".join(bad) if bad else "—"
        if bad and stype == "SCH":
            note += " (schematic line-art read as letters; check grab)"
        unexpected_total += len(bad) if stype != "SCH" else 0
        rep.append(f"| {t} | {why} | {sid} | {' '.join(words)[:120] or '—'} | {note} |")
    rep += ["", f"Unexpected words outside schematic shots: **{unexpected_total}**", ""]
    # 2. credit read-back
    rep += ["## 2. Credit read-back vs credits.md", "", "| shot | expected (credits.md) | OCR of credit band | similarity | result |", "|---|---|---|---|---|"]
    expected = {}
    for ln in open(f"{ROOT}/research/credits.md"):
        m = re.match(r"^\d+\. (\S+) \| [0-9a-f]{64} \| (.+?) \|", ln)
        if m:
            expected[m.group(1)] = m.group(2)
    fails = 0
    for s in shots:
        if not s.get("credit"):
            continue
        key = os.path.basename(s["image"]).replace("_marks", "")
        src = {"colA.png": "IshangoColumnA.png", "colB.png": "IshangoColumnB.png", "colC.png": "IshangoColumnC.png",
               "colABC.png": "IshangoColumnA.png", "MAP_lake_edward.jpg": "Wfm_lake_edward_lake_george.jpg"}.get(key, key)
        exp = expected.get(src, "?")
        img = os.path.join(G, f"credit_{s['id']}.png")
        grab(video, s["t0"] + s["dur"] / 2, img, "crop=900:70:20:1005,scale=2700:-1")
        got = " ".join(ocr(img, psm="7", conf_min=0))
        sim = difflib.SequenceMatcher(None, norm_credit(exp), norm_credit(got)).ratio()
        ok = sim >= 0.9 and norm_credit(s["credit"]) == norm_credit(exp)
        fails += 0 if ok else 1
        rep.append(f"| {s['id']} | {exp} | {got} | {sim:.3f} | {'PASS' if ok else 'FAIL'} |")
    rep += ["", f"Credit read-back failures: **{fails}**", ""]
    # 3. freezedetect
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-vf", "freezedetect=n=-50dB:d=2", "-map", "0:v",
                        "-f", "null", "-"], capture_output=True, text=True)
    fr = re.findall(r"freeze_start: ([\d.]+).*?freeze_duration: ([\d.]+)", r.stderr, re.S)
    rep += ["## 3. freezedetect (−50 dB, ≥ 2 s)", "", f"Frozen segments: **{len(fr)}** " + (str(fr) if fr else "(none)"), ""]
    # 4. loudness
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    i_val, tp_val = (float(I[-1]) if I else None), (float(TP[-1]) if TP else None)
    rep += ["## 4. Loudness", "", f"Integrated: **{i_val} LUFS** (target ≈ −14) · True peak: **{tp_val} dBTP** (≤ −1) → "
            + ("PASS" if i_val is not None and abs(i_val + 14) <= 1 and tp_val is not None and tp_val <= -1 else "CHECK"), ""]
    open(os.path.join(QC, "QA_REPORT.md"), "w").write("\n".join(rep) + "\n")
    print("\n".join(rep[:4]), f"\nunexpected={unexpected_total} credit_fails={fails} freezes={len(fr)} I={i_val} TP={tp_val}")


if __name__ == "__main__":
    main(sys.argv[1])
