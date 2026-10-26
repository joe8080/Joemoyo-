"""After Closing Ep 1, Scene 01 v2 "The City and the Room": cut, sound and grade.

Run from this folder. Clips are Kling 2.6 renders (clips/, git-ignored); audio
takes are in audio_raw/ and the V.O. lines in ../audio/. Two-pass loudnorm with
linear gain so the silence before "You always stop there." stays silent.
"""
import json
import subprocess

FPS = 24

# (clip, in, out) in seconds; hard cuts in this order
SHOTS = [
    ("V01", 0, 10),    # street, cab, neon; title card
    ("V02", 0, 8),     # push-in to the doors; muffled piano begins
    ("V03", 0, 7),     # interior wide, chandeliers off
    ("V03b", 0, 6),    # macro glass + ashtray, cloth
    ("V04", 1, 10),    # MJ and the playbill
    ("V05", 0, 9),     # wide: Isaiah plays for himself
    ("V06", 0, 8),     # MJ stops, listens
    ("V07", 0, 8),     # hands, mended cuff; music swells
    ("V08", 0, 8),     # OTS: he finds her
    ("V08b", 0, 6),    # her knowing smile
    ("V09", 0, 4.5),   # the wrong chord
    ("V10", 0, 5),     # hand over his face
    ("V10b", 0, 6),    # she walks to the stage
    ("V11", 0, 9),     # tray down, chair; 2s silence; "You always stop there."
    ("V12", 0, 9),     # elbow on the piano; "You always listen?"
    ("V12b", 0, 7.5),  # her laugh; "Hard not to. Same mistake, six weeks."
]
CHORD_IN_V09 = 1.95    # his hands hit the keys (frame-checked)
TRAY_END_IN_V11 = 4.5  # last tray/chair sound in tray_2
SILENCE = 2.0          # Joe: two full seconds before the first line

A = "audio_raw"
OUT = "../AfterClosing_E01_S01_TheCityAndTheRoom_16x9.mp4"


def starts():
    t, s = 0.0, {}
    for name, a, b in SHOTS:
        s[name] = t
        t += b - a
    return s, t


def graph(total, s):
    chord = s["V09"] + CHORD_IN_V09
    line1 = s["V11"] + TRAY_END_IN_V11 + SILENCE
    line2 = s["V12"] + 2.0
    line3 = s["V12b"] + 0.6
    pno_len = chord - s["V02"]   # piano runs from the doors to the chord, then dies
    muff = s["V03"] - s["V02"]   # heard through the glass until we cut inside

    V = "scale=-2:1080:flags=lanczos,crop=1920:1080,setsar=1,fps=24,format=yuv420p"
    g = []
    for i, (name, a, b) in enumerate(SHOTS):
        g.append(f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,{V}[v{i}]")
    n = len(SHOTS)
    title = ("drawtext=fontfile=/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf:"
             "fontcolor=white:fontsize={fs}:x=120:y=h-{y}:text='{t}':"
             "alpha='if(lt(t,2.5),0,if(lt(t,3.5),t-2.5,if(lt(t,7.5),1,if(lt(t,8.5),8.5-t,0))))'")
    g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,"
             + title.format(fs=58, y=210, t="CHICAGO") + ","
             + title.format(fs=40, y=140, t="AUTUMN, 1962") + ","
             "eq=contrast=1.04:saturation=0.9,vignette=PI/5,noise=alls=7:allf=t,"
             f"fade=t=in:st=0:d=1.2,fade=t=out:st={total - 1.5:.2f}:d=1.5[vout]")

    k = n  # first audio input index
    ms = lambda t: int(t * 1000)
    g += [
        f"[{k}:a]volume=0.55,afade=t=in:d=1.5,afade=t=out:st=12:d=6,atrim=0:18[street]",
        f"[{k+1}:a]volume=0.4,afade=t=in:d=2,afade=t=out:st=10:d=6,atrim=0:16[sax]",
        f"[{k+2}:a]atrim=0:{pno_len:.3f},asplit=2[p1][p2]",
        f"[p1]atrim=0:{muff},lowpass=f=450,lowpass=f=450,volume=0.6,"
        f"afade=t=in:d=3,afade=t=out:st={muff - 0.15}:d=0.15,adelay={ms(s['V02'])}:all=1[pmuff]",
        f"[p2]atrim={muff}:{pno_len:.3f},asetpts=PTS-STARTPTS,volume=0.85,"
        f"afade=t=in:d=0.15,afade=t=out:st={pno_len - muff - 0.01:.3f}:d=0.01,"
        f"adelay={ms(s['V03'])}:all=1[pclean]",
        f"[{k+3}:a]volume=0.95,adelay={ms(chord)}:all=1[chord]",
        f"[{k+4}:a]atrim=0:{total - s['V03']:.3f},volume=2,afade=t=in:d=0.6,"
        f"afade=t=out:st={total - s['V03'] - 2:.3f}:d=2,adelay={ms(s['V03'])}:all=1[room]",
        f"[{k+5}:a]atrim=0:6,volume=1.6,afade=t=out:st=5.4:d=0.6,adelay={ms(s['V10b'])}:all=1[steps]",
        f"[{k+6}:a]atrim=0:{TRAY_END_IN_V11 + 0.3},volume=0.8,adelay={ms(s['V11'])}:all=1[tray]",
        f"[{k+7}:a]volume=1.6,adelay={ms(line1)}:all=1[l1]",
        f"[{k+8}:a]volume=1.6,adelay={ms(line2)}:all=1[l2]",
        f"[{k+9}:a]volume=1.6,adelay={ms(line3)}:all=1[l3]",
        "[street][sax][pmuff][pclean][chord][room][steps][tray][l1][l2][l3]"
        f"amix=inputs=11:normalize=0:duration=longest,atrim=0:{total:.3f},"
        "aresample=48000,aformat=channel_layouts=stereo[mix]",
    ]
    marks = dict(chord=chord, line1=line1, line2=line2, line3=line3)
    return g, marks


def inputs():
    args = []
    for name, _, _ in SHOTS:
        args += ["-i", f"clips/{name}.mp4"]
    for f in ["street_1", "sax_1", "piano_4", "chord_3"]:
        args += ["-i", f"{A}/{f}.mp3"]
    args += ["-stream_loop", "-1", "-i", f"{A}/room_4.mp3"]
    for f in ["steps_4", "tray_2"]:
        args += ["-i", f"{A}/{f}.mp3"]
    for f in ["s01_mj1", "s01_ir1", "s01_mj2"]:
        args += ["-i", f"../audio/{f}.mp3"]
    return args


def main():
    s, total = starts()
    g, marks = graph(total, s)
    base = ["ffmpeg", "-y", "-v", "error", *inputs()]

    # Pass 1: measure the mix.
    meas = subprocess.run([*base[:2], "-v", "info", *base[4:], "-filter_complex", ";".join(g[len(SHOTS) + 1:])
                                  + ";[mix]loudnorm=I=-16:TP=-1.5:LRA=20:print_format=json[o]",
                                  "-map", "[o]", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=20:linear=true:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}")

    # Pass 2: render.
    g[-1] = g[-1].replace("[mix]", f",{ln}[aout]")
    subprocess.run(base + ["-filter_complex", ";".join(g), "-map", "[vout]", "-map", "[aout]",
                           "-c:v", "libx264", "-preset", "slow", "-b:v", "5.5M", "-maxrate", "7M",
                           "-bufsize", "11M", "-tune", "grain", "-c:a", "aac", "-b:a", "192k",
                           "-ar", "48000", "-movflags", "+faststart", OUT], check=True)
    print(f"{OUT}: {total:.2f}s")
    for name, _, _ in SHOTS:
        print(f"  {s[name]:7.2f}s  {name}")
    for k, v in marks.items():
        print(f"  {k} at {v:.2f}s")


if __name__ == "__main__":
    main()
