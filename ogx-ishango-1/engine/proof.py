"""v1.2 PROOF clip for ogx-ishango-1 (Chief REQUEST CHANGES, follow-up 09). Zero credits.

Builds work_proof/ from the FROZEN v1.1 natural cut (work_v11 is read only):
  * same VO and music stems, cut at shot boundaries (no re-voicing, no word changes)
  * fix a: the real bone photo is the object of record on every line that describes the bone
  * fix b: animated map with labels DR Congo / Lake Edward / Ishango
  * fix c: guided notch count, numbers on screen, only the counts in the locked script
  * fix e: no real-name subtitles on generated excavation scenes
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
P = os.path.join(ROOT, "work_proof")
W, H, FPS = E.W, E.H, E.FPS
T_START = 33.66                  # v1.1 L08 shot start
VO_END = 119.62                  # just before L25's first word (119.65): keeps L24 whole
T_END = 121.0                    # picture/music tail after the last word
REAL = "Joeykentin · Wikimedia Commons · CC BY-SA 4.0"
SCH = "Albert1ls · Wikimedia Commons · CC BY 2.5"
NASA = "NASA Landsat · Wikimedia Commons · Public domain"
WARM = (242, 179, 90)


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


def crops():
    """Crops of the REAL photo (same file, same credit). Coordinates in the 891x1230 original."""
    src = Image.open(os.path.join(ROOT, "research/images/Ishango_bone_(cropped).jpg")).convert("RGB")
    boxes = {"real_full.png": None,
             "real_tip.png": (230, 20, 670, 460),        # quartz end + first notches
             "real_surface.png": (300, 820, 640, 1160),   # worn surface lower shaft
             "real_marks.png": (300, 560, 640, 900)}      # densest visible notching
    for name, b in boxes.items():
        (src if b is None else src.crop(b)).save(os.path.join(P, "stills", name))


# ---------------------------------------------------------------- map with labels (fix b)

def render_map_labels(spec, out, matte_out):
    n = int(round(spec["dur"] * FPS))
    src = cv2.cvtColor(cv2.imread(os.path.join(P, "stills", spec["image"])), cv2.COLOR_BGR2RGB)
    src = cv2.resize(src, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    src = cv2.convertScaleAbs(src, alpha=1.08, beta=-6)
    ih, iw = src.shape[:2]
    tx, ty = spec["target"]
    z0, z1 = spec["zoom_from"], spec["zoom_to"]
    base = max(W / iw, H / ih)
    ov = E.Overlays(["haze"], n, 11)
    wr, mw = E.ffmpeg_writer(out), E.ffmpeg_writer(matte_out, gray=True)
    f_big = E.font(E.F_SUB, 46)
    f_small = E.font(E.F_SUB, 36)
    for i in range(n):
        t = E.ease(i / max(1, n - 1))
        z = base * (z0 + (z1 - z0) * t)
        cx, cy = iw * (0.5 + (tx - 0.5) * t), ih * (0.5 + (ty - 0.5) * t)
        M = np.float32([[z, 0, W / 2 - z * cx], [0, z, H / 2 - z * cy]])
        fr = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        mx, my = int(z * iw * tx + M[0, 2]), int(z * ih * ty + M[1, 2])
        if t > 0.30:
            k = min(1.0, (t - 0.30) / 0.15)
            pulse = 0.5 + 0.5 * math.sin(i / FPS * 4.0)
            ring = np.zeros((H, W), np.float32)
            cv2.circle(ring, (mx, my), int(18 + 10 * pulse), 1.0, 3, cv2.LINE_AA)
            cv2.circle(ring, (mx, my), 6, 1.0, -1, cv2.LINE_AA)
            ring = cv2.GaussianBlur(ring, (0, 0), 1.2)[..., None] * k
            fr = np.clip(fr * (1 - ring) + np.array(WARM, np.float32) * ring, 0, 255).astype(np.uint8)
        fr = ov.apply(fr, i)
        img = Image.fromarray(fr)
        d = ImageDraw.Draw(img, "RGBA")
        tsec = i / FPS
        for lab in spec["labels"]:
            if tsec < lab["t"]:
                continue
            a = min(1.0, (tsec - lab["t"]) / 0.6)
            if lab.get("anchor") == "marker":
                px, py = mx + 34, my - 22
            else:
                px, py = z * iw * lab["xy"][0] + M[0, 2], z * ih * lab["xy"][1] + M[1, 2]
            f = f_big if lab.get("big") else f_small
            tw = d.textlength(lab["text"], font=f)
            x = px - tw / 2 if lab.get("anchor") != "marker" else px
            for dx, dy in ((2, 2), (-1, 1), (1, -1)):
                d.text((x + dx, py + dy), lab["text"], font=f, fill=(0, 0, 0, int(190 * a)))
            d.text((x, py), lab["text"], font=f, fill=(255, 255, 255, int(255 * a)))
        fr = E.draw_text_layers(np.array(img), spec, tsec, spec["dur"])
        wr.stdin.write(fr.tobytes())
        mw.stdin.write(np.full((H, W), 255, np.uint8).tobytes())
    for p_ in (wr, mw):
        p_.stdin.close()
        p_.wait()


# ---------------------------------------------------------------- guided count (fix c)

def col_groups():
    return json.load(open(os.path.join(ROOT, "work/plates/schematic_groups.json")))


def render_count(spec, out, matte_out):
    """Real photo (object of record) + the CC BY drawing; groups lit one at a time with their number."""
    n = int(round(spec["dur"] * FPS))
    # BG = the same real photo, heavily blurred (no generated imagery on the count shots)
    bg = cv2.cvtColor(cv2.imread(os.path.join(P, "stills", "real_full.png")), cv2.COLOR_BGR2RGB)
    bg = E.cover(bg, int(W * 1.15), int(H * 1.15))
    bg = (cv2.GaussianBlur(bg, (0, 0), 28).astype(np.float32) * 0.32).astype(np.uint8)
    photo = cv2.cvtColor(cv2.imread(os.path.join(P, "stills", "real_full.png")), cv2.COLOR_BGR2RGB)
    ph_h = 820
    ph_w = int(photo.shape[1] * ph_h / photo.shape[0])
    photo = cv2.resize(photo, (ph_w, ph_h), interpolation=cv2.INTER_AREA)
    # soft warm glow on the notched shaft (photo y 200..1110 of 1230), not on any single group
    glow = np.zeros((ph_h, ph_w), np.float32)
    s = ph_h / 1230.0
    cv2.rectangle(glow, (int(370 * ph_w / 891), int(200 * s)), (int(545 * ph_w / 891), int(1110 * s)), 1.0, -1)
    glow = cv2.GaussianBlur(glow, (0, 0), 14)[..., None]
    diag_src = cv2.cvtColor(cv2.imread(os.path.join(P, "stills", spec["diagram"])), cv2.COLOR_BGR2RGB)
    dw = 980
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
    dg_x0, dg_y0 = 820, (H - dh) // 2 + 30
    for i in range(n):
        t = E.ease(i / max(1, n - 1))
        tsec = i / FPS
        bx = -0.3 * 0.03 * W * (t - 0.5)
        bgf = cv2.warpAffine(bg, np.float32([[1, 0, -(bg.shape[1] - W) / 2 + bx], [0, 1, -(bg.shape[0] - H) / 2]]),
                             (W, H), borderMode=cv2.BORDER_REFLECT)
        fr = bgf.astype(np.float32)
        matte = np.zeros((H, W), np.float32)
        # photo panel: FG, drifts and pushes in slightly
        pz = 1.0 + 0.05 * t
        pdx = 0.038 * W * (t - 0.5)
        pw, phh = int(ph_w * pz), int(ph_h * pz)
        pim = cv2.resize(photo, (pw, phh), interpolation=cv2.INTER_LINEAR).astype(np.float32)
        if spec.get("glow_from") is not None and tsec >= spec["glow_from"]:
            ga = min(1.0, (tsec - spec["glow_from"]) / 0.5)
            g = cv2.resize(glow, (pw, phh))[..., None] * ga
            pim = pim * (1 + 0.28 * g) + np.array(WARM, np.float32) * 0.10 * g
        x0, y0 = int(ph_x0 + pdx - (pw - ph_w) / 2), int(ph_y0 - (phh - ph_h) / 2)
        xs, ys = max(0, x0), max(0, y0)
        xe, ye = min(W, x0 + pw), min(H, y0 + phh)
        fr[ys:ye, xs:xe] = np.clip(pim[ys - y0:ye - y0, xs - x0:xe - x0], 0, 255)
        matte[ys:ye, xs:xe] = 1.0
        # diagram panel: FG, drifts the other way
        ddx = -0.030 * W * (t - 0.5)
        dx0, dy0 = int(dg_x0 + ddx), dg_y0
        dimg = diag.astype(np.float32).copy()
        ink = (diag.mean(2) < 110).astype(np.float32)[..., None]
        labels = []
        for g in spec.get("groups", []):
            gx0, gx1, t_on, label = g
            if tsec < t_on:
                continue
            active = (tsec - t_on) < g_hold(spec, g)
            k = min(1.0, (tsec - t_on) / 0.25)
            m = np.zeros(ink.shape, np.float32)
            m[:, int(gx0 * dw) - 4:int(gx1 * dw) + 4] = 1.0
            amt = (0.9 if active else 0.45) * k
            dimg = dimg * (1 - amt * ink * m) + np.array(WARM, np.float32) * amt * ink * m
            labels.append((dx0 + (gx0 + gx1) / 2 * dw, dy0 - 64, label, 1.0 if active else 0.6, k))
        fr[dy0:dy0 + dh, max(0, dx0):min(W, dx0 + dw)] = dimg[:, max(0, -dx0):min(dw, W - dx0)]
        matte[dy0:dy0 + dh, max(0, dx0):min(W, dx0 + dw)] = 1.0
        fr = ov.apply(np.clip(fr, 0, 255).astype(np.uint8), i)
        img = Image.fromarray(fr)
        d = ImageDraw.Draw(img, "RGBA")
        for (lx, ly, lab, op, k) in labels:
            tw = d.textlength(lab, font=f_num)
            d.text((lx - tw / 2 + 2, ly + 2), lab, font=f_num, fill=(0, 0, 0, int(180 * k * op)))
            d.text((lx - tw / 2, ly), lab, font=f_num, fill=(*WARM, int(255 * k * op)))
        for sm in spec.get("sums", []):
            if tsec >= sm["t"]:
                k = min(1.0, (tsec - sm["t"]) / 0.4)
                tw = d.textlength(sm["text"], font=f_sum)
                x = dx0 + dw / 2 - tw / 2 if sm.get("pos") == "top" else dx0 + dw - tw
                y = dy0 - 170 if sm.get("pos") == "top" else dy0 + dh + 30
                d.text((x + 2, y + 2), sm["text"], font=f_sum, fill=(0, 0, 0, int(180 * k)))
                d.text((x, y), sm["text"], font=f_sum, fill=(255, 255, 255, int(255 * k)))
        # one credit line per real image (photo + drawing)
        for k_, txt in enumerate([REAL, SCH]):
            y = H - 98 + k_ * 40
            tw = d.textlength(txt, font=f_cred)
            d.rounded_rectangle([34, y - 6, 46 + tw + 12, y + 32], 8, fill=(0, 0, 0, 120))
            d.text((46, y), txt, font=f_cred, fill=(255, 255, 255, 230))
        wr.stdin.write(np.array(img).tobytes())
        mw.stdin.write((matte * 255).astype(np.uint8).tobytes())
    for p_ in (wr, mw):
        p_.stdin.close()
        p_.wait()


def g_hold(spec, g):
    gs = spec["groups"]
    idx = gs.index(g)
    return (gs[idx + 1][2] - g[2]) if idx + 1 < len(gs) else 99


# ---------------------------------------------------------------- plan

def words_for(line):
    L = json.load(open(os.path.join(V11, "timing/lines.json")))
    off = json.load(open(os.path.join(V11, "render/meta.json")))["vo_offset"]
    return [(w["w"], w["s"] + off) for w in next(x for x in L if x["line"] == line)["words"]]


def norm(w):
    return "".join(ch for ch in w.lower() if ch.isalnum() or ch == "-")


def build_specs():
    v11 = {s["id"]: s for s in json.load(open(os.path.join(V11, "render/shots.json")))}
    G = col_groups()
    ids = [f"L{k:02d}" for k in range(8, 25)]
    specs = []
    for sid in ids:
        s = dict(v11[sid])
        s["t0"] = round(s["t0"] - T_START, 3)
        if sid == "L24":
            s["dur"] = round(T_END - T_START - s["t0"], 3)
        rel0 = v11[sid]["t0"]
        if sid == "L08":
            s.update(kind="MAP_LABELS", zoom_from=1.0, zoom_to=2.3,
                     labels=[{"text": "DR CONGO", "xy": [0.30, 0.30], "t": 0.8, "big": True},
                             {"text": "Lake Edward", "xy": [0.40, 0.50], "t": 1.6},
                             {"text": "Ishango", "anchor": "marker", "t": 2.6}])
        elif sid in ("L09", "L10"):
            s.pop("subtitle", None)       # fix e: no real names on generated scenes
            s.pop("subtitle_text", None)
        elif sid in ("L16", "L17", "L18", "L19"):
            img = {"L16": "real_full.png", "L17": "real_surface.png", "L18": "real_tip.png", "L19": "real_marks.png"}[sid]
            s = {"id": sid, "t0": s["t0"], "dur": s["dur"], "line": s.get("line"), "type": "REAL", "ai": False,
                 "image": img, "credit": REAL, "fit": 0.86 if sid == "L16" else 0.80, "overlays": ["dust"],
                 "dir": [1, 0] if sid in ("L16", "L18") else [-1, 0], "push": "in"}
        elif sid in ("L20", "L21", "L22", "L23", "L24"):
            line = int(sid[1:])
            ws = [(norm(w), t - rel0) for w, t in words_for(line)]
            nums = [(w, t) for w, t in ws if w in ("three", "four", "five", "six", "seven", "eight", "nine", "ten",
                                                  "eleven", "thirteen", "seventeen", "nineteen", "twenty-one")]
            spec = {"id": sid, "t0": s["t0"], "dur": s["dur"], "kind": "COUNT", "type": "COUNT", "ai": False,
                    "line": line, "credits": [REAL, SCH], "glow_from": 0.3}
            if sid == "L20":
                spec["diagram"] = "colABC_marks.png"
                t168 = next(t for w, t in ws if w == "sixty-eight")
                spec["sums"] = [{"text": "168", "t": t168, "pos": "top"}]
            else:
                col, order, labels = {
                    "L21": ("A", [3, 2, 1, 0], ["11", "13", "17", "19"]),
                    "L22": ("B", [7, 6, 5, 4, 3, 2, 1, 0], ["3", "6", "4", "8", "10", "5", "5", "7"]),
                    "L23": ("C", [3, 2, 1, 0], ["11", "21", "19", "9"]),
                    "L24": ("B", [3, 3], ["10", "10 or 9?"]),
                }[sid]
                spec["diagram"] = f"col{col}_marks.png"
                gl = G[col]["groups_left_to_right"]
                cues = nums if sid != "L24" else [x for x in nums if x[0] in ("ten", "nine")]
                spec["groups"] = [[gl[gi][0], gl[gi][1], cues[k][1], labels[k]] for k, gi in enumerate(order)]
                if sid == "L24":
                    spec["groups"][1][2] = cues[1][1]
                sum_word = {"L21": ("sixty", "= 60"), "L22": ("forty-eight", "= 48"), "L23": ("sixty", "= 60")}.get(sid)
                if sum_word:
                    ts = next(t for w, t in ws if w == sum_word[0])
                    spec["sums"] = [{"text": sum_word[1], "t": ts}]
            s = spec
        specs.append(s)
    return specs


def main():
    os.makedirs(os.path.join(P, "shots"), exist_ok=True)
    os.makedirs(os.path.join(P, "stills"), exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, "work/stills")):
        if f.endswith((".png", ".jpg")) and not os.path.exists(os.path.join(P, "stills", f)):
            shutil.copy(os.path.join(ROOT, "work/stills", f), os.path.join(P, "stills", f))
    crops()
    specs = build_specs()
    json.dump(specs, open(os.path.join(P, "shots.json"), "w"), indent=1, ensure_ascii=False)
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    for s in specs:
        if only and s["id"] not in only:
            continue
        out, mo = os.path.join(P, "shots", s["id"] + ".mp4"), os.path.join(P, "shots", s["id"] + "_matte.mp4")
        if s.get("kind") == "MAP_LABELS":
            render_map_labels(s, out, mo)
        elif s.get("kind") == "COUNT":
            render_count(s, out, mo)
        else:
            E.render_shot(s, out, mo, os.path.join(P, "stills"))
        print("rendered", s["id"], s["dur"], flush=True)


# ---------------------------------------------------------------- audio + assembly (re-uses v1.1 stems)

def audio():
    A = os.path.join(P, "audio")
    os.makedirs(A, exist_ok=True)
    src = os.path.join(V11, "audio")
    total = T_END - T_START
    vo_len = VO_END - T_START
    # VO: v1.1 stem cut between L24's last word (119.50) and L25's first (119.65): a line boundary
    ff("-ss", f"{T_START}", "-t", f"{vo_len:.3f}", "-i", f"{src}/stem_vo.wav", "-af",
       f"afade=t=out:st={vo_len - 0.03:.3f}:d=0.03,apad=whole_dur={total:.3f}", "-t", f"{total:.3f}",
       f"{A}/stem_vo.wav")
    for k in ("music", "ambience"):     # already at their v1.1 bed levels
        ff("-ss", f"{T_START}", "-t", f"{total:.3f}", "-i", f"{src}/stem_{k}.wav", "-af",
           f"afade=t=in:d=0.4,afade=t=out:st={total - 1.6:.3f}:d=1.6", f"{A}/stem_{k}.wav")
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
    print("audio done", js["input_i"], js["input_tp"])


def assemble(name="OGX_Ishango_v1.2_PROOF.mp4"):
    specs = json.load(open(os.path.join(P, "shots.json")))
    lst = os.path.join(P, "concat.txt")
    with open(lst, "w") as f:
        for s in specs:
            f.write(f"file '{os.path.join(P, 'shots', s['id'] + '.mp4')}'\n")
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", os.path.join(P, "picture.mp4"))
    ff("-i", os.path.join(P, "picture.mp4"), "-i", os.path.join(P, "audio", "mix.wav"), "-map", "0:v", "-map", "1:a",
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(P, name))
    print("exported", name)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--audio":
        audio()
    elif len(sys.argv) > 1 and sys.argv[1] == "--assemble":
        assemble()
    else:
        main()
