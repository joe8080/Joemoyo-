#!/bin/bash
# After Closing Ep 1, Scene 1 "The Mistake": cut, sound and grade.
set -e
cd "$(dirname "$0")"
V="scale=1920:1080:flags=lanczos,setsar=1,fps=24,format=yuv420p"
ffmpeg -y -v error \
  -i s01/01A.mp4 -i s01/01B.mp4 -i s01/01C.mp4 -i s01/01D.mp4 -i s01/01E.mp4 \
  -i audio/piano_phrase.mp3 -i audio/s01_dialogue_12s.mp3 \
  -f lavfi -t 36 -i "anoisesrc=color=brown:amplitude=0.5:r=48000" \
  -filter_complex "
[0:v]trim=0:10,setpts=PTS-STARTPTS,$V[a];
[1:v]trim=0:3.5,setpts=PTS-STARTPTS,$V[b];
[2:v]trim=0:4,setpts=PTS-STARTPTS,$V[c];
[3:v]trim=0:12,setpts=PTS-STARTPTS,$V,unsharp=5:5:0.6[d];
[4:v]trim=0:5,setpts=PTS-STARTPTS,$V[e];
[a][b][c][d][e]concat=n=5:v=1:a=0,noise=alls=7:allf=t,eq=saturation=0.95:contrast=1.03,
 fade=t=in:st=0:d=0.6,fade=t=out:st=33.3:d=1.2[vout];
[5:a]atrim=0:12.4,afade=t=out:st=12.25:d=0.15,adelay=100|100,volume=0.8[pno];
[6:a]adelay=17500|17500,volume=1.0[dlg];
[7:a]lowpass=f=300,volume=0.025,afade=t=in:d=1,afade=t=out:st=33:d=1.5[room];
[pno][dlg][room]amix=inputs=3:normalize=0:duration=longest,atrim=0:34.5,
 aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11[aout]" \
  -map "[vout]" -map "[aout]" -c:v libx264 -preset slow -b:v 8M -maxrate 10M -bufsize 16M -tune grain -c:a aac -b:a 192k \
  -movflags +faststart AfterClosing_E01_S01_TheMistake_16x9.mp4
