import numpy as np, pickle, scipy.ndimage as nd
d=np.load('pitch2.npz'); f0=d['f0']; dt=int(d['hop'])/int(d['sr'])
lf=np.log2(f0); loc=nd.median_filter(lf,81); dv=lf-loc; lf=np.where(dv>0.6,lf-1,np.where(dv<-0.6,lf+1,lf))
midi=12*lf+69-12*np.log2(440)
scale={9,11,1,2,4,6,8}                      # A major: A B C# D E F# G#
def snap(x):
    c=[n for n in range(int(x)-2,int(x)+3) if n%12 in scale]
    return min(c,key=lambda n:abs(n-x))
notes=pickle.load(open('notes.pkl','rb')); out=[]
for a,b,_ in notes:
    L=b-a; core=midi[a+int(L*.25):max(a+int(L*.25)+1,b-int(L*.15))]
    m=snap(float(np.median(core)))
    if L*dt<0.08 and out and a-out[-1][1]<3: out[-1]=(out[-1][0],b,out[-1][2]); continue   # passing note: part of the one before
    if out and m==out[-1][2] and a-out[-1][1]<3 and L*dt<0.12: out[-1]=(out[-1][0],b,m); continue
    out.append((a,b,m))
names='C C# D D# E F F# G G# A A# B'.split()
h=np.bincount(np.array([x[2] for x in out])%12,minlength=12)/len(out)
print(len(notes),'->',len(out),'notes;',' '.join(f'{names[i]}:{h[i]*100:.0f}' for i in np.argsort(-h) if h[i]))
pickle.dump(out,open('notes_snap.pkl','wb'))
