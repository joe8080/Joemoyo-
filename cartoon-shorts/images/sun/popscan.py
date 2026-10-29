# Mean frame-to-frame difference (blurred, 270x480); flag frames > 2.2x the local median.
import subprocess, numpy as np, cv2, sys
f=sys.argv[1]; w,h=270,480
raw=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf',f'scale={w}:{h}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True).stdout
fr=np.frombuffer(raw,np.uint8).reshape(-1,h,w).astype(np.float32)
fr=np.stack([cv2.GaussianBlur(x,(5,5),0) for x in fr])
d=np.abs(np.diff(fr,axis=0)).mean((1,2))
flags=[]
for i in range(len(d)):
    lo,hi=max(0,i-15),min(len(d),i+16); med=np.median(d[lo:hi])
    if d[i]>2.2*max(med,0.05) and d[i]>0.4: flags.append((i+1,round((i+1)/60,3),round(float(d[i]),2),round(float(med),2)))
print('frames',len(fr),'flags',len(flags))
for x in flags: print(x)
# frozen check at the end
print('last 10 diffs',np.round(d[-10:],3))
