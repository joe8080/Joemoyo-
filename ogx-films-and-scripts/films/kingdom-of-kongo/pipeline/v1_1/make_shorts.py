"""Kongo v1.4: three 9:16 Shorts cut from the finished film.
Needs full.mp4 (the v1.4 1080p master) in the working directory.
Word timings come from faster-whisper; caption text comes from the script (tts.json lines below),
aligned to those timings, so names are spelt correctly.
Layout: blurred fill, 16:9 picture in the middle, title banner on top, captions below, end line.
Outputs short1.mp4, short2.mp4, short3.mp4 and preview.jpg."""
import difflib, json, re, subprocess

SRC = "full.mp4"
SHORTS = [
    dict(out="short1.mp4", top="KONGO · 1526", sub="A king's warning to Portugal", pieces=[
        ("our kingdom he writes", "is being emptied",
         '"Our kingdom," he writes, "is being lost." Merchants are taking "our people, sons of the land, sons of our nobles and vassals, and our relatives." And the land, he says, is being emptied.'),
        ("so why would a king", "away from his court",
         "So why would a king in Central Africa send that warning to Portugal? His letters give us part of the answer. Afonso wasn't asking Portugal to end slavery. Slavery existed in Kongo, and Afonso himself sent war captives to Portuguese ships. What his letters complain about is free people being kidnapped and sold, by people he couldn't stop, in a trade that was pulling power away from his court."),
    ]),
    dict(out="short2.mp4", top="KONGO · 1526", sub="The king's law on who could be sold", pieces=[
        ("so he made a law", "officials had checked them",
         "So he made a law. Any white man buying people in Kongo had to show them first to three officials of the royal court: Dom Pedro Manipunzo, Dom Manuel Manissaba, and Gonçalo Pires. The three would decide whether each person was free or lawfully enslaved. If they passed, they could be shipped. If not, the buyer lost them. So in July, he had asked for no slave trade at all. By October, he was setting rules that let some people be shipped, but only after his own officials had checked them."),
    ]),
    dict(out="short3.mp4", top="KONGO · 1529", sub="Portugal's answer", pieces=[
        ("so did portugal listen", "church was part of it",
         "So did Portugal listen? It did reply. In a letter written towards the end of 1529, King João said he'd been told Kongo was so full of people that it seemed not a single slave had ever left it. He suggested a fixed place in the market, where two of Afonso's men would check who was being sold. Then he added this. He'd agree, he said, to no slave trade at all, and send one small ship a year with wine and flour. But that wouldn't do Kongo any honour. Better, he wrote, that ten thousand slaves left Kongo every year, with ten thousand copper bracelets and as many ivory tusks. The same letter told the Portuguese priests in Kongo how to have slaves bought for their own upkeep. So the trade went on, and the Church was part of it."),
    ]),
]

norm = lambda t: re.sub(r"[^a-z0-9]", "", t.lower().replace("’", "'"))


def transcribe():
    from faster_whisper import WhisperModel
    m = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)
    segs, _ = m.transcribe(SRC, word_timestamps=True, beam_size=1, language="en")
    W = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    json.dump(W, open("words.json", "w"))
    return W


def find(NW, phrase, after=0):
    toks = [norm(x) for x in phrase.split()]
    for i in range(after, len(NW) - len(toks) + 1):
        if NW[i:i + len(toks)] == toks:
            return i
    raise SystemExit("phrase not found: " + phrase)


def align(script, W, i0, i1):
    """Give each script word a (start, end) from the whisper words W[i0:i1+1]."""
    st = script.split()
    a = [norm(x) for x in st]
    b = [norm(w[0]) for w in W[i0:i1 + 1]]
    tim = [None] * len(st)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            w = W[i0 + blk.b + k]
            tim[blk.a + k] = (w[1], w[2])
    tim[0] = tim[0] or (W[i0][1], W[i0][2])
    tim[-1] = tim[-1] or (W[i1][1], W[i1][2])
    k = 0
    while k < len(st):  # fill gaps by spreading evenly between known neighbours
        if tim[k] is None:
            j = k
            while tim[j] is None:
                j += 1
            t0, t1 = tim[k - 1][1], tim[j][0]
            n = j - k
            for q in range(n):
                tim[k + q] = (t0 + (t1 - t0) * q / n, t0 + (t1 - t0) * (q + 1) / n)
            k = j
        k += 1
    return list(zip(st, tim))


def ass_t(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def esc(t):
    return t.replace("\\", "").replace("{", "(").replace("}", ")")


HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat,66,&H00F0F5F8,&H00F0F5F8,&H00101010,&H90000000,1,0,0,0,100,100,0,0,1,5,2,8,70,70,1290,1
Style: Top,DejaVu Serif,72,&H005CB4D9,&H005CB4D9,&H00101010,&H00000000,1,0,0,0,100,100,3,0,1,5,3,8,40,40,250,1
Style: Sub,DejaVu Serif,44,&H00E6EEF2,&H00E6EEF2,&H00101010,&H00000000,0,1,0,0,100,100,0,0,1,4,2,8,40,40,355,1
Style: End,Montserrat,48,&H005CB4D9,&H005CB4D9,&H00101010,&H00000000,1,0,0,0,100,100,1,0,1,4,2,8,40,40,1640,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

VF916 = ("split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
         "gblur=sigma=40,eq=brightness=-0.14[bg];[b]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2-80,"
         "format=yuv420p")


def run(*a):
    subprocess.run(list(a), check=True)


def build(sh, W, NW):
    parts, events, t_off = [], [], 0.0
    for n, (p0, p1, text) in enumerate(sh["pieces"]):
        i0 = find(NW, p0)
        i1 = find(NW, p1, i0) + len(p1.split()) - 1
        last = n == len(sh["pieces"]) - 1
        s = max(0.0, W[i0][1] - 0.35)
        e = W[i1][2] + (1.2 if last else 0.45)
        words = align(text, W, i0, i1)
        cue, c0 = [], None
        for k, (tok, (a, b)) in enumerate(words):
            if not cue:
                c0 = a
            cue.append(tok)
            brk = (len(cue) >= 4 or len(" ".join(cue)) >= 24 or re.search(r"[.?!,:;]\"?$", tok)
                   or k == len(words) - 1)
            if brk:
                nxt = words[k + 1][1][0] if k + 1 < len(words) else b + 0.4
                events.append(f"Dialogue: 0,{ass_t(c0 - s + t_off)},{ass_t(min(nxt, b + 0.6) - s + t_off)},Cap,,0,0,0,,{esc(' '.join(cue))}")
                cue = []
        pf = f"piece{n}.mp4"
        d = e - s
        run("ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", SRC,
            "-filter_complex", f"[0:v]{VF916},fade=t=in:d=0.25,fade=t=out:st={d - 0.25:.3f}:d=0.25[v];"
            f"[0:a]afade=t=in:d=0.15,afade=t=out:st={d - 0.25:.3f}:d=0.25[a]",
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast", "-crf", "16",
            "-c:a", "pcm_s16le", "-ar", "48000", pf.replace(".mp4", ".mov"))
        parts.append(pf.replace(".mp4", ".mov"))
        t_off += d
    dur = t_off
    top = [f"Dialogue: 0,0:00:00.00,{ass_t(dur)},Top,,0,0,0,,{sh['top']}",
           f"Dialogue: 0,0:00:00.00,{ass_t(dur)},Sub,,0,0,0,,{sh['sub']}",
           f"Dialogue: 0,{ass_t(dur - 3.0)},{ass_t(dur)},End,,0,0,0,,FULL FILM ON THE CHANNEL"]
    open("short.ass", "w", encoding="utf-8").write(HDR + "\n".join(top + events) + "\n")
    open("concat.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt",
        "-vf", "ass=short.ass", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aformat=sample_rates=48000:channel_layouts=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", sh["out"])
    run("ffmpeg", "-v", "error", "-y", "-ss", f"{dur * 0.4:.2f}", "-i", sh["out"], "-frames:v", "1",
        "-vf", "scale=360:-2", sh["out"].replace(".mp4", ".jpg"))
    print(sh["out"], f"{dur:.1f}s", len(events), "cues")


if __name__ == "__main__":
    W = transcribe()
    NW = [norm(w[0]) for w in W]
    for sh in SHORTS:
        build(sh, W, NW)
    run("ffmpeg", "-v", "error", "-y", "-i", "short1.jpg", "-i", "short2.jpg", "-i", "short3.jpg",
        "-filter_complex", "hstack=inputs=3", "preview.jpg")
    print("SHORTS DONE")
