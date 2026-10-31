"""v1.3 REVIEW builder for ogx-ishango-1 (Chief rulings on the v1.2 proof, follow-up 10). Zero credits.

Full film = v1.1 natural cut + every v1.2 proof fix across the whole film + two cuts:
  * C1: L07 ('Three questions ...')      * C2: L41-L43 (start of the recap)
Cuts sit inside the silences of the existing VO take: no word is changed, no re-voicing, no padding.
v1.0 / v1.1 / v1.2 files are read only; everything is written to work_v13/.

Usage:  python3 v13.py plan | render [main|nb] [ids] | audio | assemble | all
"""
import json
import math
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ogx_engine as E  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V11 = os.path.join(ROOT, "work_v11")
PRF = os.path.join(ROOT, "work_proof")
V13 = os.path.join(ROOT, os.environ.get("V13_DIR", "work_v13"))
ST = os.path.join(V13, "stills")
W, H, FPS = E.W, E.H, E.FPS
LEAD, TAIL, END_DUR = 0.25, 1.6, 5.0
REAL = "Joeykentin · Wikimedia Commons · CC BY-SA 4.0"
SCH = "Albert1ls · Wikimedia Commons · CC BY 2.5"
NOTE = "Count shown on a published drawing of the bone"       # Chief ruling 1 (follow-up 10)
WARM = (242, 179, 90)


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


# ---------------------------------------------------------------- top note on engine-rendered drawing shots

_orig_text = E.draw_text_layers


def _text_with_note(frame, spec, tsec, dur):
    fr = _orig_text(frame, spec, tsec, dur)
    if spec.get("top_note"):
        fr = draw_note(fr, spec["top_note"])
    return fr


def draw_note(frame, txt):
    img = Image.fromarray(frame)
    d = ImageDraw.Draw(img, "RGBA")
    f = E.font(E.F_LABEL, 26)
    x, y = 46, 38
    tw = d.textlength(txt, font=f)
    d.rounded_rectangle([x - 12, y - 6, x + tw + 12, y + 34], 8, fill=(0, 0, 0, 120))
    d.text((x, y), txt, font=f, fill=(255, 255, 255, 230))
    return np.array(img)


E.draw_text_layers = _text_with_note


# ---------------------------------------------------------------- assets (copies; frozen dirs are only read)

CROPS = {"real_full.png": None,
         "real_tip.png": (230, 20, 670, 460),        # quartz end + first notches
         "real_surface.png": (300, 820, 640, 1160),   # worn lower shaft
         "real_marks.png": (300, 560, 640, 900),      # densest visible notching
         "real_upper.png": (290, 180, 630, 520),      # upper notched shaft
         "real_mid.png": (300, 380, 640, 720),        # middle of the shaft
         "real_top.png": (160, 0, 760, 760)}          # quartz end in context (upper half)


def assets():
    os.makedirs(ST, exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, "work/stills")):
        if f.endswith((".png", ".jpg")) and not os.path.exists(os.path.join(ST, f)):
            shutil.copy(os.path.join(ROOT, "work/stills", f), os.path.join(ST, f))
    src = Image.open(os.path.join(ROOT, "research/images/Ishango_bone_(cropped).jpg")).convert("RGB")
    for name, b in CROPS.items():
        (src if b is None else src.crop(b)).save(os.path.join(ST, name))
    # neutral dark ground for drawing shots in the noBYSA cut (no generated or BY-SA imagery behind them)
    rng = np.random.default_rng(7)
    g = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (H // 6, W // 6)).astype(np.float32), (0, 0), 4),
                   (W, H), interpolation=cv2.INTER_CUBIC)
    g = (g - g.min()) / (np.ptp(g) + 1e-6)
    ground = np.stack([22 + 30 * g, 18 + 24 * g, 14 + 16 * g], -1).astype(np.uint8)
    cv2.imwrite(os.path.join(ST, "dark_ground.png"), ground[..., ::-1])


# ---------------------------------------------------------------- timeline: cuts inside the take's silences

def lines():
    off = json.load(open(os.path.join(V11, "render/meta.json")))["vo_offset"]
    L = {}
    for l_ in json.load(open(os.path.join(V11, "timing/lines.json"))):
        ws = l_["words"]
        L[l_["line"]] = {"text": l_["text"], "s": ws[0]["s"] + off, "e": ws[-1]["e"] + off}
    return L


def cuts(L):
    # C1: L07. Keep the pause that led into L08 (a section start): remove from the middle of the
    # L06/L07 gap to the point that leaves the original L07->L08 pause in front of L08.
    a1 = (L[6]["e"] + L[7]["s"]) / 2
    pause_before_08 = L[8]["s"] - L[7]["e"]
    keep_after = pause_before_08 - (a1 - L[6]["e"])
    b1 = L[8]["s"] - max(0.05, keep_after)
    # C2: L41-L43. Keep (almost all of) the L40->L41 section pause; resume just before L44's first word.
    a2 = L[41]["s"] - 0.20          # Scribe onsets run ~0.05 s late: stay well inside the silence
    b2 = L[44]["s"] - 0.05
    assert L[6]["e"] < a1 < L[7]["s"] and L[7]["e"] < b1 < L[8]["s"]
    assert L[40]["e"] < a2 < L[41]["s"] and L[43]["e"] < b2 < L[44]["s"]
    return [(round(a1, 3), round(b1, 3)), (round(a2, 3), round(b2, 3))]


def mapper(C):
    def m(t):
        sh = 0.0
        for a, b in C:
            if t >= b:
                sh += b - a
            elif t > a:
                raise ValueError(f"time {t} inside cut {a}-{b}")
        return t - sh
    return m


# ---------------------------------------------------------------- shot plans

def real(line, img, dirx=1, push="in", fit=0.80, overlays=("dust",)):
    return {"line": line, "type": "REAL", "ai": False, "image": img, "credit": REAL, "fit": fit,
            "overlays": list(overlays), "dir": [dirx, 0], "push": push}


def sch(line, img, bg, dirx=1, push="in", note=False):
    s = {"line": line, "type": "SCH", "ai": False, "image": img, "credit": SCH,
         "bg_image": bg, "bg_dim": 0.35 if bg != "dark_ground.png" else 1.0,
         "overlays": ["dust"], "dir": [dirx, 0], "push": push, "fit": 0.62 if "ABC" in img else 0.4}
    if note:
        s["top_note"] = NOTE
    return s


def ai(line, img, base, dirx=1, push="in"):
    s = {k: v for k, v in base.items() if k not in ("t0", "dur", "id", "subtitle", "subtitle_text", "subtitle_cue")}
    s.update({"line": line, "type": "AI", "ai": True, "image": img, "dir": [dirx, 0], "push": push})
    s.setdefault("layer_mode", "subject")
    return s


# lines whose v1.1 picture was an AI bone still presented as the object -> the real photo (main cut)
MAIN_REAL = {2: ("real_tip.png", 1, "in"), 4: ("real_mid.png", -1, "in"), 5: ("real_upper.png", 1, "out"),
             16: ("real_full.png", 1, "in"), 17: ("real_surface.png", -1, "in"), 18: ("real_top.png", 1, "in"),
             19: ("real_marks.png", -1, "in"), 25: ("real_mid.png", 1, "out"), 33: ("real_full.png", -1, "in"),
             34: ("real_surface.png", 1, "in"), 35: ("real_marks.png", -1, "out"), 36: ("real_upper.png", 1, "in"),
             44: ("real_top.png", -1, "out"), 45: ("real_full.png", 1, "in")}
# noBYSA: no photo of the bone exists outside BY-SA, so object lines show the CC BY drawing (never an AI bone
# presented as the object); non-object lines take an existing, labelled, non-bone AI still.
NB_SCH = {2: "colABC_marks.png", 3: "colABC_marks.png", 4: "colA_marks.png", 5: "colC_marks.png",
          16: "colABC_marks.png", 17: "colA_marks.png", 19: "colB_marks.png", 25: "colC_marks.png",
          33: "colABC_marks.png", 34: "colA_marks.png", 35: "colC_marks.png", 36: "colB_marks.png",
          44: "colABC_marks.png"}
NB_AI = {12: "26.png", 18: "26.png", 45: "01.png"}
COUNT = (20, 21, 22, 23, 24)
GROUPED_SCH = (27, 28)          # group highlights in time with the VO -> carry the drawing line too


def plan():
    L = lines()
    C = cuts(L)
    m = mapper(C)
    v11 = json.load(open(os.path.join(V11, "render/shots.json")))
    proof = {s["id"]: s for s in json.load(open(os.path.join(PRF, "shots.json")))}
    kept = [s for s in v11 if s.get("line") not in (7, 41, 42, 43) and s["type"] != "END"]
    main, nb, origin = [], [], {}
    for s in kept:
        ln, sid = s["line"], s["id"]
        t0 = 0.0 if ln == 1 else round(m(L[ln]["s"]) - LEAD, 3)
        base = {"id": sid, "t0": t0}
        # ---- main cut
        if ln in MAIN_REAL:
            img, dx, push = MAIN_REAL[ln]
            mm = dict(real(ln, img, dx, push, fit=0.86 if img == "real_full.png" else 0.80), **base)
            how_m = "real photo (was AI bone still)" if s["type"] == "AI" else "real photo"
        elif ln in COUNT:
            mm = dict(proof[sid], **base, top_note=NOTE, photo=True)
            mm.pop("dur", None)
            how_m = "guided count (photo + drawing)"
        elif ln == 8:
            mm = dict(proof[sid], **base)
            mm.pop("dur", None)
            how_m = "labelled map (v1.2)"
        elif s["type"] == "SCH":
            mm = dict(s, **base, bg_image="real_full.png", bg_dim=0.32)
            mm.pop("dur", None)
            if ln in GROUPED_SCH:
                mm["top_note"] = NOTE
            how_m = "drawing (BG now the real photo, blurred)"
        else:
            mm = dict(s, **base)
            mm.pop("dur", None)
            if ln in (9, 10):
                for k in ("subtitle", "subtitle_text"):
                    mm.pop(k, None)
                how_m = "AI excavation, name subtitle removed"
            else:
                how_m = "as v1.1"
        main.append(mm)
        # ---- noBYSA cut
        if ln in NB_SCH:
            nn = dict(sch(ln, NB_SCH[ln], "dark_ground.png", 1 if ln % 2 else -1, "in" if ln % 3 else "out"), **base)
            how_n = "CC BY drawing"
        elif ln in NB_AI and s.get("image") == NB_AI[ln]:
            nn = dict(s, **base)
            nn.pop("dur", None)
            how_n = "AI still 01 (labelled reconstruction of the act, as v1.1)"
        elif ln in NB_AI:
            nn = dict(ai(ln, NB_AI[ln], next(x for x in v11 if x.get("image") == NB_AI[ln])), **base)
            how_n = f"AI still {NB_AI[ln][:2]} (labelled, not a bone)" if NB_AI[ln] != "01.png" else \
                "AI still 01 (labelled reconstruction of the act)"
        elif ln in COUNT:
            nn = dict(mm, photo=False, credits=[SCH])
            how_n = "guided count (drawing only)"
        elif mm["type"] == "SCH":
            nn = dict(mm, bg_image="dark_ground.png", bg_dim=1.0)
            how_n = "drawing on dark ground"
        else:
            nn = dict(mm)
            how_n = "same as main"
        nb.append(nn)
        origin[sid] = (how_m, how_n)
    # durations from consecutive starts; END card after L46 + tail
    t_end = round(m(L[46]["e"]) + TAIL, 3)
    for seq in (main, nb):
        for i, s in enumerate(seq):
            s["dur"] = round((seq[i + 1]["t0"] if i + 1 < len(seq) else t_end) - s["t0"], 3)
        end = dict(next(x for x in v11 if x["type"] == "END"), t0=t_end, dur=END_DUR)
        seq.append(end)
    total = round(t_end + END_DUR, 3)
    meta = {"cuts_v11_time": C, "removed_s": round(sum(b - a for a, b in C), 3), "total": total,
            "v11_total": json.load(open(os.path.join(V11, "render/meta.json")))["total"],
            "thin0": round(m(L[26]["s"]) - LEAD, 3), "thin1": round(m(L[37]["s"]) - LEAD, 3),
            "origin": origin}
    os.makedirs(V13, exist_ok=True)
    json.dump(main, open(os.path.join(V13, "shots_main.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(nb, open(os.path.join(V13, "shots_noBYSA.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(meta, open(os.path.join(V13, "meta.json"), "w"), indent=1, ensure_ascii=False)
    return main, nb, meta


# ---------------------------------------------------------------- guided count (v1.2 renderer + drawing line,
#                                                                  + drawing-only layout for the noBYSA cut)

def g_hold(spec, g):
    gs = spec["groups"]
    idx = gs.index(g)
    return (gs[idx + 1][2] - g[2]) if idx + 1 < len(gs) else 99


def render_count(spec, out, matte_out):
    n = int(round(spec["dur"] * FPS))
    use_photo = spec.get("photo", True)
    if use_photo:
        bg = cv2.cvtColor(cv2.imread(os.path.join(ST, "real_full.png")), cv2.COLOR_BGR2RGB)
        bg = E.cover(bg, int(W * 1.15), int(H * 1.15))
        bg = (cv2.GaussianBlur(bg, (0, 0), 28).astype(np.float32) * 0.32).astype(np.uint8)
    else:
        bg = E.cover(cv2.cvtColor(cv2.imread(os.path.join(ST, "dark_ground.png")), cv2.COLOR_BGR2RGB),
                     int(W * 1.15), int(H * 1.15))
    photo = cv2.cvtColor(cv2.imread(os.path.join(ST, "real_full.png")), cv2.COLOR_BGR2RGB)
    ph_h = 820
    ph_w = int(photo.shape[1] * ph_h / photo.shape[0])
    photo = cv2.resize(photo, (ph_w, ph_h), interpolation=cv2.INTER_AREA)
    diag_src = cv2.cvtColor(cv2.imread(os.path.join(ST, spec["diagram"])), cv2.COLOR_BGR2RGB)
    if use_photo:
        dw = 1040
    else:
        dw = min(1500, int(680 * diag_src.shape[1] / diag_src.shape[0]))
    dh = int(diag_src.shape[0] * dw / diag_src.shape[1])
    diag = cv2.resize(diag_src, (dw, dh), interpolation=cv2.INTER_NEAREST)
    diag = cv2.GaussianBlur(diag, (0, 0), 0.8)
    diag = np.clip(diag.astype(np.float32) * np.array([0.97, 0.93, 0.84]), 0, 255).astype(np.uint8)
    ov = E.Overlays(["dust"], n, 5)
    wr, mw = E.ffmpeg_writer(out), E.ffmpeg_writer(matte_out, gray=True)
    f_num = E.font(E.F_SUB, 54)
    f_sum = E.font(E.F_SUB, 64)
    f_cred = E.font(E.F_LABEL, 24)
    ph_x0, ph_y0 = 110, (H - ph_h) // 2 - 30
    dg_x0 = 790 if use_photo else (W - dw) // 2
    dg_y0 = (H - dh) // 2 + 30
    credits = spec.get("credits", [REAL, SCH])
    for i in range(n):
        t = E.ease(i / max(1, n - 1))
        tsec = i / FPS
        bx = -0.3 * 0.03 * W * (t - 0.5)
        bgf = cv2.warpAffine(bg, np.float32([[1, 0, -(bg.shape[1] - W) / 2 + bx], [0, 1, -(bg.shape[0] - H) / 2]]),
                             (W, H), borderMode=cv2.BORDER_REFLECT)
        fr = bgf.astype(np.float32)
        matte = np.zeros((H, W), np.float32)
        x0 = y0 = pw = phh = 0
        if use_photo:
            pz = 1.0 + 0.05 * t
            pdx = 0.038 * W * (t - 0.5)
            pw, phh = int(ph_w * pz), int(ph_h * pz)
            pim = cv2.resize(photo, (pw, phh), interpolation=cv2.INTER_LINEAR).astype(np.float32)
            x0, y0 = int(ph_x0 + pdx - (pw - ph_w) / 2), int(ph_y0 - (phh - ph_h) / 2)
            xs, ys = max(0, x0), max(0, y0)
            xe, ye = min(W, x0 + pw), min(H, y0 + phh)
            fr[ys:ye, xs:xe] = np.clip(pim[ys - y0:ye - y0, xs - x0:xe - x0], 0, 255)
            matte[ys:ye, xs:xe] = 1.0
            ddx = -0.030 * W * (t - 0.5)
        else:
            ddx = 0.040 * W * (t - 0.5) * (1 if int(spec["line"]) % 2 else -1)
        dz = 1.0 if use_photo else 1.0 + 0.04 * t
        dwz, dhz = int(dw * dz), int(dh * dz)
        dsrc = diag if dz == 1.0 else cv2.resize(diag, (dwz, dhz), interpolation=cv2.INTER_LINEAR)
        dx0 = int(dg_x0 + ddx - (dwz - dw) / 2)
        dy0 = int(dg_y0 - (dhz - dh) / 2)
        dimg = dsrc.astype(np.float32).copy()
        ink = (dsrc.mean(2) < 110).astype(np.float32)[..., None]
        labels = []
        for g in spec.get("groups", []):
            gx0, gx1, t_on, label = g
            if tsec < t_on:
                continue
            active = (tsec - t_on) < g_hold(spec, g)
            k = min(1.0, (tsec - t_on) / 0.25)
            mk = np.zeros(ink.shape, np.float32)
            mk[:, int(gx0 * dwz) - 4:int(gx1 * dwz) + 4] = 1.0
            amt = (0.9 if active else 0.45) * k
            dimg = dimg * (1 - amt * ink * mk) + np.array(WARM, np.float32) * amt * ink * mk
            cx = dx0 + (gx0 + gx1) / 2 * dwz
            labels = [l_ for l_ in labels if abs(l_[0] - cx) > 1]
            labels.append((cx, dy0 - 64, label, 1.0 if active else 0.6, k))
        xa, xb = max(0, dx0), min(W, dx0 + dwz)
        ya, yb = max(0, dy0), min(H, dy0 + dhz)
        fr[ya:yb, xa:xb] = dimg[ya - dy0:yb - dy0, xa - dx0:xb - dx0]
        matte[ya:yb, xa:xb] = 1.0
        fr = ov.apply(np.clip(fr, 0, 255).astype(np.uint8), i)
        img = Image.fromarray(fr)
        d = ImageDraw.Draw(img, "RGBA")
        if use_photo and spec.get("glow_from") is not None and tsec >= spec["glow_from"]:
            ga = int(235 * min(1.0, (tsec - spec["glow_from"]) / 0.5))
            bxx = x0 + int(585 * pw / 891)
            by0, by1 = y0 + int(200 * phh / 1230), y0 + int(1110 * phh / 1230)
            d.line([(bxx - 18, by0), (bxx, by0), (bxx, by1), (bxx - 18, by1)], fill=(*WARM, ga), width=5)
        for (lx, ly, lab, op, k) in labels:
            tw = d.textlength(lab, font=f_num)
            d.text((lx - tw / 2 + 2, ly + 2), lab, font=f_num, fill=(0, 0, 0, int(180 * k * op)))
            d.text((lx - tw / 2, ly), lab, font=f_num, fill=(*WARM, int(255 * k * op)))
        for sm in spec.get("sums", []):
            if tsec >= sm["t"]:
                k = min(1.0, (tsec - sm["t"]) / 0.4)
                tw = d.textlength(sm["text"], font=f_sum)
                x = dx0 + dwz / 2 - tw / 2 if sm.get("pos") == "top" else dx0 + dwz - tw
                y = max(90, dy0 - 170) if sm.get("pos") == "top" else dy0 + dhz + 30
                d.text((x + 2, y + 2), sm["text"], font=f_sum, fill=(0, 0, 0, int(180 * k)))
                d.text((x, y), sm["text"], font=f_sum, fill=(255, 255, 255, int(255 * k)))
        y_c = H - 98 if len(credits) == 2 else H - 62
        for k_, txt in enumerate(credits):
            y = y_c + k_ * 40
            tw = d.textlength(txt, font=f_cred)
            d.rounded_rectangle([34, y - 6, 46 + tw + 12, y + 32], 8, fill=(0, 0, 0, 120))
            d.text((46, y), txt, font=f_cred, fill=(255, 255, 255, 230))
        fr = np.array(img)
        if spec.get("top_note"):
            fr = draw_note(fr, spec["top_note"])
        wr.stdin.write(fr.tobytes())
        mw.stdin.write((matte * 255).astype(np.uint8).tobytes())
    for p_ in (wr, mw):
        p_.stdin.close()
        p_.wait()


# ---------------------------------------------------------------- render (re-uses identical earlier renders by copy)

def reuse_source(spec, v11, proof):
    """An earlier render can be copied only if the spec is unchanged and the duration is identical."""
    sid = spec["id"]
    o = v11.get(sid)
    strip = lambda d: {k: v for k, v in d.items() if k not in ("t0", "dur")}  # noqa: E731
    if o and abs(o["dur"] - spec["dur"]) < 1e-6 and strip(o) == strip(spec):
        return os.path.join(V11, "render/shots", sid + ".mp4")
    p = proof.get(sid)
    if p and abs(p["dur"] - spec["dur"]) < 1e-6 and strip(p) == strip(spec):
        return os.path.join(PRF, "shots", sid + ".mp4")
    return None


def render(which, only=None):
    seq = json.load(open(os.path.join(V13, "shots_main.json" if which == "main" else "shots_noBYSA.json")))
    v11 = {s["id"]: s for s in json.load(open(os.path.join(V11, "render/shots.json")))}
    proof = {s["id"]: s for s in json.load(open(os.path.join(PRF, "shots.json")))}
    main = {s["id"]: s for s in json.load(open(os.path.join(V13, "shots_main.json")))}
    od = os.path.join(V13, "shots" if which == "main" else "shots_nb")
    os.makedirs(od, exist_ok=True)
    log = []
    for s in seq:
        sid = s["id"]
        if only and sid not in only:
            continue
        out, mo = os.path.join(od, sid + ".mp4"), os.path.join(od, sid + "_matte.mp4")
        if which == "nb" and main.get(sid) == s:
            log.append((sid, "same as main"))
            continue
        src = reuse_source(s, v11, proof)
        if src and os.path.exists(src):
            shutil.copy(src, out)
            ms = src.replace(".mp4", "_matte.mp4")
            if os.path.exists(ms):
                shutil.copy(ms, mo)
            log.append((sid, "copied " + os.path.relpath(src, ROOT)))
            print("copied", sid, flush=True)
            continue
        if s.get("kind") == "COUNT":
            render_count(s, out, mo)
        elif s.get("kind") == "MAP_LABELS":
            import proof as PR
            PR.P = V13
            PR.render_map_labels(dict(s), out, mo)
        else:
            E.render_shot(s, out, mo, ST)
        log.append((sid, "rendered"))
        print("rendered", sid, s["dur"], flush=True)
    return log


# ---------------------------------------------------------------- audio

def audio():
    meta = json.load(open(os.path.join(V13, "meta.json")))
    A = os.path.join(V13, "audio")
    os.makedirs(A, exist_ok=True)
    (a1, b1), (a2, b2) = meta["cuts_v11_time"]
    src = os.path.join(V11, "audio/stem_vo.wav")
    end = meta["v11_total"]
    fc = (f"[0:a]atrim=0:{a1},asetpts=PTS-STARTPTS[p1];"
          f"[0:a]atrim={b1}:{a2},asetpts=PTS-STARTPTS[p2];"
          f"[0:a]atrim={b2}:{end},asetpts=PTS-STARTPTS[p3];"
          "[p1][p2][p3]concat=n=3:v=0:a=1[o]")
    ff("-i", src, "-filter_complex", fc, "-map", "[o]", "-t", str(meta["total"]), f"{A}/stem_vo.wav")
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "music.py"), A, str(meta["total"]),
                    str(meta["thin0"]), str(meta["thin1"])], check=True)
    ff("-i", f"{A}/music_bed.wav", "-af", "volume=-17dB", "-t", str(meta["total"]), f"{A}/stem_music.wav")
    ff("-i", f"{A}/ambience.wav", "-af", "volume=-26dB", "-t", str(meta["total"]), f"{A}/stem_ambience.wav")
    ff("-i", f"{A}/stem_vo.wav", "-i", f"{A}/stem_music.wav", "-i", f"{A}/stem_ambience.wav",
       "-filter_complex",
       "[1:a][2:a]amix=inputs=2:normalize=0[bed];"
       "[0:a]asplit=2[vo][sc];"
       "[bed][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck];"
       "[vo][duck]amix=inputs=2:normalize=0[m]",
       "-map", "[m]", f"{A}/mix_pre.wav")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{A}/mix_pre.wav", "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    ff("-i", f"{A}/mix_pre.wav", "-af",
       f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
       f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,"
       "aresample=48000", f"{A}/mix.wav")
    print("audio done")


def assemble():
    for which, name in (("main", "OGX_Ishango_v1.3_REVIEW.mp4"), ("noBYSA", "OGX_Ishango_v1.3_REVIEW_noBYSA.mp4")):
        seq = json.load(open(os.path.join(V13, f"shots_{which}.json")))
        lst = os.path.join(V13, f"concat_{which}.txt")
        with open(lst, "w") as f:
            for s in seq:
                p = os.path.join(V13, "shots_nb", s["id"] + ".mp4")
                if which == "main" or not os.path.exists(p):
                    p = os.path.join(V13, "shots", s["id"] + ".mp4")
                f.write(f"file '{p}'\n")
        pic = os.path.join(V13, f"picture_{which}.mp4")
        ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", pic)
        ff("-i", pic, "-i", os.path.join(V13, "audio", "mix.wav"), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(V13, name))
        print("exported", name, flush=True)


if __name__ == "__main__":
    E.check_flags()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if cmd == "plan":
        assets()
        _, _, meta = plan()
        print(json.dumps({k: v for k, v in meta.items() if k != "origin"}, indent=1))
    elif cmd == "render":
        which = sys.argv[2]
        only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
        for r in render("main" if which == "main" else "nb", only):
            pass
    elif cmd == "audio":
        audio()
    elif cmd == "assemble":
        assemble()
