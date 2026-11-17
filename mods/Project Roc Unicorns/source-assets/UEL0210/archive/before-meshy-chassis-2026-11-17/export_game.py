from pathlib import Path
from io import BytesIO
import struct,json
import numpy as np
from PIL import Image,ImageDraw
from supcom_binary import write_scm,save_dds_dxt5
S=Path(__file__).resolve().parent; OUT=S/'game_stage';OUT.mkdir(exist_ok=True)
d=(S/'sonic_rebuilt_rig.glb').read_bytes();n=struct.unpack_from('<I',d,12)[0];g=json.loads(d[20:20+n]);base=28+n
N={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}; DT={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}
def accessor(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];t=np.dtype(DT[a['componentType']]);n=N[a['type']];return np.ndarray((a['count'],n),dtype=t,buffer=d,offset=base+v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',t.itemsize*n),t.itemsize)).copy()
def image(i):
 v=g['bufferViews'][g['images'][i]['bufferView']];return Image.open(BytesIO(d[base+v.get('byteOffset',0):base+v.get('byteOffset',0)+v['byteLength']])).convert('RGBA')
# Original user-provided texture in the top-left quadrant; separate solid swatches for rebuilt parts.
al=Image.new('RGBA',(512,512),(32,36,42,0)); al.paste(image(0).resize((256,256),Image.Resampling.LANCZOS),(0,0));sp=Image.new('RGBA',(512,512),(55,65,0,0));nm=Image.new('RGBA',(512,512),(128,128,255,128)); draw=ImageDraw.Draw(al)
for k,col in enumerate([(25,30,38,0),(30,38,48,0),(61,69,77,0),(54,64,74,0)]):
 x=256+(k%2)*128;y=(k//2)*128;draw.rectangle((x,y,x+127,y+127),fill=col)
# Unit shader uses SpecTeam.A for player color; small existing blue source markings only.
a=np.array(al);r,gg,b=a[:256,:256,0].astype(int),a[:256,:256,1].astype(int),a[:256,:256,2].astype(int);v=np.array(sp);v[:256,:256,3]=(((b>65)&(b>r*1.45)&(b>gg*1.16)&(b-r>18))*180).astype('uint8');sp=Image.fromarray(v)
for suffix,img in [('albedo',al),('specteam',sp),('normalsTS',nm)]:
 img.save(S/('UEL0210_'+suffix+'_source.png'));save_dds_dxt5(img,OUT/('UEL0210_'+suffix+'.dds'),independent_channels=True);print('DDS',suffix,flush=True)
names=['UEL0210','Turret','Turret_Barrel','Turret_Muzzle'];parents=[-1,0,1,2];scale=3;ground=.333850682;nodes=g['nodes'];skin=g['skins'][0];joints=[nodes[x]['name'] for x in skin['joints']]; pivots=[(0,0,0),(0,(ground-.095)*scale,.235*scale),(0,.225*scale,.010*scale),(0,0,.177*scale)]
class Mesh: pass
m=Mesh();m.vertices=[];m.indices=[]
for mesh in g['meshes']:
 for prim in mesh['primitives']:
  at=prim['attributes'];p=accessor(at['POSITION']).astype(float);p[:,1]+=ground;p*=scale
  normal=accessor(at['NORMAL']).astype(float);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
  ref=np.tile([0.,1.,0.],(len(p),1));ref[np.abs(normal[:,1])>.9]=[0.,0.,1.];tan=np.cross(ref,normal);tan/=np.maximum(np.linalg.norm(tan,axis=1)[:,None],1e-10);bit=np.cross(normal,tan)
  mat=prim['material'];uv=accessor(at['TEXCOORD_0']).astype(float)*.5 if mat==4 else np.tile((.625+(mat%2)*.25,.125+(mat//2)*.25),(len(p),1))
  ji=accessor(at['JOINTS_0']);wt=accessor(at['WEIGHTS_0']);pick=ji[np.arange(len(p)),np.argmax(wt,axis=1)];bone=np.array([names.index(joints[int(k)]) for k in pick]);ix=accessor(prim['indices']).reshape(-1).astype(int);start=len(m.vertices)
  allv=np.column_stack((p,normal,tan,bit,uv,uv,bone));m.vertices.extend(tuple(row[:16])+(int(row[16]),) for row in allv);m.indices.extend((ix+start).tolist())
print('SCM',len(m.vertices),'vertices',len(m.indices)//3,'triangles',flush=True)
assert len(m.vertices)<65535
write_scm(m,OUT/'UEL0210_lod0.scm',names,parents,pivots)
