"""After Closing Ep 1, Block 3 "The Room" (Scene 2), from Joe's package.

Mary Jane's rented room by day, with Ruth in the doorway. R1/R2 are Kling,
R3/R4 Seedance lip-sync. Voices are the clean ElevenLabs lines, laid where the
rendered lips move (measured from each clip's own speech track). R3 is mirrored
so Ruth looks screen-left, back at Mary Jane, who looks screen-right to the door.
"""
import json
import subprocess

# (clip, in, out) in seconds
SHOTS = [
    ("R1", 0, 6),       # The Skill: stitching the sage collar
    ("R2v2", 0, 4.5),   # The Letter & The Suitcase (Ruth V.O.)
    ("R3", 0, 6.5),     # The Friend: Ruth in the doorway
    ("R4", 0, 9.8),     # The Resolve: Mary Jane answers, back to her stitching
]
FLIP = {"R3"}
# (file, shot, seconds into that shot)
LINES = [
    ("audio/ruth_doit.mp3", "R2v2", 1.0),            # V.O. over the letter
    ("audio/ruth_newyork.mp3", "R3", 0.92),          # lips run ~0.6s after the 0.3s reference
    ("audio/mj_theydonthaveme.mp3", "R4", 2.4),      # lips run ~2.1s after the 0.3s reference
]
# (file, shot, seconds into that shot, volume)
FOLEY = [
    ("audio/needle.mp3", "R1", 0.0, 0.5),
    ("audio/needle.mp3", "R4", 8.6, 0.35),           # she goes back to her stitching
]
STREET_VOL = 0.35
OUT = "../AfterClosing_E01_Block3_TheRoom_16x9.mp4"


def main():
    s, t = {}, 0.0
    for name, a, b in SHOTS:
        s[name] = t
        t += b - a
    total = t
    ms = lambda x: int(x * 1000)

    V = "scale=-2:1080:flags=lanczos,crop=1920:1080,setsar=1,fps=24,format=yuv420p"
    g = [f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,{'hflip,' if name in FLIP else ''}{V}[v{i}]"
         for i, (name, a, b) in enumerate(SHOTS)]
    n = len(SHOTS)
    g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
             "eq=contrast=1.04:saturation=0.9,vignette=PI/5,noise=alls=7:allf=t,"
             f"fade=t=in:st=0:d=0.8,fade=t=out:st={total - 1.2:.2f}:d=1.2[vout]")

    k = n
    g.append(f"[{k}:a]atrim=0:{total:.3f},volume={STREET_VOL},afade=t=in:d=0.8,"
             f"afade=t=out:st={total - 1.5:.3f}:d=1.5[street]")
    labels = ["[street]"]
    for j, (f, shot, off) in enumerate(LINES):
        g.append(f"[{k+1+j}:a]volume=1.6,adelay={ms(s[shot] + off)}:all=1[l{j}]")
        labels.append(f"[l{j}]")
    base = k + 1 + len(LINES)
    for j, (f, shot, off, vol) in enumerate(FOLEY):
        dur = min(7.0, total - (s[shot] + off))
        g.append(f"[{base+j}:a]atrim=0:{dur:.3f},volume={vol},afade=t=out:st={dur - 0.6:.3f}:d=0.6,"
                 f"adelay={ms(s[shot] + off)}:all=1[f{j}]")
        labels.append(f"[f{j}]")
    g.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,"
             f"atrim=0:{total:.3f},aresample=48000,aformat=channel_layouts=stereo[mix]")

    ins = []
    for name, _, _ in SHOTS:
        ins += ["-i", f"clips/{name}.mp4"]
    ins += ["-stream_loop", "-1", "-i", "audio/street_day.mp3"]
    for f, _, _ in LINES:
        ins += ["-i", f]
    for f, _, _, _ in FOLEY:
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
