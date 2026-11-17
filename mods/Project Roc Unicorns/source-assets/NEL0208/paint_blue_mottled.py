from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageFilter
from supcom_binary import save_dds_dxt5
S=Path(__file__).resolve().parent;A=S/'archive/before-blue-mottled-2026-11-14';ST=S/'blue_mottled_stage';ST.mkdir(exist_ok=True)
al=Image.open(A/'NEL0208_albedo_source.png').convert('RGBA');sp=Image.open(A/'NEL0208_specteam_source.png').convert('RGBA');old=np.asarray(al).copy();out=old.copy();team=np.asarray(sp)[:,:,3]
# Low-frequency world-coordinate variation on the imported hull; continuous
# across UV islands because the field is based on the baked 3D position.
p=np.flipud(np.load(S/'hull_optimized_position.npy'))[:,:,:3]-.5
x,y,z=p[:,:,0],p[:,:,1],p[:,:,2]
field=.5+.20*np.sin(x*25+y*16+z*13)+.17*np.sin(y*29-z*17+x*9)+.10*np.cos(z*41+y*9)
field=np.clip(field,0,1).astype(np.float32)
field=np.asarray(Image.fromarray(field,mode='F').resize((512,512),Image.Resampling.BILINEAR))
# Irregular clouds for the launcher and front armor; independent of pixel noise.
rng=np.random.default_rng(14112026)
def cloud(size,seed_shape):
 small=(rng.random(seed_shape)*255).astype(np.uint8)
 return np.asarray(Image.fromarray(small,mode='L').resize(size,Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(12)),dtype=np.float32)/255
def tint_region(x0,y0,x1,y1,field,amount=.24,solid=False):
 region=old[y0:y1,x0:x1,:3].astype(np.float32);pteam=team[y0:y1,x0:x1];lum=.25*region[:,:,0]+.40*region[:,:,1]+.35*region[:,:,2]
 # Avoid light sensors, very dark grooves and the player-color mask.
 valid=(lum>=25)&(lum<=125)&(pteam==0)
 shade=np.ones_like(lum) if solid else 1-amount*np.clip((field-.38)/.38,0,1)
 result=np.empty_like(region);result[:,:,0]=region[:,:,0]*.97*shade;result[:,:,1]=(region[:,:,1]+3.0)*shade;result[:,:,2]=(region[:,:,2]+9.0)*shade
 patch=out[y0:y1,x0:x1,:3];patch[valid]=np.uint8(np.clip(result[valid],0,255))
 print('region',x0,y0,x1,y1,'armor pixels',int(valid.sum()),'mean delta',np.round((patch.astype(float)-region)[valid].mean(axis=0),2),flush=True)
tint_region(0,0,512,512,field,.32)
tint_region(0,512,512,1024,cloud((512,512),(9,9)),.38)
tint_region(512,128,1024,384,cloud((512,256),(6,11)),.20)
tint_region(525,850,741,1011,cloud((216,161),(5,7)),.30)
# Existing support UV samples this previously unused solid tile. Keep it solid.
tint_region(800,600,1001,801,np.zeros((201,201)),solid=True)
# Shared pad tile, wheel tile, and sensor tile are deliberately untouched.
assert np.array_equal(old[410:501,520:1011],out[410:501,520:1011])
assert np.array_equal(old[0:128,512:1024],out[0:128,512:1024])
assert np.array_equal(old[:,:,3],out[:,:,3])
image=Image.fromarray(out,'RGBA');image.save(ST/'NEL0208_albedo_source.png');save_dds_dxt5(image,ST/'NEL0208_albedo.dds',independent_channels=True)
print('saved recolored albedo; spec/team and normal maps unchanged',flush=True)
