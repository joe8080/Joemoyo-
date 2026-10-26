"""Replace garbled AI phone-screen text with clean text, tracked to the phone.

Usage: python3 phone_fix.py <job> <in.mp4> <out.mp4> [--preview DIR]
Jobs are defined in JOBS below: a time window, a reference time, the four
corners of the text box in the reference frame, a phone-screen region for
feature tracking, and a function that draws the replacement patch.
"""
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
PW, PH = 760, 136  # patch canvas size (box-local units, 2x for quality)


def draw_victor(ref_crop):
    """Ep 7: iOS-style notification text, keeping the app icon on the left."""
    w, h = 760, 136
    bg = np.median(ref_crop.reshape(-1, 3), axis=0)  # BGR median of the box
    bg = tuple(int(c) for c in bg[::-1])
    img = Image.new("RGBA", (w, h), bg + (255,))
    d = ImageDraw.Draw(img)
    d.text((118, 14), "VICTOR", font=ImageFont.truetype(FONT_BOLD, 34), fill=(25, 28, 34, 255))
    d.text((w - 22, 18), "now", font=ImageFont.truetype(FONT_MED, 26), fill=(110, 118, 128, 255), anchor="ra")
    d.text((118, 66), "I can get you your empire back. Meet me.", font=ImageFont.truetype(FONT_MED, 29), fill=(40, 44, 52, 255))
    alpha = Image.new("L", (w, h), 0)
    ImageDraw.Draw(alpha).rectangle([104, 6, w - 10, h - 6], fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(3))
    img.putalpha(alpha)
    return img


def draw_frozen(ref_crop):
    """Ep 6: red alert label, replacing FUNDS FROIZEN with FUNDS FROZEN."""
    w, h = 760, 460
    px = ref_crop.reshape(-1, 3).astype(int)
    reds = px[(px[:, 2] > 150) & (px[:, 1] < 120)]  # BGR: strong red, low green
    fill = tuple(int(c) for c in np.median(reds, axis=0)[::-1]) if len(reds) else (230, 60, 50)
    img = Image.new("RGBA", (w, h), fill + (255,))
    txt = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    f = ImageFont.truetype(FONT_BLACK, 150)
    d.text((w // 2, h * 0.30), "FUNDS", font=f, fill=(255, 245, 240, 255), anchor="mm")
    d.text((w // 2, h * 0.72), "FROZEN", font=f, fill=(255, 245, 240, 255), anchor="mm")
    glow = txt.filter(ImageFilter.GaussianBlur(10))
    img = Image.alpha_composite(img, Image.eval(glow, lambda v: v))
    img = Image.alpha_composite(img, txt)
    alpha = Image.new("L", (w, h), 0)
    ImageDraw.Draw(alpha).rounded_rectangle([34, 30, w - 34, h - 30], radius=40, fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(5))
    img.putalpha(alpha)
    return img


JOBS = {
    # corners: TL, TR, BR, BL of the text box in the reference frame (720x1280)
    "ep7": dict(t0=476 / 24, t1=552 / 24, tref=21.0, fade=1, occlude=False,
                corners=[(157, 488), (537, 447), (540, 515), (160, 555)],
                screen=(100, 120, 620, 1100), draw=draw_victor),
    "ep6": dict(t0=495 / 24, t1=544 / 24, tref=21.5, fade=1, occlude=True, every=6,
                corners=[(240, 545), (525, 587), (495, 732), (210, 685)],
                screen=(150, 290, 610, 1000), draw=draw_frozen),
}


def read_frames(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    return frames, fps


def main():
    job = JOBS[sys.argv[1]]
    src, dst = sys.argv[2], sys.argv[3]
    preview = sys.argv[5] if len(sys.argv) > 5 and sys.argv[4] == "--preview" else None
    frames, fps = read_frames(src)
    i0, i1, iref = (int(round(job[k] * fps)) for k in ("t0", "t1", "tref"))
    ref = frames[iref]
    corners = np.float32(job["corners"])

    # Patch in box-local coordinates, mapped onto the reference box.
    x, y, w, h = cv2.boundingRect(corners.astype(np.int32))
    patch = job["draw"](ref[y:y + h, x:x + w])
    pw, ph = patch.size
    rect = np.float32([(0, 0), (pw, 0), (pw, ph), (0, ph)])
    H_patch = cv2.getPerspectiveTransform(rect, corners)
    rgba = np.array(patch)
    p_bgr = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2BGR).astype(np.float32)
    p_a = rgba[:, :, 3].astype(np.float32) / 255.0

    # Feature tracking of the phone screen relative to the reference frame.
    sx0, sy0, sx1, sy1 = job["screen"]
    mask = np.zeros(ref.shape[:2], np.uint8)
    mask[sy0:sy1, sx0:sx1] = 255
    orb = cv2.ORB_create(3000)
    gref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    kr, dr = orb.detectAndCompute(gref, mask)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    ref_box = cv2.perspectiveTransform(corners[None], np.eye(3))[0]
    ref_mean = cv2.mean(gref, cv2.fillConvexPoly(np.zeros_like(gref), corners.astype(np.int32), 255))[0]

    smooth = None
    for i in range(i0, min(i1, len(frames))):
        f = frames[i]
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        k, d = orb.detectAndCompute(g, mask)
        H = None
        if d is not None and len(k) > 20:
            m = sorted(bf.match(dr, d), key=lambda m: m.distance)[:400]
            if len(m) >= 12:
                a = np.float32([kr[q.queryIdx].pt for q in m])
                b = np.float32([k[q.trainIdx].pt for q in m])
                H, inl = cv2.findHomography(a, b, cv2.RANSAC, 3.0)
                if H is None or inl.sum() < 12:
                    H = None
        box = cv2.perspectiveTransform(ref_box[None], H)[0] if H is not None else (smooth if smooth is not None else ref_box)
        smooth = box if smooth is None else 0.6 * box + 0.4 * smooth  # damp jitter
        Hf = cv2.getPerspectiveTransform(rect, np.float32(smooth))
        warp = cv2.warpPerspective(p_bgr, Hf, (f.shape[1], f.shape[0]))
        a = cv2.warpPerspective(p_a, Hf, (f.shape[1], f.shape[0]))[..., None]
        # Match the screen's brightness in this frame (glow flicker, lights going out).
        cur_mean = cv2.mean(g, cv2.fillConvexPoly(np.zeros_like(g), np.int32(smooth), 255))[0]
        gain = float(np.clip(cur_mean / max(ref_mean, 1), 0.3, 1.4))
        if job["occlude"]:
            # Keep a thumb (muted skin tones) in front of the new text.
            hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
            skin = ((hsv[..., 1] < 95) & (hsv[..., 2] > 45) & (hsv[..., 2] < 215)).astype(np.uint8)
            skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            skin = cv2.dilate(skin, np.ones((7, 7), np.uint8))
            skin = cv2.GaussianBlur(skin.astype(np.float32), (9, 9), 0)[..., None]
            a = a * (1 - skin)
        out = f.astype(np.float32) * (1 - a) + np.clip(warp * gain, 0, 255) * a
        # Fade the patch in over the first 3 frames.
        fade = min(1.0, (i - i0 + 1) / job["fade"])
        frames[i] = (f.astype(np.float32) * (1 - fade) + out * fade).astype(np.uint8)
        if preview and (i - i0) % job.get("every", 12) == 0:
            cv2.imwrite(f"{preview}/{sys.argv[1]}_{i:04d}.png", frames[i])

    h_, w_ = frames[0].shape[:2]
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w_}x{h_}",
         "-r", str(fps), "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
         "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", dst],
        stdin=subprocess.PIPE)
    for f in frames:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"{dst}: frames {i0}-{i1} patched")


if __name__ == "__main__":
    main()
