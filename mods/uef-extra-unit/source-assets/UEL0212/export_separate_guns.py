from pathlib import Path
import json, numpy as np, sys, shutil, math
S=Path(__file__).resolve().parent;sys.path.insert(0,str(S));from supcom_binary import write_scm
from scm_preview import render_scm
stage=S/'game_stage';stage.mkdir(parents=True,exist_ok=True)
unit=S.parents[1]/'units'/'UEL0212'
names=['UEL0212','Turret','Turret_Barrel','Recoil_Top','Muzzle_Top','Barrel_Left','Recoil_Left','Muzzle_Left','Barrel_Right','Recoil_Right','Muzzle_Right']
parents=[-1,0,1,2,3,1,5,6,1,8,9]
pivots=[(0,0,0),(0,.635,0),(0,.725,.60),(0,0,0),(0,0,.96),(-.45,.235,.60),(0,0,0),(0,0,.96),(.45,.235,.60),(0,0,0),(0,0,.96)]
rows=json.loads((S/'mesh.json').read_text());assert len(rows)%3==0
class Mesh:pass
m=Mesh();m.vertices=[];m.indices=[];lookup={};counts={'hull':0,'turret':0,'Top':0,'Left':0,'Right':0}
for j in range(0,len(rows),3):
 tri=rows[j:j+3];part=tri[0][8];assert all(x[8]==part for x in tri)
 if part==0:bone=0;counts['hull']+=1
 elif part==1:bone=1;counts['turret']+=1
 else:
  ys=[r[1] for r in tri]; assert max(ys)<1.12 or min(ys)>1.12
  which='Top' if min(ys)>1.12 else ('Left' if sum(r[0] for r in tri)<0 else 'Right');bone={'Top':3,'Left':6,'Right':9}[which];counts[which]+=1
 for row in tri:
  x,y,z,nx,ny,nz,u,v,part=row;part=int(part);normal=np.array([nx,ny,nz]);ref=np.array([0.,0.,1.]) if abs(ny)>.9 else np.array([0.,1.,0.]);tan=np.cross(ref,normal);tan/=max(np.linalg.norm(tan),1e-10);bit=np.cross(normal,tan);uv=((u%1)/2+(part%2)*.5,((1-v)%1)/2+(part//2)*.5);data=(x,y,z,nx,ny,nz,*tan,*bit,*uv,*uv,bone);key=tuple(round(k,7) for k in data)
  if key not in lookup:lookup[key]=len(m.vertices);m.vertices.append(data)
  m.indices.append(lookup[key])
assert [counts[x] for x in ['Top','Left','Right']]==[346,274,380],counts
write_scm(m,stage/'UEL0212_lod0.scm',names,parents,pivots);print('triangles',counts,'vertices',len(m.vertices),flush=True)
for s in ['albedo','specteam','normalsTS']:shutil.copyfile(unit/f'UEL0212_{s}.dds',stage/f'UEL0210_{s}.dds')
render_scm(stage/'UEL0212_lod0.scm',S,stage/'scm_separate_front.png',0,12,size=640)
render_scm(stage/'UEL0212_lod0.scm',S,stage/'scm_separate_perspective.png',35,25,size=640)
# Test individual recoil displacements by writing and rendering poses read back from SCM.
for which,bi in [('Top',3),('Left',6),('Right',9)]:
 pose=Mesh();pose.indices=m.indices;pose.vertices=[tuple((v[0],v[1],v[2]-(.22 if v[16]==bi else 0),*v[3:])) for v in m.vertices]
 path=stage/f'pose_{which}.scm';write_scm(pose,path,names,parents,pivots);render_scm(path,S,stage/f'pose_recoil_{which}.png',35,25,size=640)
print('rendered neutral and recoil poses',flush=True)

