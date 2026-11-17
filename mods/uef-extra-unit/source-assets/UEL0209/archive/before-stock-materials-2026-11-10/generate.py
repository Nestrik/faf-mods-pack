from pathlib import Path
import math
from PIL import Image, ImageDraw
from model_geometry import Mesh, render_scm, load_scm
from supcom_binary import write_scm, save_dds_dxt5
H=Path(__file__).resolve().parent
U=H.parents[1]/'units'/'UEL0209'
N=['UEL0209','Turret','Turret_Barrel','Recoil_Left','Recoil_Right','Muzzle_Left','Muzzle_Right']
P=[-1,0,1,2,2,3,4]
V=[(0,0,0),(0,.85,-.1),(0,.23,.1),(0,0,0),(0,0,0),(-.42,0,2.37),(.42,0,2.37)]
def box(m,x,y,z,sx,sy,sz,mat='armor',bone=0):
 rings=[[(x-sx/2,y-sy/2,z+d*sz/2),(x+sx/2,y-sy/2,z+d*sz/2),(x+sx/2,y+sy/2,z+d*sz/2),(x-sx/2,y+sy/2,z+d*sz/2)] for d in (-1,1)]
 m.loft(rings,[(x,y,z-sz/2),(x,y,z+sz/2)],bone,mat)
def cylinder(m,x,y,z,rad,length,axis,mat,bone=0,n=16):
 rings=[]; centers=[]
 for t in (-length/2,length/2):
  c=(x+t,y,z) if axis=='x' else (x,y,z+t); centers.append(c)
  rings.append([(c[0],y+rad*math.cos(a*2*math.pi/n),z+rad*math.sin(a*2*math.pi/n)) if axis=='x' else (x+rad*math.cos(a*2*math.pi/n),y+rad*math.sin(a*2*math.pi/n),c[2]) for a in range(n)])
 m.loft(rings,centers,bone,mat)
def chamfer(m,sections,mat='armor',bone=0):
 # Cross sections: z, half width, bottom, top; eight-sided armor shell.
 rings=[]; centers=[]
 for z,w,lo,hi in sections:
  c=min(w*.22,(hi-lo)*.28)
  rings.append([(-w+c,lo,z),(w-c,lo,z),(w,lo+c,z),(w,hi-c,z),(w-c,hi,z),(-w+c,hi,z),(-w,hi-c,z),(-w,lo+c,z)])
  centers.append((0,(lo+hi)/2,z))
 m.loft(rings,centers,bone,mat)
def shifted_chamfer(m,x,sections,mat='armor',bone=0):
 start=len(m.vertices); chamfer(m,sections,mat,bone)
 for i in range(start,len(m.vertices)):
  v=list(m.vertices[i]); v[0]+=x; m.vertices[i]=tuple(v)
def make(detail):
 m=Mesh(detail); fine=detail>8
 # Thick tracked bogies; front and rear sets remain distinct.
 for side in (-1,1):
  for zc in (-.91,.91):
   x=side*.77
   shifted_chamfer(m,x,[(zc-.83,.19,.18,.46),(zc-.67,.22,.045,.56),(zc+.67,.22,.045,.56),(zc+.83,.19,.18,.46)],'joint')
   # Transverse track shoes wrap over the top and run down both ends.
   for j in range(10 if fine else 6):
    z=zc-.66+j*1.32/(9 if fine else 5)
    box(m,x,.565,z,.46,.055,.105 if fine else .15,'steel')
    box(m,x,.599,z,.35,.022,.035,'edge')
   for z in (zc-.76,zc+.76):
    for y in (.20,.31,.42): box(m,x,y,z,.45,.055,.07,'steel')
   for z in (zc-.55,zc-.28,zc,zc+.28,zc+.55):
    cylinder(m,x+side*.218,.29,z,.18,.045,'x','dark',n=detail)
    cylinder(m,x+side*.245,.29,z,.132,.025,'x','steel',n=detail)
    cylinder(m,x+side*.261,.29,z,.051,.025,'x','edge',n=detail)
   # Armored fender with contrasting raised strips.
   shifted_chamfer(m,x,[(zc-.80,.25,.60,.66),(zc-.68,.26,.60,.72),(zc+.68,.26,.60,.72),(zc+.80,.25,.60,.66)],'armor')
   box(m,x,.73,zc,.35,.035,1.22,'steel')
   for z in (zc-.48,zc,zc+.48): box(m,x,.752,z,.32,.015,.035,'dark')
 # Layered central chassis and low sloped nose.
 chamfer(m,[(-1.72,.50,.20,.67),(-1.48,.65,.15,.83),(.95,.65,.15,.83),(1.55,.57,.18,.71),(1.75,.46,.25,.53)],'armor')
 chamfer(m,[(-1.64,.47,.67,.75),(-1.43,.54,.72,.89),(-.73,.54,.72,.89),(-.60,.50,.74,.84)],'steel')
 # Rear deck framed vents.
 for side in (-1,1):
  box(m,side*.40,.906,-1.18,.22,.035,.73,'dark')
  for z in [-1.47+i*.10 for i in range(7)]: box(m,side*.40,.93,z,.20,.025,.035,'edge')
  box(m,side*.60,.73,-.08,.12,.20,1.15,'steel')
  box(m,side*.62,.85,-.08,.09,.04,.90,'team')
 # Nose glacis, panels and inset grille.
 chamfer(m,[(.67,.49,.81,.86),(1.22,.49,.69,.88),(1.61,.40,.52,.70)],'steel')
 for side in (-1,1):
  box(m,side*.35,.85,.94,.17,.045,.43,'team')
  box(m,side*.35,.87,1.22,.17,.04,.10,'dark')
  box(m,side*.35,.88,1.22,.09,.02,.045,'lens')
 box(m,0,.63,1.68,.55,.16,.06,'dark')
 for x in (-.21,-.14,-.07,0,.07,.14,.21): box(m,x,.64,1.72,.025,.13,.025,'edge')
 # Turret turntable and stepped, faceted armor; geometry bound to yaw bone.
 cylinder(m,0,.88,-.10,.46,.14,'z','dark',1,detail) if False else None
 chamfer(m,[(-.77,.42,.91,1.11),(-.62,.56,.90,1.25),(.26,.56,.90,1.25),(.50,.42,.93,1.12)],'dark',1)
 chamfer(m,[(-.65,.39,1.12,1.32),(-.48,.48,1.12,1.43),(.15,.48,1.12,1.43),(.40,.34,1.12,1.26)],'armor',1)
 chamfer(m,[(-.50,.31,1.43,1.49),(-.38,.34,1.43,1.54),(.03,.34,1.43,1.54),(.19,.23,1.43,1.48)],'steel',1)
 box(m,0,1.55,-.25,.35,.03,.30,'team',1)
 for side in (-1,1):
  box(m,side*.46,1.32,-.23,.06,.16,.53,'edge',1)
  box(m,side*.405,1.445,-.20,.07,.025,.38,'dark',1)
  for z in (-.35,-.26,-.17,-.08): box(m,side*.405,1.465,z,.065,.015,.035,'edge',1)
 # Twin armored breeches, nested gun sleeves, muzzle brakes; common pitch.
 for x, recoil in ((-.42,3),(.42,4)):
  shifted_chamfer(m,x,[(.28,.17,.90,1.25),(.56,.18,.90,1.25),(.74,.13,.96,1.19)],'armor',2)
  cylinder(m,x,1.08,1.32,.115,1.25,'z','steel',recoil,detail)
  for z in (.85,1.25,1.65,1.91): cylinder(m,x,1.08,z,.13,.045,'z','edge',recoil,detail)
  shifted_chamfer(m,x,[(2.00,.145,.94,1.22),(2.10,.16,.93,1.23),(2.34,.16,.93,1.23)],'dark',recoil)
  cylinder(m,x,1.08,2.348,.105,.015,'z','joint',recoil,detail)
  for z in (2.13,2.21,2.29):
   for side in (-1,1): box(m,x+side*.162,1.08,z,.016,.10,.035,'edge',recoil)
 return m
def textures():
 # Independent material atlas, based on UEF steel plate references. Unit shader:
 # team mask in SpecTeam.A; packed normal coordinates in G/A.
 import numpy as np
 from PIL import ImageFilter
 rng=np.random.default_rng(266419)
 size=128; width=512; height=256
 colors=[(71,79,92),(32,36,43),(109,119,131),(83,91,103),(69,78,91),(87,91,94),(194,205,209),(26,29,33)]
 al=Image.new('RGBA',(width,height)); sp=Image.new('RGBA',al.size); relief=Image.new('L',al.size,128)
 da=ImageDraw.Draw(al); ds=ImageDraw.Draw(sp); dh=ImageDraw.Draw(relief)
 for i,c in enumerate(colors):
  x=(i%4)*size; y=(i//4)*size
  da.rectangle((x,y,x+127,y+127),fill=(*c,0))
  ds.rectangle((x,y,x+127,y+127),fill=(58 if i not in (1,7) else 24,88 if i not in (1,7) else 50,0,210 if i==4 else 0))
  # Chamfered panel borders have painted highlights and recessed dark seams.
  if i in (0,2,3,4):
   dark=(29,35,43,0); light=(131,143,155,0) if i!=2 else (161,169,177,0)
   da.rectangle((x+12,y+8,x+116,y+119),outline=dark,width=2)
   da.line((x+15,y+12,x+113,y+12),fill=light,width=1)
   da.line((x+15,y+13,x+15,y+114),fill=light,width=1)
   da.line((x+15,y+116,x+113,y+116),fill=(38,44,53,0),width=2)
   dh.rectangle((x+13,y+9,x+115,y+118),outline=103,width=2)
   # Offset equipment panels and small screws, restrained so that each face
   # remains legible at game zoom despite sharing an atlas tile.
   for px,py in ((20,20),(108,20),(20,108),(108,108)):
    da.ellipse((x+px-2,y+py-2,x+px+2,y+py+2),fill=(28,34,42,0))
    da.point((x+px-1,y+py-1),fill=(165,174,184,0))
   if i==0:
    da.line((x+22,y+77,x+48,y+77,x+58,y+87,x+104,y+87),fill=(44,52,64,0),width=2)
    da.line((x+22,y+79,x+47,y+79),fill=(118,129,143,0),width=1)
   elif i==3:
    for yy in (37,41,45): da.line((x+29,y+yy,x+98,y+yy),fill=(53,61,73,0),width=1)
  elif i==1:
   # Dark framed recess, suitable for breeches and inset machinery.
   for yy in (27,42,57,72,87,102):
    da.line((x+20,y+yy,x+108,y+yy),fill=(45,51,58,0),width=2)
    da.line((x+20,y+yy+2,x+108,y+yy+2),fill=(19,23,29,0),width=1)
  elif i==7:
   # Heavy dark steel and rub marks on track and muzzle recesses.
   for yy in (30,62,94): da.line((x+13,y+yy,x+115,y+yy),fill=(48,51,55,0),width=1)
 # Combine broad cloudy wear with fine metallic grain independently of alpha.
 arr=np.asarray(al).copy().astype(np.int16)
 coarse=Image.fromarray(rng.integers(0,256,(32,64),dtype=np.uint8),'L').resize((width,height),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(2))
 cloud=(np.asarray(coarse,dtype=np.int16)-128)*0.12
 grain=rng.normal(0,2.2,(height,width))
 weather=cloud+grain
 arr[:,:,:3]=np.clip(arr[:,:,:3]+weather[:,:,None],0,255)
 al=Image.fromarray(arr.astype(np.uint8),'RGBA')
 # Tiny relief on the painted seams; a neutral background keeps smooth plates flat.
 h=np.asarray(relief.filter(ImageFilter.GaussianBlur(.65)),dtype=np.float32)
 dy,dx=np.gradient(h)
 nm=np.empty((height,width,4),dtype=np.uint8)
 nm[:,:,0]=128; nm[:,:,1]=np.clip(128-dy*.36,0,255).astype(np.uint8)
 nm[:,:,2]=255; nm[:,:,3]=np.clip(128-dx*.36,0,255).astype(np.uint8)
 nm=Image.fromarray(nm,'RGBA')
 for name,img in [('albedo',al),('specteam',sp),('normalsTS',nm)]:
  img.save(H/f'UEL0209_{name}.png'); save_dds_dxt5(img,U/f'UEL0209_{name}.dds',independent_channels=True)
if __name__=='__main__':
 U.mkdir(parents=True,exist_ok=True)
 for lod,detail in [(0,16),(1,8)]:
  m=make(detail); write_scm(m,U/f'UEL0209_lod{lod}.scm',N,P,V); print(lod,len(m.vertices),len(m.indices)//3)
 textures()
 for name,a,e in [('front',0,12),('side',90,12),('top',0,85),('perspective',35,28)]: render_scm(U/'UEL0209_lod0.scm',H,H/(name+'.png'),a,e,size=640)
