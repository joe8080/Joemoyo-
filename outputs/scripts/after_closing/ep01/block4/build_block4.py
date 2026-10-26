"""After Closing Ep 1, Block 4 "The Ambition" (Scene 3), from Joe's package.

Smash cut from Block 3's daylight room into the ballroom at night. One soft
piano note lands on the cut and rings out under Shot 1; Isaiah speaks in Shot
2; a full 1.5s of quiet after his line before Mary Jane answers in Shot 3.
C1 is Kling, C2v2/C3v2 Seedance lip-sync; voices are the clean ElevenLabs
lines laid where the rendered lips move (measured from each clip's own track).
"""
import json
import subprocess

# (clip, in, out) in seconds
SHOTS = [
    ("C1", 0, 6),         # The Reveal: she holds up the sage collar, the note rings
    ("C2v2", 1.8, 9.0),   # His Respect (set from measurement)
    ("C3v2", 0.0, 9.0),   # Her Challenge (set from measurement)
]
# (file, shot, seconds into that shot as cut)
LINES = [
    ("audio/ir_seriouswork.mp3", "C2v2", 0.0),
    ("audio/mj_melody.mp3", "C3v2", 0.0),
]
NOTE_AT = 0.05      # the single key lands right on the cut
NOTE_VOL = 1.6
ROOM_VOL = 2.0
OUT = "../AfterClosing_E01_Block4_TheAmbition_16x9.mp4"
A = "../v2/audio_raw"


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
    # hard cut in (smash cut from Block 3), gentle fade out at the end
    g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
             "eq=contrast=1.04:saturation=0.9,vignette=PI/5,noise=alls=7:allf=t,"
             f"fade=t=out:st={total - 1.0:.2f}:d=1.0[vout]")

    k = n
    g.append(f"[{k}:a]atrim=0:{total:.3f},volume={ROOM_VOL},afade=t=out:st={total - 1.2:.3f}:d=1.2[room]")
    # the note: first 2.6s of the take (before a stray knock), with a long soft room tail
    g.append(f"[{k+1}:a]atrim=0:2.6,asetpts=PTS-STARTPTS,volume={NOTE_VOL},apad=pad_dur=4,"
             "aecho=0.8:0.7:120|260|450:0.35|0.22|0.12,afade=t=out:st=3.5:d=2.5,"
             f"adelay={ms(NOTE_AT)}:all=1[note]")
    labels = ["[room]", "[note]"]
    for j, (f, shot, off) in enumerate(LINES):
        g.append(f"[{k+2+j}:a]volume=1.6,adelay={ms(s[shot] + off)}:all=1[l{j}]")
        labels.append(f"[l{j}]")
    g.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,"
             f"atrim=0:{total:.3f},aresample=48000,aformat=channel_layouts=stereo[mix]")

    ins = []
    for name, _, _ in SHOTS:
        ins += ["-i", f"clips/{name}.mp4"]
    ins += ["-stream_loop", "-1", "-i", f"{A}/room_4.mp3", "-i", "audio/piano_note.mp3"]
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
