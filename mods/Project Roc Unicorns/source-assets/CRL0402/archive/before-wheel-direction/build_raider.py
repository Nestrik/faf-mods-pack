"""Raider in bind pose. Y is up, positive Z is the bow."""
from pathlib import Path
from math import sin, cos, tau
import numpy as np
from PIL import Image, ImageDraw
from mesh_tools import Mesh, render_scm
from supcom_binary import write_scm, write_sca, save_dds_dxt5

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
UNIT = MOD / 'units/CRL0402'
NAMES, PARENTS, POSITIONS = ['CRL0402'], [-1], [(0, 0, 0)]

def bone(name, parent, position):
    NAMES.append(name)
    PARENTS.append(parent)
    POSITIONS.append(position)
    return len(NAMES)-1

guns = []
for side, x in [('Left', -1.02), ('Right', 1.02)]:
    yaw = bone(side+'Yaw', 0, (x, 1.52, 1.15))
    pitch = bone(side+'Pitch', yaw, (x, 1.83, 1.38))
    bone(side+'Muzzle', pitch, (x, 1.83, 6.45))
    guns.append((x, yaw, pitch))
aa = bone('Turret', 0, (0, 1.86, -2.30))
pods = bone('Turret_Barrel', aa, (0, 2.19, -2.30))
ports = []
for side, sign in [('Left', -1), ('Right', 1)]:
    for i in range(4):
        p = (sign*.62 + ((i%2)-.5)*.27, 2.19+((i//2)-.5)*.22, -1.48)
        ports.append(p)
        bone(f'Turret_{side}_Muzzle{i+1:02}', pods, p)
wheels = [bone(f'Roller_{side}_{i}', 0, (x,.45,z))
          for side,x in [('L',-2.54),('R',2.54)]
          for i,z in enumerate(np.linspace(-2.9,2.9,8))]

def shell(m, sections, x=0, mat='armor', bone=0):
    """Eight-sided transverse sections define the bevels and the prow rake."""
    rings, centers = [], []
    for z,w,lo,hi in sections:
        c=min(w*.38,(hi-lo)*.35)
        rings.append([(x+dx,y,z) for dx,y in [(-w+c,lo),(w-c,lo),(w,lo+c),(w,hi-c),
                                               (w-c,hi),(-w+c,hi),(-w,hi-c),(-w,lo+c)]])
        centers.append((x,(hi+lo)/2,z))
    m.loft(rings, centers, bone, mat)

def plate(m,x,y,z,w,h,d,mat,b=0):
    shell(m,[(z-d/2,w/2,y,y+h),(z+d/2,w/2,y,y+h)],x,mat,b)

def tube(m, center, axis, profile, mat, b=0):
    rings, centers = [], []
    for off,r in profile:
        c=np.array(center,dtype=float)
        c[axis]+=off
        centers.append(c)
        ring=[]
        for t in np.arange(m.detail)*tau/m.detail:
            p=c.copy()
            p[(axis+1)%3]+=r*cos(t)
            p[(axis+2)%3]+=r*sin(t)
            ring.append(p)
        rings.append(ring)
    m.loft(rings,centers,b,mat)

def model(detail):
    m=Mesh(detail)
    shell(m,[(-3.98,1.53,.48,1.07),(-3.5,2.28,.32,1.47),
             (1.9,2.36,.34,1.50),(3.75,1.55,.65,1.03)])
    shell(m,[(-3.86,1.02,1.02,1.42),(-3.34,1.46,1.28,1.88),
             (-1.42,1.38,1.30,1.92),(.80,.88,1.37,1.74),(2.80,.46,1.28,1.51)])
    for s in [-1,1]:
        x=s*2.55
        shell(m,[(-3.73,.42,.37,.78),(-3.22,.57,.04,.93),
                 (3.08,.57,.04,.94),(3.75,.39,.39,.78)],x,'joint')
        for z in np.arange(-3.17,3.22,.30 if detail==12 else .60):
            plate(m,x,.016,z,1.07,.13,.17,'dark')
        for b in wheels:
            c=POSITIONS[b]
            if c[0]*s<0: continue
            tube(m,c,0,[(s*.49,.39),(s*.59,.37),(s*.60,.27)],'steel',b)
            tube(m,c,0,[(s*.60,.15),(s*.63,.12)],'dark',b)
            if detail==12:
                plate(m,c[0]+s*.637,.41,c[2],.016,.08,.24,'edge',b)
        for z in [-1.88,1.79]:
            shell(m,[(z-1.83,.29,.60,1.04),(z-1.37,.85,.57,1.58),
                     (z+.75,.85,.65,1.48),(z+1.93,.22,.72,.84)],x)
            shell(m,[(z-1.29,.64,1.49,1.58),(z-.95,.68,1.50,1.64),
                     (z+.53,.65,1.45,1.55)],x,'steel')
            if detail==12:
                for i in range(6):
                    plate(m,x,1.64,z-.88+i*.13,.75,.025,.055,'joint')
            plate(m,x+s*.62,1.54,z-.62,.10,.04,.57,'team')
            # The narrow diagonal warning bands run along the inner shoulder.
            for j in range(5):
                v=z-.74+j*.21
                xx=x-s*.47
                m.face([(xx-.085,1.649,v),(xx+.085,1.649,v+.09),
                        (xx+.085,1.649,v+.17),(xx-.085,1.649,v+.08)],0,'hazard',(0,1,0))
        # Pointed cheek plates frame the elevated engine spine.
        shell(m,[(-3.48,.20,1.30,1.52),(-2.91,.36,1.34,1.86),
                 (-.37,.33,1.41,1.78),(.29,.06,1.46,1.61)],s*1.62,'dark')
        for j in range(7):
            plate(m,s*.97,1.88,-3.26+j*.12,.53,.06,.06,'joint')
    for x,yaw,pitch in guns:
        tube(m,(x,1.49,1.15),1,[(0,.70),(.19,.68),(.24,.56)],'joint',yaw)
        shell(m,[(-.12,.37,1.63,1.84),(.37,.62,1.57,2.16),
                 (1.46,.58,1.60,2.20),(2.28,.30,1.64,1.98)],x,'armor',yaw)
        tube(m,(x,1.83,0),2,[(1.57,.23),(3.12,.21),(3.28,.135),(6.39,.102),
                                (6.45,.12)],'steel',pitch)
        shell(m,[(1.78,.32,1.57,2.05),(2.85,.31,1.59,2.13),
                 (3.45,.20,1.66,2.0)],x,'dark',pitch)
        for shift in [-.09,.09]:
            plate(m,x+shift,2.132,2.52,.075,.023,.64,'lens',pitch)
        for z in [3.57,4.53,5.54,6.30]:
            tube(m,(x,1.83,z),2,[(0,.146),(.13,.142)],'dark',pitch)
        tube(m,(x,1.83,6.45),2,[(0,.081),(.004,.081)],'lens',pitch)
    tube(m,(0,1.90,-2.3),1,[(-.06,.55),(.09,.60),(.24,.43)],'joint',aa)
    plate(m,0,1.98,-2.30,.58,.43,.76,'steel',aa)
    for sign in [-1,1]:
        shell(m,[(-3.14,.26,2,2.4),(-2.93,.39,1.92,2.51),
                 (-1.49,.37,1.94,2.47)],sign*.62,'armor',pods)
        plate(m,sign*.62,2.51,-2.64,.12,.025,.45,'team',pods)
    for p in ports:
        tube(m,p,2,[(-.015,.113),(.04,.11)],'steel',pods)
        tube(m,p,2,[(.04,.078),(.042,.078)],'joint',pods)
    # Split arrow insignia on the central glacis.
    for sign in [-1,1]:
        m.face([(sign*x,1.755-(z-.72)*.117,z) for x,z in
                [(0,1.43),(.44,.82),(.17,.87),(0,1.20)]],0,'crystal',(0,1,0))
    return m

def textures():
    palette=[(56,58,63),(32,33,37),(99,103,110),(74,76,83),
             (86,86,88),(206,210,212),(208,28,18),(19,20,24)]
    al=Image.new('RGBA',(512,256))
    spec=Image.new('RGBA',al.size)
    da,ds=ImageDraw.Draw(al),ImageDraw.Draw(spec)
    for i,rgb in enumerate(palette):
        x,y=i%4*128,i//4*128
        rect=(x,y,x+127,y+127)
        da.rectangle(rect,fill=rgb+(0,))
        ds.rectangle(rect,fill=(52,85,155 if i==6 else 0,215 if i==4 else 0))
        if i<4:
            da.line([(x+15,y+105),(x+15,y+29),(x+29,y+15),(x+108,y+15),
                     (x+108,y+102),(x+98,y+111),(x+20,y+111)], fill=(31,32,36,0),width=2)
            for u,v in [(21,32),(100,23),(100,98),(22,103)]:
                da.ellipse((x+u-1,y+v-1,x+u+1,y+v+1),fill=(115,118,122,0))
    da.rectangle((240,240,251,251),fill=(176,145,44,0))
    arr=np.asarray(al).copy()
    arr[:,:,:3]=np.clip(arr[:,:,:3].astype(int)+np.random.default_rng(402).integers(-4,5,(256,512,1)),0,255)
    for name,img in [('albedo',Image.fromarray(arr)),('specteam',spec),
                     ('normalsTS',Image.new('RGBA',al.size,(128,128,255,128)))]:
        save_dds_dxt5(img,UNIT/f'CRL0402_{name}.dds',independent_channels=True)

if __name__=='__main__':
    UNIT.mkdir(parents=True,exist_ok=True)
    for lod,detail in enumerate((12,6)):
        mesh=model(detail)
        local=[tuple(np.subtract(p,POSITIONS[parent])) if parent>=0 else p
               for p,parent in zip(POSITIONS,PARENTS)]
        write_scm(mesh,UNIT/f'CRL0402_lod{lod}.scm',NAMES,PARENTS,local)
    frames=[]
    for i in range(17):
        a=-tau*i/16
        frames.append([((0,0,0),(1,0,0,0))]+[(POSITIONS[b],(cos(a/2),sin(a/2),0,0)) for b in wheels])
    write_sca(UNIT/'CRL0402_drive.sca',[NAMES[b] for b in [0]+wheels],[-1]+[0]*len(wheels),frames,1)
    textures()
    views=[]
    for a,e in [(32,38),(-147,50),(0,88)]:
        im=render_scm(UNIT/'CRL0402_lod0.scm',HERE,HERE/'preview.png',a,e,
                      player=(.84,.075,.045),size=480,transparent=True)
        views.append(im)
    sheet=Image.new('RGB',(1440,480),(48,51,57))
    for i,im in enumerate(views):
        sheet.paste(im,(480*i,0),im)
    sheet.save(HERE/'preview.png')
    icon=views[0].crop(views[0].getbbox())
    icon.thumbnail((76,76),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(80,80))
    canvas.paste(icon,((80-icon.width)//2,(80-icon.height)//2))
    for sub in ['icons/units','textures/ui/common/icons/units']:
        (MOD/sub).mkdir(parents=True,exist_ok=True)
        save_dds_dxt5(canvas,MOD/sub/'CRL0402_icon.dds')
