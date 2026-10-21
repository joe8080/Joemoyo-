import re, json, time
from pocketsphinx import Decoder
txt=open('/tmp/film2r/audio/VOICEOVER_v2.txt').read()
SUB={"chillers":"chill ers","gigawatt":"gig a watt","gigawatts":"gig a watts","spenders'":"spenders","switchgear":"switch gear","ucits":"you sits"}
disp=txt.split()            # display words with punctuation
toks=[]; owner=[]
for i,w in enumerate(disp):
    for p in [x for x in re.split(r"-",w) if x]:
        n=re.sub(r"[^a-z']","",p.lower().replace("’","'"))
        if not n: continue
        n=SUB.get(n,n)
        for q in n.split():
            toks.append(q); owner.append(i)
d=Decoder(samprate=16000)
d.set_align_text(" ".join(toks))
data=open('/tmp/film2r/audio/vo16.raw','rb').read()
t0=time.time()
d.start_utt(); d.process_raw(data, full_utt=True); d.end_utt()
segs=[(s.word,s.start_frame,s.end_frame) for s in d.seg()]
print("segs",len(segs),"toks",len(toks),"sec",round(time.time()-t0,1))
# match in order
j=0; times=[None]*len(toks)
for w,sf,ef in segs:
    if w in ("<s>","</s>","<sil>","[NOISE]","[SPEECH]") or w.startswith("++"): continue
    base=re.sub(r"\(\d+\)$","",w)
    if j<len(toks) and base==toks[j]:
        times[j]=(sf/100,ef/100); j+=1
print("matched",j,"of",len(toks))
words=[]
cur=None
for k,(tk,o) in enumerate(zip(toks,owner)):
    if times[k] is None: continue
    if words and words[-1]["i"]==o:
        words[-1]["e"]=times[k][1]
    else:
        words.append({"i":o,"w":disp[o],"s":times[k][0],"e":times[k][1]})
json.dump({"words":words},open('/tmp/film2r/audio/words.json','w'),indent=0)
print(words[:6]); print(words[-4:])
