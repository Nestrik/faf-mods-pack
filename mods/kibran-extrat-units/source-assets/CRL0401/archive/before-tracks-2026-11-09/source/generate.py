"""Original Cybran-inspired eight-wheel engineering platform; Y up, +Z forward."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
from model_geometry import Mesh, render_scm, load_scm, load_dds_mip
from supcom_binary import write_scm, save_dds_dxt5

HERE = Path(__file__).resolve().parent
UNIT = HERE.parents[1] / 'units' / 'CRL0401'

def beam(m, start, end, width, height, mat='armor'):
    a,b=np.asarray(start,float),np.asarray(end,float)
    axis=b-a; axis/=np.linalg.norm(axis)
    ref=np.array((0.,1.,0.)) if abs(axis[1]) < .9 else np.array((0.,0.,1.))
    u=np.cross(axis,ref); u/=np.linalg.norm(u); v=np.cross(axis,u)
    rings=[[p+u*width*s+v*height*t for s,t in ((-1,-1),(1,-1),(1,1),(-1,1))] for p in (a,b)]
    m.loft(rings,[a,b],material=mat)

def block(m,x,y,z,sx,sy,sz,mat='armor'):
    rings=[[(x-sx/2,y-sy/2,z+q*sz/2),(x+sx/2,y-sy/2,z+q*sz/2),
            (x+sx/2,y+sy/2,z+q*sz/2),(x-sx/2,y+sy/2,z+q*sz/2)] for q in (-1,1)]
    m.loft(rings,[(x,y,z-sz/2),(x,y,z+sz/2)],material=mat)

def hull(m,sections,mat='armor'):
    # Each cross-section is an octagonal chamfered shell: z, half-width, bottom, top.
    rings=[]; centers=[]
    for z,w,lo,hi in sections:
        c=min(w*.23,(hi-lo)*.28)
        rings.append([(-w+c,lo,z),(w-c,lo,z),(w,lo+c,z),(w,hi-c,z),
                      (w-c,hi,z),(-w+c,hi,z),(-w,hi-c,z),(-w,lo+c,z)])
        centers.append((0,(lo+hi)/2,z))
    m.loft(rings,centers,material=mat)

def wheel(m,side,z,detail):
    x=side*1.19; y=.34; n=detail
    rings=[]; centers=[]
    for dx,r in [(-.22,.27),(-.19,.32),(-.13,.34),(.13,.34),(.19,.32),(.22,.27)]:
        rings.append([(x+dx,y+r*math.cos(2*math.pi*i/n),z+r*math.sin(2*math.pi*i/n)) for i in range(n)])
        centers.append((x+dx,y,z))
    m.loft(rings,centers,material='joint')
    # Hub cap and raised chevron-like segmented tread, visible on each side.
    face=x+side*.225
    n2=max(8,detail//2)
    rings=[]; centers=[]
    for dx,r in [(0,.18),(side*.025,.18),(side*.03,.08)]:
        rings.append([(face+dx,y+r*math.cos(2*math.pi*i/n2),z+r*math.sin(2*math.pi*i/n2)) for i in range(n2)])
        centers.append((face+dx,y,z))
    m.loft(rings,centers,material='steel')
    if detail >= 16:
        for i in range(12):
            a=2*math.pi*i/12; c,s=math.cos(a),math.sin(a)
            beam(m,(x-.15,y+.34*c,z+.34*s),(x+.15,y+.34*c,z+.34*s),.025,.013,'dark')
        for i in range(4):
            a=2*math.pi*i/4
            beam(m,(face+side*.036,y+.095*math.cos(a),z+.095*math.sin(a)),
                 (face+side*.036,y+.155*math.cos(a),z+.155*math.sin(a)),.012,.012,'edge')

def tower(m,detail):
    # Squat base, then a tall swept, chamfered spire in the Hive's style.
    sections=[(.91,.68,.70,.03),(1.15,.64,.62,.00),(1.55,.52,.46,-.07),
              (2.08,.34,.31,-.20),(2.47,.13,.17,-.30),(2.57,.025,.055,-.32)]
    rings=[]; centers=[]
    for y,w,d,z in sections:
        c=min(w,d)*.22
        rings.append([(-w+c,y,z-d),(w-c,y,z-d),(w,y,z-d+c),(w,y,z+d-c),
                      (w-c,y,z+d),(-w+c,y,z+d),(-w,y,z+d-c),(-w,y,z-d+c)])
        centers.append((0,y,z))
    m.loft(rings,centers,material='dark')
    # Sloping front face with three raised triangular panels, separated by armour bands.
    # Front plane interpolates the front edge of the tower sections.
    points=[(1.17,.621),(1.55,.39),(2.08,.11),(2.46,-.13)]
    for i in range(3):
        y0,z0=points[i]; y1,z1=points[i+1]
        mid=y0+(y1-y0)*.13; top=y1-(y1-y0)*.12
        def front(y): return z0+(z1-z0)*(y-y0)/(y1-y0)+.012
        w=(.43,.32,.19)[i]
        vertices=[(-w,mid,front(mid)),(w,mid,front(mid)),(0,top,front(top))]
        m.face(vertices,material='steel',outward=(0,.3,1))
        inset=[(-w*.68,mid+.035,front(mid+.035)+.006),(w*.68,mid+.035,front(mid+.035)+.006),(0,top-.045,front(top-.045)+.006)]
        m.face(inset,material='team',outward=(0,.3,1))
        for j in range(3): beam(m,vertices[j],vertices[(j+1)%3],.015,.012,'edge')
        if detail >= 16:
            # The inner frame and split prongs echo the inset details of Hive.
            ins2=[(-w*.45,mid+.055,front(mid+.055)+.011),(w*.45,mid+.055,front(mid+.055)+.011),(0,top-.085,front(top-.085)+.011)]
            for j in range(3): beam(m,ins2[j],ins2[(j+1)%3],.008,.006,'dark')
            beam(m,(0,mid+.07,front(mid+.07)+.018),(0,top-.11,front(top-.11)+.018),.009,.006,'edge')
    # Large triangular side buttresses and braces make the tower read as Hive.
    for side in (-1,1):
        outer=[(side*.70,1.04,-.53),(side*.70,1.04,.48),(side*.43,1.83,-.19)]
        m.face(outer,material='steel',outward=(side,0,0))
        inner=[(side*.711,1.12,-.39),(side*.711,1.12,.31),(side*.49,1.66,-.17)]
        m.face(inner,material='team',outward=(side,0,0))
        for j in range(3): beam(m,outer[j],outer[(j+1)%3],.03,.025,'edge')
        beam(m,(side*.56,1.18,.49),(side*.115,2.48,-.12),.035,.025,'edge')
        beam(m,(side*.61,1.12,-.5),(side*.13,2.42,-.43),.035,.025,'armor')
        if detail >= 16:
            for y in (1.28,1.42,1.56,1.70):
                z=.59-(y-1.17)*.6
                beam(m,(side*.38,y,z),(side*.47,y,z-.02),.01,.01,'crystal')
            for z in (-.34,-.22,-.10,.02,.14):
                beam(m,(side*.695,1.08,z),(side*.61,1.35,z-.04),.011,.01,'edge')

def model(detail):
    m=Mesh(detail)
    hull(m,[(-1.38,.61,.39,.71),(-1.15,.94,.35,.85),(.83,.94,.35,.83),(1.30,.66,.38,.67),(1.40,.36,.43,.59)],'dark')
    hull(m,[(-1.22,.75,.70,.89),(-.85,.83,.72,1.00),(.70,.81,.72,1.00),(1.18,.54,.68,.87)],'armor')
    for side in (-1,1):
        for z in (-1.00,-.34,.34,1.00): wheel(m,side,z,detail)
        beam(m,(side*.93,.71,-1.22),(side*.93,.71,1.18),.055,.035,'steel')
        beam(m,(side*.92,.87,-1.15),(side*.92,.87,1.10),.035,.02,'team')
        for z in (-.68,.68):
            beam(m,(side*.87,.62,z-.28),(side*1.02,.74,z+.24),.06,.04,'dark')
            block(m,side*.83,.91,z,.22,.07,.36,'edge')
            if detail >= 16:
                beam(m,(side*.90,.78,z-.25),(side*.98,.63,z+.22),.035,.035,'steel')
                beam(m,(side*.90,.78,z-.25),(side*.95,.67,z+.06),.017,.017,'edge')
        beam(m,(side*.66,.83,1.03),(side*.28,.65,1.36),.065,.05,'steel')
        beam(m,(side*.63,.86,-1.08),(side*.80,.99,-1.31),.06,.035,'edge')
        if detail >= 16:
            for z in (-.99,-.33,.33,.99):
                beam(m,(side*.98,.92,z-.24),(side*.98,.92,z+.24),.038,.025,'dark')
                beam(m,(side*.98,.96,z-.20),(side*.98,.96,z+.20),.012,.01,'steel')
            for x in (.26,.37,.48):
                beam(m,(side*x,.88,1.05),(side*(x-.08),.76,1.29),.014,.012,'edge')
            block(m,side*.54,.72,1.28,.15,.07,.05,'lens')
    block(m,0,.94,-1.04,1.05,.16,.38,'dark')
    for x in (-.32,-.16,0,.16,.32):
        block(m,x,1.035,-1.05,.045,.025,.28,'edge')
    tower(m,detail)
    return m

def textures():
    colors=[(72,79,87),(29,34,40),(125,133,143),(89,96,103),
            (95,103,110),(88,27,23),(224,45,20),(31,34,37)]
    al=Image.new('RGBA',(256,128)); spec=Image.new('RGBA',al.size); normal=Image.new('RGBA',al.size,(128,128,255,128))
    da,ds=ImageDraw.Draw(al),ImageDraw.Draw(spec)
    for i,c in enumerate(colors):
        rect=((i%4)*64,(i//4)*64,(i%4+1)*64-1,(i//4+1)*64-1)
        da.rectangle(rect,fill=(*c,0))
        ds.rectangle(rect,fill=(85 if i!=7 else 25,105 if i!=7 else 45,95 if i==6 else 0,255 if i==4 else 0))
    # Small independent-channel surface variation survives mip generation and
    # avoids relying on alpha transparency for the material maps.
    pixels=np.asarray(al).copy(); rng=np.random.default_rng(304309)
    noise=rng.integers(-5,6,(128,256,1),dtype=np.int16)
    pixels[:,:,:3]=np.clip(pixels[:,:,:3].astype(np.int16)+noise,0,255).astype(np.uint8)
    al=Image.fromarray(pixels,'RGBA')
    for name,img in [('albedo',al),('specteam',spec),('normalsTS',normal)]:
        img.save(HERE / ('CRL0401_'+name+'.png'))
        save_dds_dxt5(img,UNIT/('CRL0401_'+name+'.dds'),independent_channels=True)

if __name__ == '__main__':
    UNIT.mkdir(parents=True,exist_ok=True)
    for lod,detail in [(0,24),(1,8)]:
        mesh=model(detail)
        write_scm(mesh,UNIT/f'CRL0401_lod{lod}.scm',['CRL0401','BuildPoint'],[-1,0],[(0,0,0),(0,2.5,0)])
        v,f=load_scm(UNIT/f'CRL0401_lod{lod}.scm')
        print('LOD',lod,'vertices',len(v),'triangles',len(f),'bounds',v[:,:3].min(axis=0),v[:,:3].max(axis=0))
    textures()
    for name,a,e in [('front',0,12),('side',90,12),('top',0,85),('perspective',35,28)]:
        render_scm(UNIT/'CRL0401_lod0.scm',HERE,HERE/(name+'.png'),a,e,player=(.85,.08,.04),size=640)
    render_scm(UNIT/'CRL0401_lod1.scm',HERE,HERE/'lod1.png',35,28,player=(.05,.35,.95),size=480,texture_mip=2)
