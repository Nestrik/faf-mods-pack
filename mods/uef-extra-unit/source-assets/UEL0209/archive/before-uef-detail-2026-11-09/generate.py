from pathlib import Path
import math
from PIL import Image, ImageDraw
from model_geometry import Mesh, render_scm, load_scm
from supcom_binary import write_scm, save_dds_dxt5
H=Path(__file__).resolve().parent
U=H.parents[1]/'units'/'UEL0209'
N=['UEL0209','Turret','Turret_Barrel','Muzzle_Left','Muzzle_Right']
P=[-1,0,1,2,2]
V=[(0,0,0),(0,.85,-.1),(0,.23,.1),(-.42,0,2.20),(.42,0,2.20)]
def box(m,x,y,z,sx,sy,sz,mat='armor',bone=0):
 rings=[[(x-sx/2,y-sy/2,z+d*sz/2),(x+sx/2,y-sy/2,z+d*sz/2),(x+sx/2,y+sy/2,z+d*sz/2),(x-sx/2,y+sy/2,z+d*sz/2)] for d in (-1,1)]
 m.loft(rings,[(x,y,z-sz/2),(x,y,z+sz/2)],bone,mat)
def cylinder(m,x,y,z,rad,length,axis,mat,bone=0,n=16):
 rings=[]; centers=[]
 for t in (-length/2,length/2):
  c=(x+t,y,z) if axis=='x' else (x,y,z+t); centers.append(c)
  rings.append([(c[0],y+rad*math.cos(a*2*math.pi/n),z+rad*math.sin(a*2*math.pi/n)) if axis=='x' else (x+rad*math.cos(a*2*math.pi/n),y+rad*math.sin(a*2*math.pi/n),c[2]) for a in range(n)])
 m.loft(rings,centers,bone,mat)
def make(detail):
 m=Mesh(detail)
 # Four separated track pods, two on each side.
 for side in (-1,1):
  for zc in (-.92,.92):
   x=side*.77
   box(m,x,.30,zc,.44,.53,1.65,'joint')
   box(m,x,.59,zc,.47,.13,1.72,'dark')
   for z in [zc-.59,zc-.30,zc,zc+.30,zc+.59]:
    cylinder(m,x+side*.235,.29,z,.19,.03,'x','steel',n=detail)
    cylinder(m,x+side*.255,.29,z,.07,.035,'x','edge',n=detail)
   for z in [zc-.66+i*.165 for i in range(9)]: box(m,x,.04,z,.46,.06,.055,'edge')
 # body, glacis and engine deck
 box(m,0,.48,0,1.27,.63,3.48,'armor')
 box(m,0,.81,-1.04,1.32,.18,1.05,'steel')
 box(m,0,.82,1.12,1.31,.17,1.00,'armor')
 for x in (-.40,-.20,0,.20,.40): box(m,x,.93,-1.09,.08,.05,.70,'dark')
 for x in (-.52,.52): box(m,x,.91,1.20,.12,.06,.60,'team')
 # single traversing turret and shared elevating barrels
 box(m,0,1.04,-.10,1.12,.31,1.22,'dark',1)
 box(m,0,1.22,-.14,1.02,.30,1.08,'armor',1)
 box(m,0,1.40,-.30,.70,.08,.48,'steel',1)
 box(m,0,1.45,-.30,.38,.04,.30,'team',1)
 for x in (-.42,.42):
  cylinder(m,x,1.08,.58,.21,.42,'z','dark',2,detail)
  cylinder(m,x,1.08,1.49,.115,1.65,'z','steel',2,detail)
  cylinder(m,x,1.08,2.22,.16,.24,'z','edge',2,detail)
 return m
def textures():
 colors=[(75,87,75),(29,34,31),(104,110,101),(72,79,71),(70,75,69),(85,90,78),(120,40,25),(24,27,24)]
 al=Image.new('RGBA',(512,256)); sp=Image.new('RGBA',al.size); nm=Image.new('RGBA',al.size,(128,128,255,128)); a=ImageDraw.Draw(al); s=ImageDraw.Draw(sp)
 for i,c in enumerate(colors):
  rect=((i%4)*128,(i//4)*128,(i%4+1)*128-1,(i//4+1)*128-1)
  a.rectangle(rect,fill=(*c,0)); s.rectangle(rect,fill=(45,80,0,220 if i==4 else 0))
 for name,img in [('albedo',al),('specteam',sp),('normalsTS',nm)]:
  img.save(H/f'UEL0209_{name}.png'); save_dds_dxt5(img,U/f'UEL0209_{name}.dds',independent_channels=True)
if __name__=='__main__':
 U.mkdir(parents=True,exist_ok=True)
 for lod,detail in [(0,16),(1,8)]:
  m=make(detail); write_scm(m,U/f'UEL0209_lod{lod}.scm',N,P,V); print(lod,len(m.vertices),len(m.indices)//3)
 textures()
 for name,a,e in [('front',0,12),('side',90,12),('top',0,85),('perspective',35,28)]: render_scm(U/'UEL0209_lod0.scm',H,H/(name+'.png'),a,e,size=640)
