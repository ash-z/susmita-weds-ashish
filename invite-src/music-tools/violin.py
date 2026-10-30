# Violin, played like a violinist: phrases bowed smoothly, singer's ornaments folded in,
# delayed and varying vibrato, three loosely-together players, tone that brightens with loudness.
import numpy as np, scipy.signal as sg, scipy.ndimage as nd, soundfile as sf, pickle
d=np.load('pitch2.npz'); rms=d['rms']; dt=int(d['hop'])/int(d['sr']); N=len(rms); SR=44100
rng=np.random.default_rng(11)
notes=[list(x) for x in pickle.load(open('notes_snap.pkl','rb'))]

# 1. simplify: fold notes shorter than 150 ms into the longer neighbour they touch
def dur(n): return (n[1]-n[0])*dt
while True:
    short=[i for i,n in enumerate(notes) if dur(n)<0.15]
    if not short: break
    i=min(short,key=lambda i:dur(notes[i])); n=notes[i]
    prev=notes[i-1] if i>0 and n[0]-notes[i-1][1]<=3 else None
    nxt=notes[i+1] if i+1<len(notes) and notes[i+1][0]-n[1]<=3 else None
    if prev is None and nxt is None:
        if dur(n)<0.08: notes.pop(i); continue
        n.append('keep'); notes[i]=n[:3]; notes[i][1]=notes[i][0]+int(0.15/dt)+1; continue
    if nxt is None or (prev is not None and dur(prev)>=dur(nxt)): prev[1]=n[1]
    else: nxt[0]=n[0]
    notes.pop(i)
# merge repeated pitches that touch (one bow, no re-articulation)
m2=[]
for n in notes:
    if m2 and n[2]==m2[-1][2] and n[0]-m2[-1][1]<=3: m2[-1][1]=n[1]
    else: m2.append(n)
notes=m2
# 2. phrases: notes closer than 250 ms are one bowed phrase
phr=[[notes[0]]]
for n in notes[1:]:
    if (n[0]-phr[-1][-1][1])*dt<0.25: phr[-1].append(n)
    else: phr.append([n])
print(len(notes),'notes in',len(phr),'phrases')

# pitch: steps with a ~50 ms glide, one octave up; held through rests
center=np.full(N,np.nan)
for a,b,m in notes: center[a:b]=m
idx=np.where(~np.isnan(center))[0]; center=np.interp(np.arange(N),idx,center[idx])
track=nd.gaussian_filter1d(center,7)+12
# loudness: the singer's shape, heavily smoothed inside each phrase (no dips per syllable)
lv=(rms/rms.max())**0.6
env=np.zeros(N); starts=[]
for p in phr:
    a=p[0][0]; b=p[-1][1]; L=b-a
    shape=nd.gaussian_filter1d(lv[a:b],max(1,int(0.18/dt)),mode='nearest')
    t=np.arange(L)*dt
    atk=np.clip(t/0.12,0,1)**1.5
    rel=int(0.3/dt); tail=np.exp(-np.arange(rel)*dt/0.1)
    seg=np.concatenate([shape*atk,shape[-1]*tail])
    e=min(N,a+len(seg)); env[a:e]=np.maximum(env[a:e],seg[:e-a]); starts.append(a)
# vibrato depth per frame: straight for ~0.2 s, then swells in; none on short notes
vd=np.zeros(N)
for a,b,m in notes:
    L=b-a; t=np.arange(L)*dt
    if L*dt<0.3: continue
    depth=rng.uniform(0.14,0.24)*(0.7+0.5*lv[a:b].mean())
    vd[a:b]=depth*np.clip((t-0.2)/0.35,0,1)
vd=nd.gaussian_filter1d(vd,4)

tf=np.arange(N)*dt; L=int(N*dt*SR); ta=np.arange(L)/SR
def slow(sig,sec):   # slow random wander, unit-ish amplitude, at frame rate then stretched
    x=nd.gaussian_filter1d(rng.standard_normal(N),sec/dt); return x/(x.std()+1e-9)
outL=np.zeros(L); outR=np.zeros(L)
for j,pan in enumerate((0.3,0.5,0.7)):
    dly=np.interp(ta,tf,0.012*j+0.008*np.clip(slow(1,1.2),-2,2))                 # timing drift per player
    tt=ta-dly
    T=np.interp(tt,tf,track); A=np.interp(tt,tf,env); V=np.interp(tt,tf,vd)
    rate=5.4+0.25*j+np.interp(tt,tf,0.3*slow(1,2.0))
    vph=2*np.pi*np.cumsum(rate)/SR+rng.uniform(0,6.28)
    cents=np.interp(tt,tf,0.05*slow(1,1.5))+(j-1)*0.04                               # tuning drift
    f=440*2**((T+V*np.sin(vph)+cents-69)/12)
    ph=2*np.pi*np.cumsum(f)/SR+rng.uniform(0,6.28)
    r=0.78+0.14*np.clip(A,0,1)                                                       # louder -> brighter
    gain=10**(np.interp(tt,tf,1.2*slow(1,0.8))/20)                                   # player's own swell
    x=np.zeros(L); rp=np.ones(L)
    for h in range(1,15):
        jit=1+0.12*np.interp(tt,tf,slow(1,0.25))                                     # bow irregularity per harmonic
        x+=np.sin(h*ph)*rp/h*jit
        rp=rp*r
    outL+=x*A*gain*(1-pan); outR+=x*A*gain*pan
# bow: a soft hiss while playing, a little scrape where each phrase begins
A0=np.interp(ta,tf,env); hiss=sg.lfilter(*sg.butter(2,[2500/(SR/2),8000/(SR/2)],'band'),rng.standard_normal(L))
scr=np.zeros(L)
for a in starts:
    s=int(a*dt*SR); n=int(0.07*SR)
    if s+n<L: scr[s:s+n]+=np.linspace(1,0,n)**2
bow=hiss*(0.025*A0+0.12*scr*A0.max())
outL+=bow; outR+=bow
def body(x):
    for fc,q,g in ((290,4,5),(480,3,2.5),(1500,1.5,-3),(2800,1.2,5)):
        w=2*np.pi*fc/SR; al=np.sin(w)/(2*q); Aa=10**(g/40)
        x=sg.lfilter([1+al*Aa,-2*np.cos(w),1-al*Aa],[1+al/Aa,-2*np.cos(w),1-al/Aa],x)
    return sg.lfilter(*sg.butter(4,7500/(SR/2)),sg.lfilter(*sg.butter(2,180/(SR/2),'high'),x))
y=np.stack([body(outL),body(outR)],1)[:int(216.02*SR)]; y=y/np.abs(y).max()*0.8
sf.write('violin2.wav',y.astype(np.float32),SR); print('ok')
