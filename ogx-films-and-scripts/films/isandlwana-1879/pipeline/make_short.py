# 9:16 Short: film 186.3 s -> 248.2 s, blurred fill, burned captions, top banner.
import re, subprocess
T0, T1 = 186.3, 248.2
SRC = "OGX_Isandlwana_1879_v1.0.mp4"; OUT = "deliver/OGX_Isandlwana_1879_v1.0_Short_9x16.mp4"
def secs(t):
    h, m, s = t.replace(",", ".").split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
def ass_t(x):
    x = max(0, x); h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"
cues = re.split(r"\n\s*\n", open("OGX_Isandlwana_1879_v1.0_EN-GB.srt", encoding="utf-8").read().strip())
ev = []
for c in cues:
    ls = c.splitlines(); a, b = [secs(x.strip()) for x in ls[1].split("-->")]
    if b <= T0 or a >= T1: continue
    txt = "\\N".join(ls[2:])
    ev.append(f"Dialogue: 0,{ass_t(a - T0)},{ass_t(min(b, T1) - T0)},Cap,,0,0,0,,{txt}")
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Lora,62,&H00D2E6EF,&H00D2E6EF,&H00101010,&H90000000,1,0,0,0,100,100,0,0,1,5,2,8,70,70,1320,1
Style: Top,Cinzel,64,&H005CA4C9,&H005CA4C9,&H00101010,&H00000000,1,0,0,0,100,100,2,0,1,5,3,8,40,40,250,1
Style: Sub,Lora,44,&H00D2E6EF,&H00D2E6EF,&H00101010,&H00000000,0,1,0,0,100,100,0,0,1,4,2,8,40,40,345,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
dur = T1 - T0
top = [f"Dialogue: 0,0:00:00.00,{ass_t(dur)},Top,,0,0,0,,ISANDLWANA · 1879",
       f"Dialogue: 0,0:00:00.00,{ass_t(dur)},Sub,,0,0,0,,How the horns closed"]
open("short.ass", "w", encoding="utf-8").write(hdr + "\n".join(top + ev) + "\n")
vf = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.12[bg];"
      "[b]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2-80,ass=short.ass:fontsdir=fonts[v]")
af = f"afade=t=in:d=0.4,afade=t=out:st={dur - 1.5:.2f}:d=1.5"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(T0), "-t", f"{dur:.2f}", "-i", SRC, "-filter_complex", vf, "-map", "[v]",
                "-map", "0:a", "-af", af, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT], check=True)
print("ok", OUT, len(ev), "caption events")
