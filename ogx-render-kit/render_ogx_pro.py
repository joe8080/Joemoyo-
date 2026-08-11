#!/usr/bin/env python3
"""
OGX PRO render — broadcast-standard Ken Burns build for one slug.

Upgrades render_ogx.py to the ogx-motion-sections spec:
  - fast pacing: each still becomes several 6-15s shots with A-to-B multi-move framings
  - one unified cinematic grade on every shot (kills the "AI slideshow" look)
  - narration-synced broadcast lower-third chyrons (from broadcast lower-third PNGs)
  - a 58Hz + pink-noise sound-design sting under each chyron entry
Falls back gracefully: no lowerthirds/ folder -> clean graded film with no chyrons.

Run where the batch + audio live (ffmpeg/ffprobe on PATH, Python 3):
    python render_ogx_pro.py 23_Kingdom_of_Meroe

Place broadcast lower-thirds (transparent PNG 1920x1080, bottom-left chyron) in:
    02_images_inbox/<slug>/lowerthirds/*.png
with an optional lowerthirds/cards.json = [{"file":"lt1.png","at":0.06,"dur":7}, ...]
(`at` = fraction 0-1 of audio duration, or absolute seconds if >1).

Output: 03_finished_packs/<slug>/FINAL_PRO.mp4
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

W, H, FPS = 1920, 1080, 30
MIN_SCENES = 15
AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac"}
SHOT_MIN, SHOT_MAX, SHOT_TARGET = 7.0, 14.0, 12.0
GRADE = ("eq=contrast=1.07:saturation=0.90:gamma=0.985,"
         "colorbalance=rs=0.015:bs=-0.025:rm=0.012:bm=-0.018,"
         "vignette=angle=PI/4.6,noise=alls=3:allf=t")
# A-to-B framings: (from z,x,y, to z,x,y) in 0..1 focal space
FRAMINGS = [(1.0,0.5,0.55,1.22,0.5,0.45),(1.32,0.35,0.35,1.08,0.5,0.5),
            (1.42,0.55,0.40,1.15,0.42,0.5),(1.10,0.40,0.50,1.30,0.60,0.5),
            (1.28,0.50,0.35,1.05,0.45,0.55),(1.35,0.40,0.45,1.12,0.55,0.42)]

def run(cmd): subprocess.run(cmd, check=True)
def probe(path):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    return float(out.stdout.strip())

def find_audio(d):
    c=sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS)
    if not c: sys.exit(f"ERROR: no audio in {d}")
    return c[0]
def find_scenes(d):
    imgs=sorted(p for p in d.iterdir() if p.suffix.lower()==".png" and p.name[:2].isdigit())
    if len(imgs)<MIN_SCENES: sys.exit(f"ERROR: only {len(imgs)} numbered scene PNGs in {d} (need >= {MIN_SCENES})")
    return imgs

def kb_filter(fz,fx,fy,tz,tx,ty,frames):
    D=max(frames-1,1)
    z=f"{fz}+({tz}-{fz})*on/{D}"
    x=f"(iw-iw/zoom)*({fx}+({tx}-{fx})*on/{D})"
    y=f"(ih-ih/zoom)*({fy}+({ty}-{fy})*on/{D})"
    return (f"scale=2560:-2,zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},{GRADE}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("--root",default=os.environ.get("OGX_BATCH_ROOT"))
    a=ap.parse_args()
    root=Path(a.root).resolve() if a.root else Path(__file__).resolve().parent
    slug=a.slug
    img_dir=root/"02_images_inbox"/slug; aud_dir=root/"01_audio_inbox"/slug
    out_dir=root/"03_finished_packs"/slug; out_dir.mkdir(parents=True,exist_ok=True)
    work=out_dir/"FINAL_PRO.work"; work.mkdir(exist_ok=True)
    final=out_dir/"FINAL_PRO.mp4"
    audio=find_audio(aud_dir); images=find_scenes(img_dir); dur=probe(audio)

    total_shots=max(len(images), round(dur/SHOT_TARGET))
    per=max(1, round(total_shots/len(images)))
    seq=[]
    for img in images:
        for _ in range(per): seq.append(img)
    shot_len=dur/len(seq)
    shot_len=min(max(shot_len,SHOT_MIN),SHOT_MAX)
    # rebuild seq length so shots*shot_len covers dur
    nshots=max(len(images), round(dur/shot_len))
    seq=[images[i%len(images)] for i in range(nshots)]
    shot_len=round(dur/nshots,3)
    print(f"{slug}: audio {dur:.1f}s · {len(images)} stills · {nshots} shots @ {shot_len:.1f}s (grade ON)")

    chunks=[]
    for i,img in enumerate(seq):
        ts=work/f"shot_{i:03d}.ts"; chunks.append(ts)
        if ts.exists() and ts.stat().st_size>0: continue
        fz,fx,fy,tz,tx,ty=FRAMINGS[i%len(FRAMINGS)]
        frames=int(round(shot_len*FPS))
        vf=kb_filter(fz,fx,fy,tz,tx,ty,frames)
        tmp=work/f"shot_{i:03d}.tmp.ts"
        print(f"  [{i+1}/{nshots}] {img.name}")
        run(["ffmpeg","-y","-loop","1","-i",str(img),"-t",f"{shot_len:.3f}","-vf",vf,
             "-c:v","libx264","-preset","veryfast","-crf","23","-maxrate","6000k","-bufsize","12000k",
             "-pix_fmt","yuv420p","-r",str(FPS),"-f","mpegts","-bsf:v","h264_mp4toannexb",str(tmp)])
        tmp.rename(ts)

    print("Concatenating...")
    lst=work/"list.txt"; lst.write_text("".join(f"file '{c.resolve().as_posix()}'\n" for c in chunks))
    silent=work/"silent.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(silent)])
    vidlen=probe(silent)

    # lower-third chyrons + sound stings (optional)
    lt_dir=img_dir/"lowerthirds"
    lts=sorted(lt_dir.glob("*.png")) if lt_dir.is_dir() else []
    base=silent
    if lts:
        cfg=[]
        cj=lt_dir/"cards.json"
        if cj.exists(): cfg={c.get("file"):c for c in json.loads(cj.read_text())}
        else: cfg={}
        CD=7.0
        specs=[]
        for i,p in enumerate(lts):
            c=cfg.get(p.name,{}); at=c.get("at",(i+1)/(len(lts)+1))
            t=at*dur if at<=1 else at; specs.append((p,float(t),float(c.get("dur",CD))))
        # sting
        sting=work/"sting.wav"
        run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=58:duration=0.9",
             "-f","lavfi","-i","anoisesrc=d=0.9:color=pink:amplitude=0.5",
             "-filter_complex","[0:a]afade=t=out:st=0.15:d=0.75[s];[1:a]highpass=f=200,lowpass=f=2200,afade=t=out:st=0:d=0.6[n];[s][n]amix=inputs=2:weights=1 0.5,volume=0.16[a]",
             "-map","[a]",str(sting)])
        inputs=["-i",str(silent),"-i",str(audio)]
        for p,_,d in specs: inputs+=["-loop","1","-t",str(d),"-i",str(p)]
        inputs+=["-i",str(sting)]; sidx=2+len(specs)
        fc=[]; prev="0:v"
        for i,(p,t,d) in enumerate(specs):
            fc.append(f"[{i+2}:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1,fade=t=out:st={d-0.6:.2f}:d=0.55:alpha=1,setpts=PTS-STARTPTS+{t}/TB[ov{i}]")
        for i,(p,t,d) in enumerate(specs):
            o=f"vb{i}" if i<len(specs)-1 else "vout"
            fc.append(f"[{prev}][ov{i}]overlay=enable='between(t,{t:.2f},{t+d:.2f})':x=0:y=0[{o}]"); prev=o
        fc.append(f"[{sidx}:a]asplit={len(specs)}"+"".join(f"[k{i}]" for i in range(len(specs))))
        for i,(p,t,d) in enumerate(specs):
            ms=int(t*1000); fc.append(f"[k{i}]adelay={ms}|{ms}[d{i}]")
        fc.append("[1:a]volume=1.0[vo]")
        fc.append("[vo]"+"".join(f"[d{i}]" for i in range(len(specs)))+f"amix=inputs={len(specs)+1}:normalize=0[aout]")
        run(["ffmpeg","-y",*inputs,"-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]",
             "-t",f"{vidlen:.2f}","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-r",str(FPS),
             "-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)])
        print(f"Applied {len(specs)} lower-third chyrons + sound stings.")
    else:
        run(["ffmpeg","-y","-i",str(silent),"-i",str(audio),"-c:v","copy","-c:a","aac","-b:a","192k",
             "-shortest","-movflags","+faststart",str(final)])

    fd=probe(final); print(f"\nDone: {final}\n   {fd:.1f}s · {final.stat().st_size/1_000_000:.0f} MB")

if __name__=="__main__": main()
