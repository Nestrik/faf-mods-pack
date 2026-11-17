from pathlib import Path
import math,numpy as np
from scm_preview import load_scm,render_scm
from supcom_binary import write_scm
S=Path(__file__).resolve().parent;D=S/'game_stage';verts,faces=load_scm(D/'UEL0210_lod0.scm')
names=['UEL0210','Turret','Turret_Barrel','Turret_Muzzle'];parents=[-1,0,1,2];pivots=[(0,0,0),(0,(.333850682-.095)*3,.235*3),(0,.225*3,.010*3),(0,0,.177*3)]
class Mesh: pass
for name,yaw,pitch in [('yaw',55,0),('pitch',0,25)]:
 m=Mesh();m.vertices=[];m.indices=faces.reshape(-1).tolist();a=math.radians(yaw);b=math.radians(pitch);Y=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]);X=np.array([[1,0,0],[0,math.cos(b),-math.sin(b)],[0,math.sin(b),math.cos(b)]])
 y=np.array(pivots[1]);p=y+np.array(pivots[2])
 for row in verts:
  v=row.copy(); bone=int(v[16]);pos=v[:3]
  if bone>=2: pos=p+X@(pos-p)
  if bone>=1: pos=y+Y@(pos-y)
  v[:3]=pos
  for j in (3,6,9):
   if bone>=2:v[j:j+3]=X@v[j:j+3]
   if bone>=1:v[j:j+3]=Y@v[j:j+3]
  m.vertices.append(tuple(v[:16])+(int(v[16]),))
 target=D/('pose_'+name+'.scm');write_scm(m,target,names,parents,pivots);print('Rendering',name,flush=True);render_scm(target,S,S/('scm_pose_'+name+'.png'),35,28,size=500)
