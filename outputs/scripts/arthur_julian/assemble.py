"""Assemble an episode: normalise scene clips, find where each line starts, burn captions, add music, export.

Usage: python3 assemble.py <episode_folder>
The folder holds scene1..4.mp4, the matching vo_s*.mp3 files and music_tension_bed.mp3.
"""
import subprocess, json, os, sys
import numpy as np

D = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "ep1")
W, H, FPS = 720, 1280, 30

LINES = [
    ("Do you have any idea how much these Italian loafers cost... old man?", "vo_s1_julian.mp3"),
    ("If you drop one more pallet on my shift, you're out on the street. You're invisible here.", "vo_s2_julian.mp3"),
    ("Every empire has a foundation, Julian. And every foundation... can be pulled out from under you.", "vo_s3_arthur.mp3"),
    ("Spare me the philosophy. Pack your box. You're fired.", "vo_s4_julian.mp3"),
]


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def dur(p):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", p])
    return float(json.loads(out)["format"]["duration"])


def pcm(p, sr=8000):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"])
    return np.frombuffer(raw, dtype=np.float32), sr


def envelope(x, sr, hop=0.01):
    n = int(sr * hop)
    x = x[: len(x) // n * n].reshape(-1, n)
    return np.sqrt((x ** 2).mean(axis=1))


def speech_offset(clip, vo):
    """Where the voice line starts inside the clip, by cross-correlating loudness envelopes."""
    a, sr = pcm(clip)
    b, _ = pcm(vo)
    ea, eb = envelope(a, sr), envelope(b, sr)
    ea = (ea - ea.mean()) / (ea.std() + 1e-9)
    eb = (eb - eb.mean()) / (eb.std() + 1e-9)
    if len(ea) <= len(eb):
        return 0.0
    corr = np.correlate(ea, eb, mode="valid")
    return float(np.argmax(corr)) * 0.01


def chunks(text, n=3):
    """Up to n words per caption, never spanning a sentence or pause boundary."""
    out, cur = [], []
    for w in text.replace("...", "…").split():
        cur.append(w)
        if len(cur) == n or w[-1] in ".?!,…":
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def main():
    clips = [os.path.join(D, f"scene{i}.mp4") for i in range(1, 5)]
    norm, starts, t = [], [], 0.0
    events = []
    for i, (clip, (text, vo)) in enumerate(zip(clips, LINES), 1):
        out = os.path.join(D, f"_norm{i}.mp4")
        run(["ffmpeg", "-y", "-i", clip, "-vf",
             f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1",
             "-af", "aresample=48000", "-ac", "2", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-c:a", "aac", "-b:a", "192k", out])
        d = dur(out)
        off = speech_offset(out, os.path.join(D, vo))
        vd = dur(os.path.join(D, vo))
        # Captions: chunks spread over the spoken words, weighted by character count
        cs = chunks(text)
        total = sum(len(c) for c in cs)
        cur = t + off
        for c in cs:
            span = vd * len(c) / total
            events.append((cur, min(cur + span, t + d), c.upper()))
            cur += span
        print(f"scene {i}: clip {d:.2f}s, line starts at {off:.2f}s, line {vd:.2f}s")
        norm.append(out)
        starts.append(t)
        t += d

    ass = os.path.join(D, "_captions.ass")
    with open(ass, "w") as f:
        f.write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display Black,58,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,400,1
Style: Tag,Inter Display Black,34,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,3,1,8,40,40,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ts(0)},{ts(t)},Tag,,0,0,0,,PART 1
""")
        for s, e, c in events:
            f.write(f"Dialogue: 1,{ts(s)},{ts(e)},Cap,,0,0,0,,{{\\fad(60,0)}}{c}\n")

    lst = os.path.join(D, "_list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in norm)
    joined = os.path.join(D, "_joined.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

    music = os.path.join(D, "music_tension_bed.mp3")
    final = os.path.join(D, "Ep1_The_Setup_9x16.mp4")
    fade_at = max(t - 0.4, 0)
    fc = (
        f"[0:v]ass={ass}[v];"
        f"[0:a]volume=1.0,asplit=2[dlg][key];"
        f"[1:a]atrim=0:{t:.2f},volume=0.35,afade=t=out:st={fade_at:.2f}:d=0.4[mus];"
        f"[mus][key]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300[duck];"
        f"[dlg][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    )
    run(["ffmpeg", "-y", "-i", joined, "-i", music, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", final])
    for tmp in norm + [lst, joined]:
        os.remove(tmp)
    print(f"final: {final} ({dur(final):.2f}s)")


if __name__ == "__main__":
    main()
