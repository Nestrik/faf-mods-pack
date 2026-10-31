"""Compile separate approved-model Unit-shader maps; leave projectile atlas untouched."""
from pathlib import Path
from io import BytesIO
import json,struct
import numpy as np
from PIL import Image
SOURCE_DIR=Path(__file__).resolve().parent
MOD=SOURCE_DIR.parents[2]
ROOT=MOD.parents[1];OUT=ROOT/'outputs/Itha_Yen_Metal_v2';UNIT=OUT/'GGA0401';UNIT.mkdir(parents=True,exist_ok=True)
W,H=4096,2048
mask=np.asarray(Image.open(SOURCE_DIR/'gondola_ornament_mask.png').convert('L'))
a=np.zeros((H,W,4),dtype=np.uint8);s=np.zeros_like(a);n=np.zeros_like(a)
# Calibrate the existing Unit shader against the current GGA2404 Seraphim shader.
# Raw Seraphim albedo bytes are not transferable: its shader adds a substantial
# metallic base before lighting; Unit instead multiplies raw albedo by 1.9.
turret=MOD/'units/GGA2404'
ta=np.asarray(Image.open(turret/'GGA2404_albedo.dds').convert('RGBA'))
ts=np.asarray(Image.open(turret/'GGA2404_specteam.dds').convert('RGBA'))
calibration={}
def metal_tile(name,tile):
 h,w=ta.shape[:2];x=tile%4*w//4;y=tile//4*h//2
 raw=np.median(ta[y+30:y+h//2-30,x+30:x+w//4-30,:3],axis=(0,1))
 spec=np.median(ts[y+30:y+h//2-30,x+30:x+w//4-30,:],axis=(0,1))
 target=(raw[[2,2,1]]/255+np.array([.4,.43,.47]))*.8
 # Unit lacks Seraphim's subsequent color/team contrast pass. Keep a
 # conservative dark-steel response instead of matching only its raw remap.
 unit_target=target*.65
 albedo=np.rint(unit_target/1.9*255).astype(np.uint8)
 rough=(1.3-np.sqrt(spec[1]/255))*.7
 g=int(round(np.clip((.65-rough)/.6,0,1)*255))
 # Unit's R>~166 is a special bright cockpit mask at high fidelity.
 # 160 raises medium-fidelity reflections without activating that mask.
 sp=(160,g,0,0)
 calibration[name]={'turret_raw_rgb':raw.tolist(),'turret_spec':spec.tolist(),
  'target_shader_albedo':target.tolist(),'unit_tone_scale':.65,'unit_shader_target':unit_target.tolist(),'unit_rgb':albedo.tolist(),
  'unit_spec':sp,'roughness':float(rough)}
 return tuple(int(v) for v in albedo),sp
metal=metal_tile('metal',1);edge=metal_tile('edge',2)
recess=metal_tile('recess',4);steel=metal_tile('steel',7)
a[:,:,:]=(*metal[0],255);s[:,:,:]=metal[1];n[:,:,:]=(128,128,255,128)
# Team tint, emission and fixed-violet ring remain independent of calibration.
s[:1024,:,3]=mask;s[:1024,:,2]=(mask.astype(np.float32)*.075).astype(np.uint8)
t=mask.astype(np.float32)/255
s[:1024,:,0]=np.rint(160*(1-t)+90*t).astype(np.uint8)
s[:1024,:,1]=np.rint(metal[1][1]*(1-t)+140*t).astype(np.uint8)
palette=[metal,edge,recess,steel,((50,50,50),(45,140,18,255)),((50,50,50),(45,140,180,255)),((55,3,175),(40,140,255,0))]
for i,(al,sp) in enumerate(palette):
 a[1024:,i*512:(i+1)*512,:3]=al;s[1024:,i*512:(i+1)*512]=sp
(OUT/'turret_material_calibration.json').write_text(json.dumps(calibration,indent=2))
# Tiny neutral surface variation; no baked lighting or team hue in the diffuse.
rng=np.random.default_rng(2401);noise=rng.integers(-1,2,(H,W,1),dtype=np.int16)
a[:,:,:3]=np.clip(a[:,:,:3].astype(np.int16)+noise,0,255).astype(np.uint8)

def save_bc3_mips(im,path):
 blobs=[];current=im;count=0
 while True:
  buf=BytesIO();current.save(buf,format='DDS',pixel_format='DXT5');data=buf.getvalue();blobs.append(data[128:]);count+=1
  if current.size==(1,1):break
  wh=(max(1,current.width//2),max(1,current.height//2))
  current=Image.merge('RGBA',tuple(c.resize(wh,Image.Resampling.LANCZOS) for c in current.split()))
 hdr=bytearray(data[:128]);struct.pack_into('<I',hdr,8,0x1|0x2|0x4|0x1000|0x20000|0x80000)
 struct.pack_into('<4I',hdr,12,im.height,im.width,((im.width+3)//4)*((im.height+3)//4)*16,0)
 struct.pack_into('<I',hdr,28,count);struct.pack_into('<I',hdr,108,0x401008)
 path.write_bytes(hdr+b''.join(blobs))
for suffix,array in [('albedo',a),('specteam',s),('normalsTS',n)]:
 im=Image.fromarray(array);im.save(OUT/f'GGA0401_approved_{suffix}.png');save_bc3_mips(im,UNIT/f'GGA0401_approved_{suffix}.dds');print('DDS',suffix,flush=True)
# Export decoding proof uses shipped DDS pixels, not the source PNG.
for suffix in ['albedo','specteam','normalsTS']:
 Image.open(UNIT/f'GGA0401_approved_{suffix}.dds').save(OUT/f'decoded_{suffix}.png')
print('MATERIALS_DONE')
