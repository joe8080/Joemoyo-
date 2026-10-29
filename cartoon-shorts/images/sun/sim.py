import numpy as np, sys
Re=2420.0; s=150/283.4
h=np.array([-(239.87-597)*s, (-380+22)+(211.8-1692)*s])/Re   # mirrored windup hand
def acc(p,v,th):
    r=np.linalg.norm(p); a=-p/r**3
    if th: a=a-th*v/np.linalg.norm(v)
    return a
def run(tL,q,ang,burn,brake,T=7,dt=0.0005):
    E=np.array([np.sin(tL),np.cos(tL)]); vE=np.array([np.cos(tL),-np.sin(tL)])
    p=E+h; v=vE+q*np.array([np.cos(ang),np.sin(ang)]); t=tL; out=[(t,np.linalg.norm(p),*p,*v)]
    while t<tL+T:
        th=0
        if burn[0]<=t<burn[1]: th=burn[2]
        if brake[0]<=t<brake[1]: th=brake[2]
        f=lambda p,v:(v,acc(p,v,th))
        k1=f(p,v);k2=f(p+dt/2*k1[0],v+dt/2*k1[1]);k3=f(p+dt/2*k2[0],v+dt/2*k2[1]);k4=f(p+dt*k3[0],v+dt*k3[1])
        p=p+dt/6*(k1[0]+2*k2[0]+2*k3[0]+k4[0]); v=v+dt/6*(k1[1]+2*k2[1]+2*k3[1]+k4[1]); t+=dt
        out.append((t,np.linalg.norm(p),*p,*v))
        if np.linalg.norm(p)<0.2: break
    return np.array(out)
tL=float(sys.argv[1]); q=float(sys.argv[2]); ang=np.radians(float(sys.argv[3]))
bdur=float(sys.argv[4]); bth=float(sys.argv[5]); rV=float(sys.argv[6]); kdur=float(sys.argv[7]); kth=float(sys.argv[8])
o=run(tL,q,ang,(0,0,0),(0,0,0)); r=o[:,1]
i=np.argmin(r[:len(r)//2]); j=i+np.argmax(r[i:i+int(3/0.0005)])
tp,ta=o[i,0],o[j,0]
print(f"r0={r[0]:.3f} peri r={r[i]:.3f} tau={tp:.3f} (d={tp-tL:.2f}) apo r={r[j]:.3f} tau={ta:.3f}")
o2=run(tL,q,ang,(ta,ta+bdur,bth),(0,0,0)); r2=o2[:,1]; k=np.searchsorted(o2[:,0],ta+bdur)
seg=r2[k:]; pi=np.argmin(seg); print(f" after burn: speed {np.hypot(*o2[k,4:6]):.3f} (was {np.hypot(*o[j,4:6]):.3f}) new peri {seg[pi]:.3f} at tau {o2[k+pi,0]:.3f}")
# inbound crossing of rV
c=k+np.argmax(seg<rV); tV=o2[c,0]; print(f" crosses r={rV} at tau={tV:.3f} pos={o2[c,2:4]}")
o3=run(tL,q,ang,(ta,ta+bdur,bth),(tV-kdur*0.3,tV+kdur*0.7,kth)); 
print(f" with brake: ends tau={o3[-1,0]:.3f} r={o3[-1,1]:.3f}  speed before {np.hypot(*o2[c,4:6]):.3f}")
print(f"EVENTS tL={tL} tp={tp:.4f} ta={ta:.4f} tb1={ta+bdur:.4f} tV={tV:.4f} tHit={o3[-1,0]:.4f}")
