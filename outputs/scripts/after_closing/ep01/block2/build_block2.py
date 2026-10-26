"""After Closing Ep 1, Block 2 "The Banter" (follows Block 1), from Joe's map.

Three Seedance lip-synced shots. The sound is rebuilt from the clean voice
files (same timing the clips were synced to): room tone continuous from Block 1,
then the piano comes back smoothly under Shot 3 and carries to the end.
"""
import json
import subprocess

# (clip, in, out) in seconds
SHOTS = [
    ("S1", 0, 6),    # Isaiah turns: "You always listen?"
    ("S2v2", 0, 7.5),  # Mary Jane, still, by the light: "Hard not to. Same mistake, six weeks." (retake)
    ("S3v2", 0, 10),   # locked-off wide, she stays by the piano; "Better?" / "Getting there." (retake)
]
# (file, shot, seconds into that shot): placed where the rendered lips actually move.
# S1 renders ~1.04s late; in S2v2 her lips run 2.8-6.0s, so her line is re-laid
# phrase by phrase onto those moments (mj_line_S2v2_aligned.wav); S3v2 answer +0.5s.
LINES = [
    ("../audio/s01_ir1.mp3", "S1", 2.04),
    ("audio/mj_line_S2v2_aligned.wav", "S2v2", 0.0),
    ("audio/ir_better.mp3", "S3v2", 3.2),
    ("audio/mj_gettingthere.mp3", "S3v2", 5.1),
]
PIANO_SRC = 20.4     # piano_4 position: the same melody Block 1 opens with inside
PIANO_VOL = 0.5

A = "../v2/audio_raw"
OUT = "../AfterClosing_E01_Block2_TheBanter_16x9.mp4"


def main():
    s, t = {}, 0.0
    for name, a, b in SHOTS:
        s[name] = t
        t += b - a
    total = t
    ms = lambda x: int(x * 1000)

    V = "scale=-2:1080:flags=lanczos,crop=1920:1080,setsar=1,fps=24,format=yuv420p"
    g = [f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,{V}[v{i}]" for i, (_, a, b) in enumerate(SHOTS)]
    n = len(SHOTS)
    g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
             "eq=contrast=1.04:saturation=0.9,vignette=PI/5,noise=alls=7:allf=t,"
             f"fade=t=out:st={total - 1.2:.2f}:d=1.2[vout]")

    k = n
    p0 = s["S3v2"]
    g.append(f"[{k}:a]atrim=0:{total:.3f},volume=2[room]")
    g.append(f"[{k+1}:a]atrim={PIANO_SRC}:{PIANO_SRC + total - p0:.3f},asetpts=PTS-STARTPTS,"
             f"volume={PIANO_VOL},afade=t=in:d=1.2,afade=t=out:st={total - p0 - 1.5:.3f}:d=1.5,"
             f"adelay={ms(p0)}:all=1[piano]")
    labels = []
    for j, (f, shot, off) in enumerate(LINES):
        g.append(f"[{k+2+j}:a]volume=1.6,adelay={ms(s[shot] + off)}:all=1[l{j}]")
        labels.append(f"[l{j}]")
    g.append(f"[room][piano]{''.join(labels)}amix=inputs={2 + len(LINES)}:normalize=0:duration=first,"
             f"atrim=0:{total:.3f},aresample=48000,aformat=channel_layouts=stereo[mix]")

    ins = []
    for name, _, _ in SHOTS:
        ins += ["-i", f"clips/{name}.mp4"]
    ins += ["-stream_loop", "-1", "-i", f"{A}/room_4.mp3", "-i", f"{A}/piano_4.mp3"]
    for f, _, _ in LINES:
        ins += ["-i", f]

    meas = subprocess.run(["ffmpeg", "-y", "-v", "info", *ins, "-filter_complex",
                           ";".join(g[n + 1:]) + ";[mix]loudnorm=I=-16:TP=-1.5:LRA=20:print_format=json[o]",
                           "-map", "[o]", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=20:linear=true:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    g[-1] = g[-1].replace("[mix]", f",{ln}[aout]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(g),
                    "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow",
                    "-b:v", "6M", "-maxrate", "8M", "-bufsize", "12M", "-tune", "grain",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT], check=True)
    print(f"{OUT}: {total:.2f}s")
    for name, _, _ in SHOTS:
        print(f"  {s[name]:6.2f}s  {name}")


if __name__ == "__main__":
    main()
