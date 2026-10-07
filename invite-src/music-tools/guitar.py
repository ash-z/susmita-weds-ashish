import numpy as np, scipy.signal as sg, scipy.ndimage as nd, soundfile as sf, librosa
d=np.load('pitch2.npz'); f0=d['f0']; p=d['p']; rms=d['rms']; on=d['on']; hop=int(d['hop']); fsr=int(d['sr'])
dt=hop/fsr; N=len(f0); SR=44100
lf=np.log2(f0)
loc=nd.median_filter(lf,81); dv=lf-loc; lf=np.where(dv>0.6,lf-1,np.where(dv<-0.6,lf+1,lf))
db=20*np.log10(rms+1e-9); sing=db>db.max()-35
std=nd.generic_filter(lf,np.std,size=7); stable=std<0.04
gate=sing&((p>0.03)|stable)
lab,nl=nd.label(gate)
for i in range(1,nl+1):
    if (lab==i).sum()<10: gate[lab==i]=False
lab,nl=nd.label(~gate)
for i in range(1,nl+1):
    idx=np.where(lab==i)[0]
    if len(idx)<=20 and idx[0]>0 and idx[-1]<N-1: gate[idx]=True
midi=nd.median_filter(12*lf+69-12*np.log2(440),7)
pk=set(librosa.util.peak_pick(on,pre_max=8,post_max=8,pre_avg=30,post_avg=30,delta=np.percentile(on,85)*0.5,wait=20))
notes=[]
lab,nl=nd.label(gate)
for i in range(1,nl+1):
    idx=np.where(lab==i)[0]; s=idx[0]; e=idx[-1]+1
    cur=round(np.median(midi[s:s+8])); st=s; run=0; j=s
    while j<e:
        off=abs(midi[j]-cur)>0.7; run=run+1 if off else 0
        new=None
        if run>=6: new=j-5
        elif j in pk and j-st>20 and abs(midi[j]-cur)<=0.7: new=j
        if new is not None and new-st>=9:
            notes.append((st,new,cur)); st=new; cur=round(np.median(midi[new:new+8])); run=0
        j+=1
    notes.append((st,e,cur))
ms=np.array([m for _,_,m in notes]); keep=[abs(m-np.median(ms[max(0,k-6):k+7]))<=8 for k,(_,_,m) in enumerate(notes)]
notes=[x for x,kp in zip(notes,keep) if kp]; print("dropped",len(keep)-sum(keep))
import pickle; pickle.dump(notes,open("notes.pkl","wb"))
print("notes",len(notes),'covering %.0f%% of audible singing'%(100*sum(b-a for a,b,_ in notes)/sing.sum()))
L=int(N*dt*SR)+SR*3; out=np.zeros(L); rng=np.random.default_rng(2)
vmax=rms.max()
for k,(a,b,m) in enumerate(notes):
    t0=a*dt; nxt=notes[k+1][0]*dt if k+1<len(notes) else 1e9
    end=min(nxt, b*dt+0.9) if nxt-b*dt>0.03 else nxt
    n=int((end-t0)*SR)+int(0.02*SR)
    if n<=0: continue
    tt=np.arange(n)/SR
    fr=np.arange(a,min(b+int(1/dt),N))
    cont=np.clip(midi[fr]-m,-1,1)*0.6; cont[(fr>=b)]=cont[min(b-a-1,len(cont)-1)] if b>a else 0
    bend=np.interp(tt,(fr-a)*dt,cont)
    f=440*2**((m+bend-69)/12)
    ph=2*np.pi*np.cumsum(f)/SR
    vel=(rms[a:a+10].max()/vmax)**0.5
    tau1=1.8*(220/f[0])**0.4
    x=np.zeros(n)
    for h in range(1,15):
        if h*f[0]>8000: break
        amp=abs(np.sin(np.pi*h*0.18))/h**1.05
        x+=amp*np.sin(h*ph*np.sqrt(1+1e-4*h*h))*np.exp(-tt/(tau1/(1+0.4*(h-1))))
    x*=np.minimum(1,tt/0.002)
    nb=int(0.008*SR); x[:nb]+=0.25*sg.lfilter(*sg.butter(2,[800/(SR/2),5000/(SR/2)],'band'),rng.standard_normal(nb))*np.linspace(1,0,nb)
    damp=np.ones(n); dn=int(0.02*SR); damp[-dn:]=np.linspace(1,0,dn)
    s0=int(t0*SR); out[s0:s0+n]+=vel*x*damp
out=sg.lfilter(*sg.butter(2,6000/(SR/2)),out)
out=out[:int(216.02*SR)]; out=out/np.abs(out).max()*0.8
sf.write('guitar.wav',np.stack([out,out],1).astype(np.float32),SR)
print('ok')
