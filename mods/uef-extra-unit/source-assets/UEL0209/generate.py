from pathlib import Path
import math
from PIL import Image, ImageDraw
from model_geometry import Mesh, render_scm, load_scm
from supcom_binary import write_scm, write_sca, save_dds_dxt5
H=Path(__file__).resolve().parent
U=H.parents[1]/'units'/'UEL0209'
N=['UEL0209','Turret','Turret_Barrel','Recoil_Left','Recoil_Right','Muzzle_Left','Muzzle_Right']
P=[-1,0,1,2,2,3,4]
V=[(0,0,0),(0,.85,-.1),(0,.23,.1),(0,0,0),(0,0,0),(-.42,0,2.37),(.42,0,2.37)]
# Four self-contained caterpillar belts: twelve rigid shoes and four rollers each.
LINKS=12
HALF=.52
RADIUS=.25
TRACK_Y=.30
PATH_LENGTH=4*HALF+2*math.pi*RADIUS
PODS=[(side,zc) for side in (-1,1) for zc in (-.91,.91)]
def track_path(d):
 d=d % PATH_LENGTH
 if d < 2*HALF: return TRACK_Y-RADIUS, HALF-d, 0., -1.
 d-=2*HALF
 if d < math.pi*RADIUS:
  t=d/RADIUS; return TRACK_Y-RADIUS*math.cos(t),-HALF-RADIUS*math.sin(t),math.sin(t),-math.cos(t)
 d-=math.pi*RADIUS
 if d < 2*HALF: return TRACK_Y+RADIUS,-HALF+d,0.,1.
 t=(d-2*HALF)/RADIUS
 return TRACK_Y+RADIUS*math.cos(t),HALF+RADIUS*math.sin(t),-math.sin(t),math.cos(t)
for side,zc in PODS:
 for j in range(LINKS):
  y,z,_,_=track_path(j*PATH_LENGTH/LINKS)
  N.append(f'Track_{len(N):02}'); P.append(0); V.append((side*.77,y,zc+z))
for side,zc in PODS:
 for z in (-.48,-.16,.16,.48):
  N.append(f'Roller_{len(N):02}'); P.append(0); V.append((side*.77,TRACK_Y,zc+z))
assert len(N)==71

def track_shoe(m,x,zc,j,bone):
 y,z,dy,dz=track_path(j*PATH_LENGTH/LINKS); z+=zc
 # tangent follows travel around the capsule; normal points outwards.
 ny,nz=dz,-dy
 length=PATH_LENGTH/LINKS*.80
 rings=[]; centers=[]
 for q in (-1,1):
  cy=y+dy*q*length/2; cz=z+dz*q*length/2
  rings.append([(x+sx*.225,cy+ny*t,cz+nz*t) for sx,t in ((-1,-.025),(1,-.025),(1,.025),(-1,.025))])
  centers.append((x,cy,cz))
 m.loft(rings,centers,bone,'steel')

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
 for pod,(side,zc) in enumerate(PODS):
   x=side*.77
   shifted_chamfer(m,x,[(zc-.80,.19,.18,.46),(zc-.60,.21,.07,.53),(zc+.60,.21,.07,.53),(zc+.80,.19,.18,.46)],'joint')
   for j in range(LINKS): track_shoe(m,x,zc,j,7+pod*LINKS+j)
   for k,z in enumerate((zc-.48,zc-.16,zc+.16,zc+.48)):
    bone=7+len(PODS)*LINKS+pod*4+k
    cylinder(m,x+side*.218,.30,z,.18,.045,'x','dark',bone,n=detail)
    cylinder(m,x+side*.245,.30,z,.132,.025,'x','steel',bone,n=detail)
    cylinder(m,x+side*.261,.30,z,.051,.025,'x','edge',bone,n=detail)
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
 colors=[(33,39,50),(18,22,29),(61,69,81),(42,49,61),(35,42,54),(48,53,61),(120,131,141),(16,18,22)]
 al=Image.new('RGBA',(width,height)); sp=Image.new('RGBA',al.size); relief=Image.new('L',al.size,128)
 da=ImageDraw.Draw(al); ds=ImageDraw.Draw(sp); dh=ImageDraw.Draw(relief)
 for i,c in enumerate(colors):
  x=(i%4)*size; y=(i//4)*size
  da.rectangle((x,y,x+127,y+127),fill=(*c,0))
  ds.rectangle((x,y,x+127,y+127),fill=(49 if i not in (1,7) else 24,55 if i not in (1,7) else 38,0,82 if i==4 else 0))
  # Chamfered panel borders have painted highlights and recessed dark seams.
  if i in (0,2,3,4):
   dark=(12,16,23,0); light=(84,96,113,0) if i!=2 else (112,123,136,0)
   da.rectangle((x+12,y+8,x+116,y+119),outline=dark,width=2)
   da.line((x+15,y+12,x+113,y+12),fill=light,width=1)
   da.line((x+15,y+13,x+15,y+114),fill=light,width=1)
   da.line((x+15,y+116,x+113,y+116),fill=(18,23,32,0),width=2)
   dh.rectangle((x+13,y+9,x+115,y+118),outline=103,width=2)
   # Offset equipment panels and small screws, restrained so that each face
   # remains legible at game zoom despite sharing an atlas tile.
   for px,py in ((20,20),(108,20),(20,108),(108,108)):
    da.ellipse((x+px-2,y+py-2,x+px+2,y+py+2),fill=(28,34,42,0))
    da.point((x+px-1,y+py-1),fill=(98,109,124,0))
   if i in (0,2,3):
    # Offset plate seams, double edge highlights and recessed service fasteners.
    for py in (29,61,95):
     da.line((x+20,y+py,x+107,y+py),fill=(13,18,26,0),width=2)
     da.line((x+20,y+py+2,x+107,y+py+2),fill=(80,91,107,0),width=1)
     dh.line((x+20,y+py,x+107,y+py),fill=104,width=2)
    for px in (30,96):
     for py in (24,54,88,105):
      da.ellipse((x+px-2,y+py-2,x+px+2,y+py+2),fill=(12,17,24,0))
      da.point((x+px-1,y+py-1),fill=(118,130,143,0))
   if i==4:
    # Player paint is a weathered inset rather than a solid neon rectangle.
    ds.rectangle((x+12,y+8,x+116,y+119),outline=(49,55,0,0),width=3)
    ds.line((x+15,y+12,x+113,y+12),fill=(49,55,0,36),width=1)
    for px,py in ((20,20),(108,20),(20,108),(108,108)):
     ds.ellipse((x+px-2,y+py-2,x+px+2,y+py+2),fill=(49,55,0,12))
    for j in range(36):
     px=int(rng.integers(19,110)); py=int(rng.integers(19,110))
     ds.line((x+px,y+py,x+px+int(rng.integers(1,5)),y+py),fill=(49,55,0,int(rng.integers(30,65))),width=1)
   if i==0:
    da.line((x+22,y+77,x+48,y+77,x+58,y+87,x+104,y+87),fill=(18,24,33,0),width=2)
    da.line((x+22,y+79,x+47,y+79),fill=(72,83,99,0),width=1)
   elif i==3:
    for yy in (37,41,45): da.line((x+29,y+yy,x+98,y+yy),fill=(21,27,37,0),width=1)
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
def animation():
 names=[N[0]]+N[7:]; parents=[-1]+[0]*(len(names)-1)
 duration=PATH_LENGTH/2.2; frames=[]; count=65
 for frame in range(count):
  phase=frame/(count-1); poses=[(V[0],(1,0,0,0))]
  for side,zc in PODS:
   for j in range(LINKS):
    d=j*PATH_LENGTH/LINKS
    y0,z0,dy0,dz0=track_path(d); y,z,dy,dz=track_path(d+phase*PATH_LENGTH)
    angle=math.atan2(dz,dy)-math.atan2(dz0,dy0)
    poses.append(((side*.77,y,zc+z),(math.cos(angle/2),math.sin(angle/2),0,0)))
  turns=round(PATH_LENGTH/(2*math.pi*.132)); angle=phase*turns*2*math.pi
  for side,zc in PODS:
   for z in (-.48,-.16,.16,.48): poses.append(((side*.77,TRACK_Y,zc+z),(math.cos(angle/2),math.sin(angle/2),0,0)))
  frames.append(poses)
 for bone in range(1,len(names)):
  for f in range(1,count):
   pos,q=frames[f][bone]; prev=frames[f-1][bone][1]
   if sum(a*b for a,b in zip(q,prev))<0: frames[f][bone]=(pos,tuple(-v for v in q))
 write_sca(U/'UEL0209_tracks.sca',names,parents,frames,duration)
 print('track cycle seconds',duration,'bones',len(names))
if __name__=='__main__':
 U.mkdir(parents=True,exist_ok=True)
 for lod,detail in [(0,16),(1,8)]:
  m=make(detail); write_scm(m,U/f'UEL0209_lod{lod}.scm',N,P,V); print(lod,len(m.vertices),len(m.indices)//3)
 textures()
 animation()
 for name,a,e in [('front',0,12),('side',90,12),('top',0,85),('perspective',35,28)]: render_scm(U/'UEL0209_lod0.scm',H,H/(name+'.png'),a,e,size=640)
