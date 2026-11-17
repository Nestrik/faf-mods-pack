from pathlib import Path
import numpy as np, json, shutil
from PIL import Image
from supcom_binary import write_scm,save_dds_dxt5
from scm_preview import render_scm
S=Path(__file__).parent; U=S/'units'/'UEL0212'; U.mkdir(parents=True,exist_ok=True)
a=Image.new('RGBA',(512,512),(20,23,28,0)); mask=np.zeros((512,512),dtype=np.uint8)
for i in range(3):
 x=(i%2)*256;y=(i//2)*256
 im=Image.open(S/f'texture{i}.png').convert('RGB').resize((256,256),Image.Resampling.LANCZOS);p=np.asarray(im);r=p[:,:,0].astype(int);g=p[:,:,1].astype(int);b=p[:,:,2].astype(int)
 a.paste(im.convert('RGBA'),(x,y));mask[y:y+256,x:x+256]=(((b>60)&(b>r*1.4)&(b>g*1.1)&(b-r>15))*160).astype('uint8')
arr=np.array(a);arr[:,:,3]=0;a=Image.fromarray(arr); spec=np.zeros((512,512,4),dtype=np.uint8);spec[:,:,:3]=(48,36,0);spec[:,:,3]=mask
normal=Image.new('RGBA',(512,512),(128,128,255,128))
for suffix,img in [('albedo',a),('specteam',Image.fromarray(spec)),('normalsTS',normal)]:
 img.save(S/f'UEL0212_{suffix}_source.png');save_dds_dxt5(img,U/f'UEL0212_{suffix}.dds',independent_channels=True);print(suffix,flush=True)
names=['UEL0212','Turret','Turret_Barrel','Muzzle_Top','Muzzle_Left','Muzzle_Right'];parents=[-1,0,1,2,2,2];pivots=[(0,0,0),(0,.635,0),(0,.42,.48),(0,.28,1.06),(-.44,-.21,1.06),(.44,-.21,1.06)]
class Mesh:pass
m=Mesh();m.vertices=[];m.indices=[];lookup={}
for row in json.loads((S/'mesh.json').read_text()):
 x,y,z,nx,ny,nz,u,v,part=row;part=int(part);normal=np.array([nx,ny,nz]);ref=np.array([0.,0.,1.]) if abs(ny)>.9 else np.array([0.,1.,0.]);tan=np.cross(ref,normal);tan/=max(np.linalg.norm(tan),1e-10);bit=np.cross(normal,tan);uv=((u%1)/2+(part%2)*.5,((1-v)%1)/2+(part//2)*.5);data=(x,y,z,nx,ny,nz,*tan,*bit,*uv,*uv,part);key=tuple(round(k,7) for k in data)
 if key not in lookup:lookup[key]=len(m.vertices);m.vertices.append(data)
 m.indices.append(lookup[key])
print('mesh',len(m.vertices),len(m.indices)//3,flush=True);write_scm(m,U/'UEL0212_lod0.scm',names,parents,pivots)
# Renderer references names from its original unit; local aliases only for preview.
for suffix in ['albedo','specteam','normalsTS']:shutil.copyfile(U/f'UEL0212_{suffix}.dds',U/f'UEL0210_{suffix}.dds')
for name,az,el in [('front',0,12),('side',90,14),('perspective',35,25),('top',0,85)]:render_scm(U/'UEL0212_lod0.scm',S,S/f'scm_{name}.png',az,el,size=640)
render_scm(U/'UEL0212_lod0.scm',S,S/'icon.png',35,28,size=256,transparent=True)
for suffix in ['albedo','specteam','normalsTS']:(U/f'UEL0210_{suffix}.dds').unlink()
im=Image.open(S/'icon.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS); (S/'icons').mkdir(exist_ok=True);save_dds_dxt5(im,S/'icons'/'UEL0212_icon.dds')
