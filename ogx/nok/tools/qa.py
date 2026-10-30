"""Proof from RENDERED frames (Lessons 27-29 Oct). Writes build/qa/qa_report.json.
  python3 tools/qa.py <final.mp4> <qa_proxy_overlays_off.mp4>
1. OCR text inventory: a grab every 30 s + every real-image credit + every name subtitle + the end card.
   Every string found must be an allowed credit line, an allowed name subtitle or the end-card wordmark.
2. Optical-flow parallax per shot on the overlays-OFF proxy (overlays don't count as motion): FG and BG travel
   as % of frame width over the shot, using the renderer's own FG mask. Floors: FG >= 3 %, FG/BG >= 2.
3. freezedetect at -50 dB on the overlays-OFF proxy (no static plate hidden under overlays).
4. Runtime and loudness (EBU R128 integrated, true peak) of the final file."""
import sys, json, re, subprocess, pathlib, difflib
import numpy as np, cv2
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import render

ROOT = pathlib.Path(__file__).resolve().parents[1]
FINAL, PROXY = sys.argv[1], sys.argv[2]
import os
VER = os.environ.get("OGX_VER")          # v1.1+: results go to build/<ver>/qa (v1.0's build/qa untouched)
OUT = (ROOT / "build" / VER / "qa") if VER else (ROOT / "build/qa"); OUT.mkdir(parents=True, exist_ok=True)
FILM = render.FILM; SH = FILM["shots"]; FPS = FILM["fps"]
ALLOWED = sorted({s["credit"] for s in SH if s["credit"]} | {s["name"]["text"] for s in SH if s.get("name")}
                 | {"ORIGINEX HUMAN ARCHIVES"})

def grab(path, t, w=1920, h=1080):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-s", f"{w}x{h}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3) if len(raw) == w * h * 3 else None

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

FLOW_ONLY = FINAL == "-"          # quick motion check on a proxy before the full render
# ---------- 1. OCR ----------
if not FLOW_ONLY:
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
times = {round(t, 2): "every 30 s" for t in np.arange(15.0, FILM["total"], 30.0)}
for s in SH:
    if s["credit"]: times[round((s["t0"] + s["t1"]) / 2, 2)] = f"credit {s['line']} {s.get('real')}"
    if s.get("name"): times[round((s["name"]["t0"] + s["name"]["t1"]) / 2, 2)] = f"name {s['line']}"
times[round(FILM["total"] - 2.0, 2)] = "end card"
inv, bad = [], 0
for t in ([] if FLOW_ONLY else sorted(times)):
    fr = grab(FINAL, t)
    res, _ = ocr(fr)
    found = []
    for box, txt, conf in (res or []):
        conf = float(conf)
        if conf < 0.5 or len(norm(txt)) < 3: continue
        best = max(ALLOWED, key=lambda a: difflib.SequenceMatcher(None, norm(txt), norm(a)).ratio())
        # a fragment of an allowed line is fine (OCR may split a line); anything else is a fail
        ok = norm(txt) in norm(best) or difflib.SequenceMatcher(None, norm(txt), norm(best)).ratio() > 0.8 \
             or any(norm(txt) in norm(a) for a in ALLOWED)
        found.append({"text": txt, "conf": round(float(conf), 2), "allowed": bool(ok), "match": best if ok else None})
        bad += not ok
    cv2.imwrite(str(OUT / f"grab_{t:07.2f}.jpg"), cv2.resize(fr, (960, 540)), [cv2.IMWRITE_JPEG_QUALITY, 80])
    inv.append({"t": t, "why": times[t], "found": found})
# every real-image credit must actually be read back
cred_ok = []
for s in SH:
    if not s["credit"]: continue
    t = round((s["t0"] + s["t1"]) / 2, 2)
    txt = " ".join(f["text"] for e in inv if e["t"] == t for f in e["found"])
    r = difflib.SequenceMatcher(None, norm(txt), norm(s["credit"])).ratio()
    cred_ok.append({"line": s["line"], "image": s["real"], "expected": s["credit"], "read": txt, "similarity": round(r, 3)})

# ---------- 2. flow on overlays-off proxy ----------
PW, PHh = 960, 540
flow_rows = []
for s in SH:
    a, b = s["t0"] + 0.3, s["t1"] - 0.3
    if b - a < 0.6: a, b = s["t0"], s["t1"]
    ts = np.linspace(a, b - 2 / FPS, 5)
    fg_m, bg_m = [], []
    for t in ts:
        f0, f1 = grab(PROXY, t, PW, PHh), grab(PROXY, t + 2 / FPS, PW, PHh)
        if f0 is None or f1 is None: continue
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))   # so dark/flat frames still give trackable texture
        g0, g1 = (clahe.apply(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)) for x in (f0, f1))
        fl = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 4, 21, 3, 5, 1.1, 0)
        mag = np.linalg.norm(fl, axis=2)
        _, m = render.shot_frame(s, t, qa=True, want_mask=True)
        m = cv2.resize(m.astype(np.float32), (PW, PHh)) > 0.5
        core = cv2.erode(m.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
        back = cv2.erode((~m).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
        if core.sum() > 500: fg_m.append(np.median(mag[core]) / 2)    # px per frame
        if back.sum() > 500: bg_m.append(np.median(mag[back]) / 2)
    nfr = (s["t1"] - s["t0"]) * FPS
    fg = float(np.mean(fg_m)) * nfr / PW * 100 if fg_m else 0.0
    bg = float(np.mean(bg_m)) * nfr / PW * 100 if bg_m else 0.0
    flow_rows.append({"line": s["line"], "kind": s["kind"], "dur": round(s["t1"] - s["t0"], 2),
                      "fg_travel_pct": round(fg, 2), "bg_travel_pct": round(bg, 2),
                      "ratio": round(fg / bg, 2) if bg > 1e-3 else None,
                      "pass_floor": fg >= 3.0, "pass_ratio": (bg < 1e-3 and fg > 0) or (bg > 0 and fg / bg >= 2)})

# ---------- 3. freezedetect -50 dB on proxy ----------
fz = subprocess.run(["ffmpeg", "-i", PROXY, "-vf", "freezedetect=n=-50dB:d=1", "-map", "0:v:0", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
freezes = re.findall(r"freeze_start: ([\d.]+).*?freeze_duration: ([\d.]+)", fz, re.S)

if FLOW_ONLY:
    fgv = [r["fg_travel_pct"] for r in flow_rows]; fails = [r for r in flow_rows if not (r["pass_floor"] and r["pass_ratio"])]
    json.dump({"flow": flow_rows, "freezes": freezes}, open(OUT / "flow_check.json", "w"), indent=1)
    print("fg_min", min(fgv), "fg_median", float(np.median(fgv)), "fails", [(r["line"], r["fg_travel_pct"], r["bg_travel_pct"], r["ratio"]) for r in fails], "freezes", freezes)
    sys.exit(0)
# ---------- 4. runtime + loudness ----------
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", FINAL],
                           capture_output=True, text=True).stdout)
lo = subprocess.run(["ffmpeg", "-i", FINAL, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", lo)[-1]); TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lo)[-1])

fgv = [r["fg_travel_pct"] for r in flow_rows]
rat = [r["ratio"] for r in flow_rows if r["ratio"]]
rep = {"final": FINAL, "proxy_overlays_off": PROXY, "runtime_s": round(dur, 2),
       "runtime_ok": 270 <= dur <= 330, "loudness_I": I, "true_peak_dbtp": TP,
       "loudness_ok": abs(I + 14) <= 1 and TP <= -1.0,
       "ocr": {"grabs": len(inv), "disallowed_strings": bad, "allowed": ALLOWED, "inventory": inv},
       "credits_read_back": cred_ok,
       "flow": {"fg_min": round(min(fgv), 2), "fg_median": round(float(np.median(fgv)), 2),
                "ratio_min": round(min(rat), 2) if rat else None, "ratio_median": round(float(np.median(rat)), 2) if rat else None,
                "fails": [r for r in flow_rows if not (r["pass_floor"] and r["pass_ratio"])], "shots": flow_rows},
       "freezedetect_-50dB": [{"start": float(a), "dur": float(b)} for a, b in freezes]}
json.dump(rep, open(OUT / "qa_report.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: rep[k] for k in ("runtime_s", "runtime_ok", "loudness_I", "true_peak_dbtp", "loudness_ok")}),
      "ocr_bad", bad, "flow", {k: v for k, v in rep["flow"].items() if k not in ("shots",)} if not rep["flow"]["fails"] else rep["flow"]["fails"][:8],
      "freezes", rep["freezedetect_-50dB"], "credits", [(c["line"], c["similarity"]) for c in cred_ok])
