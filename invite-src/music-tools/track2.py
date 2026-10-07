import numpy as np, librosa, time
t=time.time()
y,sr=librosa.load('voc.wav',sr=22050,mono=True)
hop=128
f0,v,p=librosa.pyin(y,fmin=75,fmax=1000,sr=sr,frame_length=2048,hop_length=hop,fill_na=None,resolution=0.05)
rms=librosa.feature.rms(y=y,frame_length=1024,hop_length=hop)[0][:len(f0)]
on=librosa.onset.onset_strength(y=y,sr=sr,hop_length=hop)[:len(f0)]
np.savez('pitch2.npz',f0=f0,v=v,p=p,rms=rms,on=on,sr=sr,hop=hop)
db=20*np.log10(rms+1e-9); sing=db>db.max()-35
old=v&(p>0.25)&sing
print('%.0fs'%(time.time()-t),'audible singing %.0f%%'%(100*sing.mean()),'old gate caught %.0f%% of it'%(100*(old&sing).sum()/sing.sum()),
      'loose gate (p>0.05) catches %.0f%%'%(100*((p>0.05)&sing).sum()/sing.sum()))
