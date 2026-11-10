import json, numpy as np, subprocess
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR=48000
import os
HERE=os.path.dirname(os.path.abspath(__file__))
tl=json.load(open(os.path.join(HERE,'..','remotion','src','timeline.json')))
N=int(tl['total_frames']/30*SR)+SR
voice=np.zeros(N)
for s in tl['scenes']:
    pth=os.path.join(HERE,"proc",s["id"]+".wav")
    if not os.path.exists(pth): continue
    sr,x=wavfile.read(pth)
    x=x.astype(np.float64)/32768.0
    st=int(s['narr_start']/30*SR)
    voice[st:st+len(x)]+=x
t=np.arange(N)/SR
rng=np.random.default_rng(7)
def lp(x,fc,order=2): return sosfilt(butter(order,fc,'low',fs=SR,output='sos'),x)
def hp(x,fc,order=2): return sosfilt(butter(order,fc,'high',fs=SR,output='sos'),x)
# --- pad: slow evolving chord (A minor 9 voicing), soft
music=np.zeros(N)
chords=[[110,164.81,220,261.63,329.63],[98,146.83,196,246.94,293.66],[87.31,130.81,174.61,220,261.63],[103.83,155.56,207.65,246.94,311.13]]
seg=16.0
for i,ch in enumerate(chords*int(np.ceil(N/SR/seg/4)+1)):
    a=int(i*seg*SR); b=min(N,int((i+1)*seg*SR+3*SR))
    if a>=N: break
    tt=np.arange(b-a)/SR
    env=np.minimum(1,tt/3)*np.minimum(1,np.maximum(0,(seg+3-tt)/3))
    for j,fq in enumerate(ch):
        det=1+0.0015*np.sin(2*np.pi*0.07*tt+j)
        music[a:b]+=env*0.06/(1+j*0.4)*(np.sin(2*np.pi*fq*det*tt)+0.3*np.sin(2*np.pi*fq*2.003*tt))
music=lp(music,1800)
# --- low bass pulse (approx 76 bpm), very soft
bpm=76; beat=60/bpm
pulse=np.zeros(N)
for k in range(int(N/SR/beat)):
    if k%2: continue
    st=int(k*beat*SR); L=int(0.9*SR)
    if st+L>N: break
    tt=np.arange(L)/SR
    pulse[st:st+L]+=0.22*np.sin(2*np.pi*55*tt)*np.exp(-tt*5.5)*(1-np.exp(-tt*120))
music+=pulse
# fade music in/out
fade=np.ones(N); fi=int(2*SR); fade[:fi]=np.linspace(0,1,fi)
endS=int(tl['total_frames']/30*SR); fo=int(6*SR)
fade[endS-fo:endS]=np.linspace(1,0,fo); fade[endS:]=0
music*=fade
# --- sfx
sfx=np.zeros(N)
def tick(sec,g=0.05):
    st=int(sec*SR); L=int(0.06*SR); tt=np.arange(L)/SR
    if st+L<N: sfx[st:st+L]+=g*np.sin(2*np.pi*2400*tt)*np.exp(-tt*90)
def impact(sec,g=0.5):
    st=int(sec*SR); L=int(0.9*SR); tt=np.arange(L)/SR
    f=80*np.exp(-tt*2.2)+38
    ph=2*np.pi*np.cumsum(f)/SR
    if st+L<N: sfx[st:st+L]+=g*np.sin(ph)*np.exp(-tt*4)*(1-np.exp(-tt*200))
def swell(end_sec,dur=3.0,g=0.10):
    L=int(dur*SR); st=int(end_sec*SR)-L
    n=hp(lp(rng.standard_normal(L),3000),300)
    env=(np.arange(L)/L)**2.2
    x=g*n*env/np.max(np.abs(n))
    if st<0: x=x[-st:]; st=0
    sfx[st:st+len(x)]+=x
for i_,s in enumerate(tl['scenes']):
    for c in s['cues'][1:]: tick(c/30)
    if s['new_section'] and i_>0: swell(s['narr_start']/30-0.6,2.4,0.05)
    for k in s.get('impact',[]): impact(s['cues'][k]/30)
    if s.get('riser'): swell(s['narr_start']/30,4.0,0.12)
# --- duck music under voice (sidechain envelope, ~ -20 dB)
env=np.abs(voice); w=int(0.25*SR)
def ma(x,w):
    c=np.cumsum(np.insert(x,0,0)); y=(c[w:]-c[:-w])/w; pad=len(x)-len(y); return np.pad(y,(pad//2,pad-pad//2),mode='edge')
env=ma(env,w)
gate=np.clip(env/0.02,0,1)
gate=ma(gate,int(0.4*SR))
duck=1-0.9*np.clip(gate,0,1)   # -20 dB at full duck
bed=music*duck*0.9
for name,arr in [('voice',voice),('bed',bed),('sfx',sfx)]:
    os.makedirs(os.path.join(HERE,'mix'),exist_ok=True)
    wavfile.write(os.path.join(HERE,'mix',name+'.wav'),SR,(np.clip(arr,-1,1)*32767).astype(np.int16))
print('ok',N/SR)
