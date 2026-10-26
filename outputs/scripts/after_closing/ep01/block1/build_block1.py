"""After Closing Ep 1, Block 1 "The Empty Room" (0:00-1:00), cut to Joe's director's map.

Run from this folder after cloth_foley.py has made audio/cloth_*.wav. Street,
doors, ballroom and macro clips are reused from ../v2/clips (symlinked here);
B05-B10 are new Kling 2.6 renders. Two-pass loudnorm with linear gain so the
room tone after the piano stops stays quiet.

Joe's note: no wrong chord and no hands on the keys. The piano ends gently on a
soft phrase while we hold on Mary Jane, then we cut back to Isaiah rubbing his eyes.
"""
import json
import subprocess

# (clip, in, out) in seconds; hard cuts in this order
SHOTS = [
    ("V01", 0, 5),     # V-01 street, cab
    ("V02", 0, 3),     # V-02 doors push-in (0:08)
    ("V03", 0, 5),     # V-03 empty ballroom
    ("V04new", 0, 5),  # V-04 macro: cloth across the table (retake: her bare forearm, empty crystal glass)
    ("B05", 0, 7),     # V-05 MJ wiping, exhausted (0:25)
    ("B06", 0, 10),    # V-06 Isaiah, eyes closed
    ("B07", 0, 10),    # V-07 MJ captivated, held (0:45); the piano dies away on her; mirrored so she looks screen-left
    ("B09", 0, 6),     # V-09 Isaiah rubs his eyes
    ("B10", 0, 9),     # MJ empathetic: "You always stop there."
]
PIANO_STOP = 41.6    # film time the last soft note starts to die away (on Mary Jane)
PIANO_TAIL = 1.95    # gentle fade on that last phrase, done before the next loud note (58.04s in piano_4)
LINE_IN_B10 = 0.8
FLIP = {"B07"}     # Joe's map: Mary Jane looks screen-left, toward the piano
PIANO_IN = 6.0       # J-cut: piano starts under the doors at 0:06
PIANO_OFFSET = 14.4  # piano_4 position at film time 0: its phrase ending (55.9s) lands at 0:41.5

A = "../v2/audio_raw"
OUT = "../AfterClosing_E01_Block1_TheEmptyRoom_16x9.mp4"


def starts():
    t, s = 0.0, {}
    for name, a, b in SHOTS:
        s[name] = t
        t += b - a
    return s, t


def graph(total, s):
    stop = PIANO_STOP + PIANO_TAIL
    line = s["B10"] + LINE_IN_B10
    inside = s["V03"]
    p0, p1 = PIANO_IN + PIANO_OFFSET, stop + PIANO_OFFSET   # piano_4 source times
    muff = inside - PIANO_IN

    V = "scale=-2:1080:flags=lanczos,crop=1920:1080,setsar=1,fps=24,format=yuv420p"
    g = [f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,{'hflip,' if name in FLIP else ''}{V}[v{i}]"
         for i, (name, a, b) in enumerate(SHOTS)]
    n = len(SHOTS)
    g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
             "eq=contrast=1.04:saturation=0.9,vignette=PI/5,noise=alls=7:allf=t,"
             f"fade=t=in:st=0:d=1,fade=t=out:st={total - 1.5:.2f}:d=1.5[vout]")

    k = n
    ms = lambda t: int(t * 1000)
    g += [
        # 0:00-0:08 the city: rain loud, sax soft, both gone once we're inside
        f"[{k}:a]volume=0.55,afade=t=in:d=0.8,afade=t=out:st={inside - 0.5}:d=1.5,atrim=0:{inside + 1}[street]",
        f"[{k+1}:a]volume=0.25,afade=t=in:d=1.5,afade=t=out:st={PIANO_IN}:d={inside + 1 - PIANO_IN},atrim=0:{inside + 1}[sax]",
        # piano: muffled J-cut under the doors, clear inside, gently ends on Mary Jane
        f"[{k+2}:a]atrim={p0}:{p1:.3f},asetpts=PTS-STARTPTS,asplit=2[p1][p2]",
        f"[p1]atrim=0:{muff},lowpass=f=450,lowpass=f=450,volume=0.7,afade=t=in:d=2,"
        f"afade=t=out:st={muff - 0.15}:d=0.15,adelay={ms(PIANO_IN)}:all=1[pmuff]",
        f"[p2]atrim={muff}:{p1 - p0:.3f},asetpts=PTS-STARTPTS,volume=0.85,afade=t=in:d=0.15,"
        f"afade=t=out:st={PIANO_STOP - inside:.3f}:d={PIANO_TAIL}:curve=qsin,adelay={ms(inside)}:all=1[pclean]",
        # room tone from the cut inside to the end
        f"[{k+3}:a]atrim=0:{total - inside:.3f},volume=2,afade=t=in:d=1.5,"
        f"afade=t=out:st={total - inside - 2:.3f}:d=2,adelay={ms(inside)}:all=1[room]",
        # cloth foley (ElevenLabs take), kept soft under the piano per Joe
        f"[{k+4}:a]atrim=0:5,volume=1.4,afade=t=out:st=4.6:d=0.4,adelay={ms(s['V04new'])}:all=1[cloth1]",
        f"[{k+5}:a]atrim=5:9,asetpts=PTS-STARTPTS,volume=1.0,afade=t=out:st=3.4:d=0.6,adelay={ms(s['B05'])}:all=1[cloth2]",
        # "You always stop there." with a little of the room on it
        f"[{k+6}:a]volume=4,apad=pad_dur=2,aecho=0.8:0.6:90|160:0.22|0.12,adelay={ms(line)}:all=1[line]",
        "[street][sax][pmuff][pclean][room][cloth1][cloth2][line]"
        f"amix=inputs=8:normalize=0:duration=longest,atrim=0:{total:.3f},"
        "aresample=48000,aformat=channel_layouts=stereo[mix]",
    ]
    return g, dict(piano_fades=PIANO_STOP, piano_silent=stop, line=line)


def inputs():
    args = []
    for name, _, _ in SHOTS:
        args += ["-i", f"clips/{name}.mp4"]
    for f in ["street_1", "sax_1", "piano_4"]:
        args += ["-i", f"{A}/{f}.mp3"]
    args += ["-stream_loop", "-1", "-i", f"{A}/room_4.mp3"]
    args += ["-i", "audio/cloth_real.mp3", "-i", "audio/cloth_real.mp3", "-i", "../audio/s01_mj1.mp3"]
    return args


def main():
    s, total = starts()
    g, marks = graph(total, s)
    ins = inputs()
    meas = subprocess.run(["ffmpeg", "-y", "-v", "info", *ins, "-filter_complex",
                           ";".join(g[len(SHOTS) + 1:]) + ";[mix]loudnorm=I=-16:TP=-1.5:LRA=20:print_format=json[o]",
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
    for k, v in marks.items():
        print(f"  {k} at {v:.2f}s")


if __name__ == "__main__":
    main()
