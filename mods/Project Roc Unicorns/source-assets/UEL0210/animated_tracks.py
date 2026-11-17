import math
import numpy as np
from supcom_binary import write_sca
N=30;H=1.20;R=.27;Y=.29;L=4*H+2*math.pi*R

def path(d):
 d%=L
 if d<2*H:return Y-R,H-d,0.,-1.
 d-=2*H
 if d<math.pi*R:
  a=d/R;return Y-R*math.cos(a),-H-R*math.sin(a),math.sin(a),-math.cos(a)
 d-=math.pi*R
 if d<2*H:return Y+R,-H+d,0.,1.
 a=(d-2*H)/R;return Y+R*math.cos(a),H+R*math.sin(a),-math.sin(a),math.cos(a)

def add_tracks(m,names,parents,pivots,out):
 first=len(names)
 for side in (-1,1):
  for j in range(N):
   y,z,dy,dz=path(j*L/N);x=side*.68;bone=len(names);names.append('Track_'+str(bone));parents.append(0);pivots.append((x,y,z))
   ny,nz=dz,-dy;points=[]
   for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
    points.append(np.array((x+a*.095,y+dy*b*L/N*.44+ny*c*.018,z+dz*b*L/N*.44+nz*c*.018)))
   for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]:
    ps=[points[k] for k in face];normal=np.cross(ps[1]-ps[0],ps[2]-ps[0]);normal/=np.linalg.norm(normal);tan=ps[1]-ps[0];tan/=np.linalg.norm(tan);bit=np.cross(normal,tan);start=len(m.vertices)
    for pt in ps:m.vertices.append(tuple(pt)+tuple(normal)+tuple(tan)+tuple(bit)+(.625,.125,.625,.125,bone))
    m.indices.extend(start+i for i in (0,1,2,0,2,3))
 frames=[]
 for f in range(121):
  poses=[((0,0,0),(1,0,0,0))]
  for side in (-1,1):
   for j in range(N):
    _,_,d0,e0=path(j*L/N);y,z,dy,dz=path(j*L/N+L*f/120);a=math.atan2(dz,dy)-math.atan2(e0,d0);poses.append(((side*.68,y,z),(math.cos(a/2),math.sin(a/2),0,0)))
  frames.append(poses)
 for b in range(1,2*N+1):
  for f in range(1,len(frames)):
   p,q=frames[f][b]
   if sum(x*y for x,y in zip(q,frames[f-1][b][1]))<0:frames[f][b]=(p,tuple(-x for x in q))
 write_sca(out/'UEL0210_tracks.sca',[names[0]]+names[first:],[-1]+[0]*(2*N),frames,L/2.2)
 print('Tracks:',2*N,'bones total:',len(names),'triangles total:',len(m.indices)//3,flush=True)

