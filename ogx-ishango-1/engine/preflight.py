"""Pre-flight every beat (L10): asset exists, shot renders, motion floor and stray-text check.

Renders each planned line as a short slice, then runs qa_motion on the slices and OCR on a
mid-slice grab (word confidence >= 70, 3+ letters). Writes work/preflight/report.json.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.path.join(ROOT, "work")
PF = os.path.join(WORK, "preflight")


def ocr_words(img):
    r = subprocess.run(["tesseract", img, "-", "--psm", "11", "tsv"], capture_output=True, text=True)
    words = []
    for ln in r.stdout.splitlines()[1:]:
        c = ln.split("\t")
        if len(c) == 12 and c[11].strip():
            try:
                conf = float(c[10])
            except ValueError:
                continue
            w = c[11].strip()
            if conf >= 70 and sum(ch.isalpha() for ch in w) >= 3:
                words.append(w)
    return words


if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    os.makedirs(PF, exist_ok=True)
    plan = json.load(open(f"{WORK}/plan.json"))
    shots, missing = [], []
    for p in plan:
        s = dict(p)
        s["id"] = f"P{p['line']:02d}"
        s["dur"] = dur
        img = s.get("image")
        if img and not os.path.exists(os.path.join(WORK, "stills", img)):
            missing.append((p["line"], img))
            continue
        if s.get("subtitle_text"):
            s["subtitle"] = {"text": s["subtitle_text"], "start": 0.2, "end": dur - 0.2}
        if s.get("group_order"):
            g = json.load(open(f"{WORK}/plates/schematic_groups.json"))[s["sch_col"]]["groups_left_to_right"]
            gi = s["group_order"][0]
            s["groups"] = [[g[gi][0], g[gi][1], 0.2, dur]]
        shots.append(s)
    json.dump(shots, open(f"{PF}/shots.json", "w"), indent=1)
    if missing:
        print("MISSING ASSETS:", missing)
    jobs = 3
    ids = [s["id"] for s in shots]
    procs = [subprocess.Popen([sys.executable, f"{HERE}/ogx_engine.py", f"{PF}/shots.json", f"{WORK}/stills",
                               f"{PF}/out", ",".join(ids[k::jobs])], stdout=open(f"{PF}/render_{k}.log", "w"),
                              stderr=subprocess.STDOUT) for k in range(jobs)]
    for pr in procs:
        pr.wait()
    subprocess.run([sys.executable, f"{HERE}/qa_motion.py", f"{PF}/out", f"{PF}/motion.csv"],
                   stdout=subprocess.DEVNULL)
    report = {"missing": missing, "shots": {}}
    import csv
    mot = {r["shot"]: r for r in csv.DictReader(open(f"{PF}/motion.csv"))}
    for s in shots:
        v = f"{PF}/out/{s['id']}.mp4"
        g = f"{PF}/out/{s['id']}_grab.png"
        ok = os.path.exists(v)
        if ok:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(dur / 2), "-i", v, "-frames:v", "1", g])
        report["shots"][s["id"]] = {"rendered": ok, "motion": mot.get(s["id"], {}).get("pass"),
                                    "fg_travel_pct": mot.get(s["id"], {}).get("fg_travel_pct"),
                                    "ratio": mot.get(s["id"], {}).get("fg_bg_ratio"),
                                    "ocr": ocr_words(g) if ok else None}
    json.dump(report, open(f"{PF}/report.json", "w"), indent=1)
    bad = {k: v for k, v in report["shots"].items() if not v["rendered"] or v["motion"] in ("FAIL", None)}
    print("rendered", sum(v["rendered"] for v in report["shots"].values()), "/", len(shots), "| motion issues:", bad)
