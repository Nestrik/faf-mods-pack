"""Itha-Yen experimental hover tank. Original geometry; Y up, +Z forward.

Run with Python, numpy and Pillow. All game dimensions are source units * 0.1.
The reusable SCM/BC3 writer and rendering primitives are local to this unit.
"""
from pathlib import Path
import math
import json
import struct
import numpy as np
from PIL import Image, ImageDraw
from tank_geometry import Mesh, normalized, make_textures, export_obj, load_scm, load_dds_mip, render_scm
from supcom_binary import write_scm, save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
MOD = ASSETS.parents[1]
UNIT = MOD / 'units/GGA0401'
NAMES = ['GGA0401', 'MainYaw', 'MainPitch', 'MainMuzzle', 'ShieldCore']
PARENTS = [-1, 0, 1, 2, 0]
PIVOTS = [(0,0,0), (0,12,-3), (0,3,0), (0,0,28), (0,10,-19)]
AA_POSITIONS = [(-14,9,14), (14,9,14), (-14,9,-17), (14,9,-17)]
for i, p in enumerate(AA_POSITIONS, 1):
    b = len(NAMES)
    NAMES.extend([f'AA{i}Yaw', f'AA{i}Pitch', f'AA{i}Muzzle'])
    PARENTS.extend([0,b,b+1])
    PIVOTS.extend([p,(0,1.5,0),(0,0,5.2)])


def shell(m, sections, bone=0, material='armor', sides=None):
    n = sides or m.detail
    rings = [[(x+rx*math.cos(a),y+ry*math.sin(a),z)
              for a in np.linspace(0,2*math.pi,n,endpoint=False)]
             for x,y,z,rx,ry in sections]
    m.loft(rings, [(x,y,z) for x,y,z,_,_ in sections], bone, material)


def ovoid(m, center, radii, bone=0, material='armor', stations=13):
    x,y,z = center
    rx,ry,rz = radii
    ts = np.linspace(-.9995,.9995,stations)
    shell(m,[(x,y,z+t*rz,rx*math.sqrt(1-t*t),ry*math.sqrt(1-t*t)) for t in ts],bone,material)


def tube(m, points, radius, bone=0, material='team', sides=6):
    points=np.asarray(points,float)
    rings=[]
    for i,p in enumerate(points):
        axis=normalized(points[min(i+1,len(points)-1)]-points[max(0,i-1)])
        u=normalized(np.cross(axis,(0,1,0) if abs(axis[1])<.95 else (1,0,0)))
        v=np.cross(axis,u)
        rings.append([p+radius*(math.cos(a)*u+math.sin(a)*v)
                      for a in np.linspace(0,2*math.pi,sides,endpoint=False)])
    m.loft(rings,points,bone,material)


def ring(m, center, radius, thickness, bone=0, material='edge', vertical=False):
    x,y,z=center
    points=[]
    for a in np.linspace(0,2*math.pi,m.detail+1):
        points.append((x+radius*math.cos(a), y+radius*math.sin(a) if vertical else y,
                       z if vertical else z+radius*math.sin(a)))
    tube(m,points,thickness,bone,material,8)


def tank(detail):
    m=Mesh(detail)
    # Broad, low central hull and separated crescent-like levitation nacelles.
    ovoid(m,(0,4,0),(12.8,3.8,27),material='dark',stations=17)
    ovoid(m,(0,6.3,-2),(11.5,3.5,24),stations=17)
    for side in (-1,1):
        x=side*14.4
        shell(m,[(side*10,3,-29.5,.16,.2),(side*13.2,3.5,-27.5,3.6,1.5),
                 (x,4,-22,5.4,2.8),(x,4.8,-10,5.6,3.6),
                 (side*14.1,4.8,7,5.7,3.6),(side*12.6,4.4,21,5.0,2.9),
                 (side*9.8,3.8,27.5,2.7,1.6),(side*8.3,3.7,29.5,.15,.2)],material='armor')
        # A second rolled plate gives volume to each outer rim.
        shell(m,[(side*13,3.1,-27,.2,.15),(side*17.3,3.4,-19,1.9,.9),
                 (side*18,3.5,0,1.9,1.2),(side*15.7,3.2,18,1.7,1.0),
                 (side*9.6,3,28,.16,.12)],material='edge')
        tube(m,[(side*11,6,-26),(side*14.1,7.1,-19),(side*14.5,8.1,-7),
                (side*14,8.1,7),(side*11.7,6.8,22),(side*9.2,5.1,28)],.11)
        # Underside lift cells are actual recessed volumes with narrow luminous rims.
        for z in (-19,-5,10,22):
            ovoid(m,(side*13.5,1.7,z),(3.0,.65,3.7),material='joint',stations=9)
            ring(m,(side*13.5,1.2,z),2.2,.16,material='lens')
        ovoid(m,(side*7,9.0,-17),(3.3,2.1,7),material='steel')
    # Central shield generator: three concentric inlays and a floating dark crystal.
    for r in (2.7,3.6,4.5): ring(m,(0,9.7,-19),r,.15,material='team' if r==3.6 else 'edge')
    ovoid(m,(0,11,-19),(1.5,2.4,1.5),4,'crystal')
    # Independent main turret. Wide rear housing, open bifurcated focusing jaws.
    ovoid(m,(0,10.7,-3),(7.9,1.8,8.1),1,'joint')
    ring(m,(0,11.8,-3),6.9,.4,1,'edge')
    ovoid(m,(0,14,-5),(6.8,3.6,8.0),1,'armor')
    ovoid(m,(0,15,-3),(4.1,2.5,6.6),2,'dark')
    for side in (-1,1):
        shell(m,[(side*3,15,-9,.3,.3),(side*4.4,15.5,-5,2.5,2.4),
                 (side*5.2,15.4,2,2.7,2.8),(side*5.4,15.3,10,2.4,2.5),
                 (side*4.8,15.1,17,1.7,1.9),(side*3.6,15,22,.9,1.1),
                 (side*3.2,15,24,.18,.25)],2,'armor')
        tube(m,[(side*4.2,17.7,-4),(side*5.1,18.2,2),(side*5.3,17.9,10),
                (side*4.6,17.1,17),(side*3.5,15.9,22)],.10,2)
    # No solid barrel through the aperture: the charge forms in free space.
    ring(m,(0,15,13),3.4,.48,2,'edge',True)
    ring(m,(0,15,13.2),2.7,.14,2,'lens',True)
    ovoid(m,(0,15,10),(1.6,1.6,1.9),2,'lens')
    # Four independent anti-air mounts; pitch assemblies have their own pivots.
    for i,(x,y,z) in enumerate(AA_POSITIONS):
        yaw=5+i*3; pitch=yaw+1
        ovoid(m,(x,y-.8,z),(3.6,1.0,3.8),material='joint',stations=9)
        ovoid(m,(x,y+.2,z),(3.0,1.7,3.2),yaw,'steel',stations=11)
        for dx in (-1.0,1.0):
            shell(m,[(x+dx,y+1.5,z-1.8,.15,.15),(x+dx,y+1.5,z-1.1,.85,.8),
                     (x+dx,y+1.5,z+2.4,.7,.65),(x+dx,y+1.5,z+5,.3,.35)],pitch,'armor')
            ovoid(m,(x+dx,y+1.5,z+5.05),(.22,.27,.15),pitch,'lens',stations=5)
        tube(m,[(x,y+1.9,z-1),(x,y+2.4,z),(x,y+1.9,z+2)],.10,pitch)
    m.smooth()
    # Weld complete vertex records without merging UV/material/bone boundaries.
    lookup={}; verts=[]; indices=[]
    for index in m.indices:
        v=m.vertices[index]; key=tuple(round(float(x),6) for x in v)
        if key not in lookup: lookup[key]=len(verts); verts.append(v)
        indices.append(lookup[key])
    m.vertices=verts; m.indices=indices
    return m


def main():
    make_textures(ASSETS,UNIT,save_dds_dxt5)
    report={'unit':'GGA0401','game_scale':.1,'lods':[],'mipmaps':{}}
    for lod,detail in enumerate((24,12)):
        m=tank(detail)
        path=UNIT/f'GGA0401_lod{lod}.scm'
        write_scm(m,path,NAMES,PARENTS,PIVOTS)
        v,f=load_scm(path)
        assert np.isfinite(v).all() and f.max()<len(v)
        assert np.max(np.abs(np.linalg.norm(v[:,3:6],axis=1)-1))<1e-5
        assert set(v[:,16].astype(int)) <= set(range(len(NAMES)))
        area=np.linalg.norm(np.cross(v[f[:,1],:3]-v[f[:,0],:3],v[f[:,2],:3]-v[f[:,0],:3]),axis=1)
        assert area.min()>1e-8
        report['lods'].append({'vertices':len(v),'triangles':len(f),'game_bounds':(np.array([v[:,:3].min(0),v[:,:3].max(0)])*.1).tolist()})
        if lod==0: export_obj(m,ASSETS,NAMES)
    # Mesh for the large launched and charging phason sphere, using our lens atlas.
    orb=Mesh(20)
    ovoid(orb,(0,0,0),(6,6,6),0,'lens',stations=17)
    orb.smooth()
    write_scm(orb,MOD/'projectiles/GGP0401/GGP0401_lod0.scm',['GGP0401'],[-1],[(0,0,0)])
    for suffix in ('albedo','specteam','normalsTS'):
        p=UNIT/f'GGA0401_{suffix}.dds'
        values=[]
        for level in range(10):
            a=np.asarray(load_dds_mip(p,level))
            assert a[:,:,:3].max()>0
            values.append([round(float(x),2) for x in a.mean(axis=(0,1))])
        report['mipmaps'][suffix]=values
    for name,az,el in [('game_view',35,38),('front',0,12),('side',90,12),('top',0,88),('rear',155,28)]:
        render_scm(UNIT/'GGA0401_lod0.scm',ASSETS,ASSETS/f'GGA0401_{name}.png',azimuth=az,elevation=el,size=720,texture_mip=1)
    render_scm(UNIT/'GGA0401_lod0.scm',ASSETS,ASSETS/'GGA0401_alt_color.png',azimuth=35,elevation=38,size=720,player=(1,.18,.05),texture_mip=2)
    views=Image.new('RGB',(1440,1440),(24,28,33)); draw=ImageDraw.Draw(views)
    for i,name in enumerate(('game_view','front','side','top')):
        views.paste(Image.open(ASSETS/f'GGA0401_{name}.png'),((i%2)*720,(i//2)*720))
        draw.text(((i%2)*720+20,(i//2)*720+20),f'GGA0401 / {name}',fill=(190,205,215))
    views.save(ASSETS/'GGA0401_views.png')
    icon=render_scm(UNIT/'GGA0401_lod0.scm',ASSETS,ASSETS/'GGA0401_icon_render.png',azimuth=35,elevation=40,size=256,transparent=True).resize((64,64),Image.Resampling.LANCZOS)
    for folder in ('icons/units','textures/ui/common/icons/units'):
        save_dds_dxt5(icon,MOD/folder/'GGA0401_icon.dds')
    icon.save(ASSETS/'GGA0401_icon.png')
    report['bones']=[{'name':n,'parent':p,'local_position':v} for n,p,v in zip(NAMES,PARENTS,PIVOTS)]
    (ASSETS/'export_findings.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['lods']))


if __name__=='__main__': main()
