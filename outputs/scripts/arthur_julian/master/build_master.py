"""Build the Arthur & Julian pilot master (Ep 1-7) in one ffmpeg pass.

Run from this folder after phone_fix.py has produced ep6_fixed.mp4 and
ep7_fixed.mp4. Cut points are frame numbers at 24 fps, found by scene-cut
detection on the source clips.
"""
import subprocess

KIT = "../capcut_kit"
FPS = 24

# (file, start_frame, end_frame or None for the whole clip)
SEGMENTS = [
    ("src/ep1.mp4", 0, None),
    ("src/ep2.mp4", 0, 205),            # lobby, up to the cut to the car
    (f"{KIT}/card_1_48_hours_later.mp4", 0, None),
    ("src/ep2.mp4", 205, None),         # Arthur steps out of the car
    ("src/ep3.mp4", 0, None),
    (f"{KIT}/card_2_the_next_day.mp4", 0, None),
    ("src/ep4.mp4", 0, None),
    ("src/ep5.mp4", 0, None),
    ("src/ep6fix.mp4", 0, 232),         # reshot opening, up to the cut to Arthur
    ("ep6_fixed.mp4", 232, None),       # rest of Ep 6, FUNDS FROZEN fixed
    (f"{KIT}/card_3_one_month_later.mp4", 0, None),
    ("ep7_fixed.mp4", 0, None),         # Ep 7, Victor's message fixed
]

# Sub-drop stings: (segment index, seconds into that segment)
STINGS = [
    (0, 19.95),   # Ep 1: Arthur's eyes glow blue for the first time
    (9, 20.2 - 232 / FPS),  # Ep 6: phone flashes FUNDS FROZEN
    (11, 19.8),   # Ep 7: Victor's message lights up the cracked phone
]

MUSIC_VOL = 0.15
STING_VOL = 0.8
OUT = "Arthur_and_Julian_Pilot_Ep1-7_master_9x16.mp4"


def frames(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=nb_read_packets,r_frame_rate", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip().split(",")
    num, den = out[0].split("/")
    return int(out[1]), float(num) / float(den)


def main():
    inputs, vf, af, durs = [], [], [], []
    for i, (path, a, b) in enumerate(SEGMENTS):
        n, fps = frames(path)
        start = a / fps
        end = (b if b is not None else n) / fps
        durs.append(end - start)
        inputs += ["-i", path]
        vf.append(f"[{i}:v]trim={start:.4f}:{end:.4f},setpts=PTS-STARTPTS,fps={FPS},"
                  f"scale=720:1280,setsar=1,format=yuv420p[v{i}]")
        af.append(f"[{i}:a]atrim={start:.4f}:{end:.4f},asetpts=PTS-STARTPTS,"
                  f"aresample=48000,aformat=channel_layouts=stereo[a{i}]")
    total = sum(durs)
    k = len(SEGMENTS)
    inputs += ["-i", f"{KIT}/music_bed_4min.mp3", "-i", f"{KIT}/sting_sub_drop.wav"]
    m, s = k, k + 1

    concat_in = "".join(f"[v{i}][a{i}]" for i in range(k))
    graph = vf + af + [f"{concat_in}concat=n={k}:v=1:a=1[vout][dlg]"]
    graph.append(f"[{m}:a]atrim=0:{total:.3f},afade=t=out:st={total - 3:.3f}:d=3,"
                 f"volume={MUSIC_VOL},aresample=48000,aformat=channel_layouts=stereo[music]")
    starts = [sum(durs[:i]) for i in range(k)]
    sting_labels = []
    graph.append(f"[{s}:a]aresample=48000,aformat=channel_layouts=stereo,volume={STING_VOL},"
                 f"asplit={len(STINGS)}" + "".join(f"[st{j}]" for j in range(len(STINGS))))
    for j, (seg, t) in enumerate(STINGS):
        ms = int((starts[seg] + t) * 1000)
        graph.append(f"[st{j}]adelay={ms}|{ms}[sd{j}]")
        sting_labels.append(f"[sd{j}]")
    graph.append(f"[dlg][music]{''.join(sting_labels)}amix=inputs={2 + len(STINGS)}:normalize=0:duration=first,"
                 f"loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(graph),
           "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", OUT]
    subprocess.run(cmd, check=True)
    print(f"{OUT}: {total:.2f}s")
    for i, (seg, _, _) in enumerate(SEGMENTS):
        print(f"  {starts[i]:7.2f}s  {seg}")
    for seg, t in STINGS:
        print(f"  sting at {starts[seg] + t:.2f}s")


if __name__ == "__main__":
    main()
