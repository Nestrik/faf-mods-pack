from pathlib import Path
import math
from PIL import Image, ImageDraw
from model_geometry import Mesh, render_scm, load_scm
from supcom_binary import write_scm, save_dds_dxt5
H=Path(__file__).resolve().parent
U=H.parents[1]/'units'/'UEL0209'
N=['UEL0209','Turret','Turret_Barrel','Muzzle_Left','Muzzle_Right']
P=[-1,0,1,2,2]
V=[(0,0,0),(0,.85,-.1),(0,.23,.1),(-.42,0,2.37),(.42,0,2.37)]
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
 for x in (-.42,.42):
  shifted_chamfer(m,x,[(.28,.17,.90,1.25),(.56,.18,.90,1.25),(.74,.13,.96,1.19)],'armor',2)
  cylinder(m,x,1.08,1.32,.115,1.25,'z','steel',2,detail)
  for z in (.85,1.25,1.65,1.91): cylinder(m,x,1.08,z,.13,.045,'z','edge',2,detail)
  shifted_chamfer(m,x,[(2.00,.145,.94,1.22),(2.10,.16,.93,1.23),(2.34,.16,.93,1.23)],'dark',2)
  cylinder(m,x,1.08,2.348,.105,.015,'z','joint',2,detail)
  for z in (2.13,2.21,2.29):
   for side in (-1,1): box(m,x+side*.162,1.08,z,.016,.10,.035,'edge',2)
 return m
def textures():
 # Cool blue-gray UEF armor; mask remains in SpecTeam alpha.
 import numpy as np
 colors=[(72,83,101),(25,31,41),(118,129,145),(83,94,110),(73,85,101),(100,104,99),(191,200,199),(24,27,32)]
 al=Image.new('RGBA',(512,256)); sp=Image.new('RGBA',al.size); nm=Image.new('RGBA',al.size,(128,128,255,128)); a=ImageDraw.Draw(al); s=ImageDraw.Draw(sp)
 for i,c in enumerate(colors):
  x=(i%4)*128; y=(i//4)*128; rect=(x,y,x+127,y+127)
  a.rectangle(rect,fill=(*c,0)); s.rectangle(rect,fill=(65 if i not in (1,7) else 30,100 if i not in (1,7) else 55,0,210 if i==4 else 0))
  if i in (0,2,3,4):
   a.line((x+14,y+14,x+113,y+14,x+113,y+113),fill=(48,57,72,0),width=2)
   a.line((x+17,y+18,x+110,y+18),fill=(125,137,153,0),width=1)
   a.line((x+18,y+109,x+110,y+109),fill=(34,42,55,0),width=2)
 arr=np.asarray(al).copy(); rng=np.random.default_rng(20261109)
 noise=rng.integers(-6,7,(256,512,1),dtype=np.int16)
 arr[:,:,:3]=np.clip(arr[:,:,:3].astype(np.int16)+noise,0,255).astype(np.uint8)
 al=Image.fromarray(arr,'RGBA')
 for name,img in [('albedo',al),('specteam',sp),('normalsTS',nm)]:
  img.save(H/f'UEL0209_{name}.png'); save_dds_dxt5(img,U/f'UEL0209_{name}.dds',independent_channels=True)
if __name__=='__main__':
 U.mkdir(parents=True,exist_ok=True)
 for lod,detail in [(0,16),(1,8)]:
  m=make(detail); write_scm(m,U/f'UEL0209_lod{lod}.scm',N,P,V); print(lod,len(m.vertices),len(m.indices)//3)
 textures()
 for name,a,e in [('front',0,12),('side',90,12),('top',0,85),('perspective',35,28)]: render_scm(U/'UEL0209_lod0.scm',H,H/(name+'.png'),a,e,size=640)
