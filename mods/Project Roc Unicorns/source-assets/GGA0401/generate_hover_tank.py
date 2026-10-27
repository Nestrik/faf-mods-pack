"""Itha-Yen experimental hover tank. Original geometry; Y up, +Z forward.

Run with Python, numpy and Pillow. All game dimensions are source units * 0.1.
The reusable SCM/BC3 writer and rendering primitives are local to this unit.
"""
from pathlib import Path
import math
import json
import struct
import argparse
import numpy as np
from PIL import Image, ImageDraw
from tank_geometry import Mesh, normalized, make_textures, export_obj, load_scm, load_dds_mip, render_scm
from supcom_binary import write_scm, save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
MOD = ASSETS.parents[1]
UNIT = MOD / 'units/GGA0401'
NAMES = ['GGA0401', 'MainYaw', 'MainPitch', 'MainMuzzle', 'ShieldCore',
         'PortHull', 'StarboardFore', 'StarboardAft', 'AftShard']
PARENTS = [-1, 0, 1, 2, 0, 0, 0, 0, 0]
PIVOTS = [(0,0,0), (0,12,-3), (0,3,0), (0,0,28), (0,10,-19),
          (-14,5,0), (14,5,10), (13,5,-18), (-4,6,-24)]
AA_POSITIONS = [(-13.5,9,14), (14,10,8), (-14,9,-17), (13,9,-14)]
AA_HULLS = [5,6,5,7]
for i, p in enumerate(AA_POSITIONS, 1):
    b = len(NAMES)
    NAMES.extend([f'AA{i}Yaw', f'AA{i}Pitch', f'AA{i}Muzzle'])
    hull = AA_HULLS[i-1]
    PARENTS.extend([hull,b,b+1])
    PIVOTS.extend([tuple(float(v) for v in np.asarray(p)-PIVOTS[hull]),(0,1.5,0),(0,0,5.2)])


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
    if len(points)<2: return
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


def interpolate(points, subdivisions):
    """Centrally sampled Catmull-Rom path with exact endpoint positions."""
    points=np.asarray(points,float)
    result=[]
    for i in range(len(points)-1):
        a,b,c,d=points[max(0,i-1)],points[i],points[i+1],points[min(len(points)-1,i+2)]
        for t in np.linspace(0,1,subdivisions,endpoint=False):
            result.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    result.append(points[-1])
    return np.asarray(result)


def ship_leaf(m, sections, bone=0, trim=True, material='armor'):
    """Cambered, rolled ship plate. Dark underside, silver upper armor.

    A closed rounded section provides real edge thickness and continuous normals;
    separate leaves have no hidden connecting slab beneath their open gaps.
    """
    profile=interpolate(sections,3 if m.detail>=20 else 1)
    sides=16 if m.detail>=20 else 10
    rings=[]
    for x,y,z,w,h in profile:
        w,h=max(.08,w),max(.08,h)
        rings.append([(x+w*math.cos(a),y+h*math.sin(a),z)
                      for a in np.linspace(0,2*math.pi,sides,endpoint=False)])
    finishes=[material if math.sin((j+.5)*2*math.pi/sides)>0 else 'dark' for j in range(sides)]
    m.loft(rings,profile[:,:3],bone,material,sides=finishes)
    if trim:
        # Crisp physical inlays follow each upper shoulder instead of relying
        # on a stretched texture stroke across the entire hull.
        for side in (-1,1):
            path=[(x+side*w*.87,y+h*.53+.025,z) for x,y,z,w,h in profile[1:-1]]
            tube(m,path,.075,bone,'team',6)
        ridge=[(x,y+h+.035,z) for x,y,z,w,h in profile[2:-2]]
        tube(m,ridge,.065,bone,'edge',6)


def sail(m, x, z, height, lean, bone):
    """A volume-rounded swept open fin, like the ship's detached arches."""
    outline=[(x,6,z+4),(x-.3,8,z+3.6),(x+lean*.4,height*.72,z+.7),
             (x+lean,height,z-3.8),(x+lean*.8,height-1.3,z-5.2),
             (x+lean*.1,9,z-3.2),(x,6,z+4)]
    path=interpolate(outline,4 if m.detail>=20 else 2)
    tube(m,path,.58,bone,'steel',10 if m.detail>=20 else 6)
    # Raised player-color vein on the outer face of the open loop.
    tube(m,[(px+.43,py,pz) for px,py,pz in path],.085,bone,'team',6)
    ship_leaf(m,[(x-.1,7,z+3.5,.18,.25),(x+.15,8,z+2,1.0,.55),
                 (x+.3,8,z-.5,1.35,.65),(x,7,z-3.3,.12,.12)],bone,trim=False,material='edge')


def tank(detail):
    m=Mesh(detail)
    # Narrow curved central keel. Its prow sweeps to starboard and the stern
    # sweeps to port: this is deliberately not a mirrored three-pod tank.
    ship_leaf(m,[(-3,4,-29.5,.12,.15),(-2,4.2,-25,2.8,1.3),
                 (-1.2,5.1,-17,5.3,2.1),(0,5.5,-6,6.2,2.5),
                 (.4,5.3,5,5.5,2.3),(1.4,4.7,17,4.1,1.6),
                 (3.1,4.6,25,2.1,.9),(4.4,4.8,29.5,.12,.13)])
    # Main port section: one long swept island with a continuous empty channel
    # between it and the central keel. All its turrets move with this island.
    ship_leaf(m,[(-10,4,-29,.13,.13),(-12.5,4.8,-24,3,1.3),
                 (-14.5,5,-17,4.5,2),(-15,5,-8,4.4,1.8),
                 (-14.7,5,2,4.4,1.7),(-13.8,5.5,13,4.3,1.9),
                 (-11.5,6,21,2.3,1.1),(-9.8,6.6,26,.12,.14)],5)
    # Starboard side is split into two shorter islands, at different heights,
    # with a diagonal opening between them rather than a duplicated port hull.
    ship_leaf(m,[(15,4.4,-3,.12,.14),(15.1,4.8,1,3.8,1.5),
                 (14.6,5.2,8,4.8,2.0),(13.4,5.2,17,4.0,1.8),
                 (10.9,5.3,25,2.6,1.2),(8.6,5.6,29,.12,.14)],6)
    ship_leaf(m,[(8,5.4,-29,.12,.14),(12.1,5.9,-26,3.4,1.5),
                 (14.7,6.2,-19,4.4,2),(14.5,6.4,-13,4.0,1.8),
                 (12.5,6.5,-7,1.7,.9),(11.8,6.6,-5,.12,.12)],7)
    # A detached aft dorsal plate, deliberately offset from the centerline.
    ship_leaf(m,[(-5,8.5,-28,.1,.12),(-4.8,9,-25,2.2,.9),
                 (-4,9.6,-22,2.5,.9),(-2.6,9.5,-18,1.7,.65),
                 (-1.8,8.8,-15,.1,.12)],8)
    # Thin exterior shards and three unequal open fins echo the naval reference.
    ship_leaf(m,[(-18.9,3.8,-5,.1,.1),(-19.1,4.3,-1,.7,.5),
                 (-18.7,4.8,4,.7,.45),(-17.4,5.2,8,.1,.1)],5,trim=True,material='steel')
    ship_leaf(m,[(18.7,7,-8,.1,.1),(19.2,7.3,-4,.6,.4),
                 (18.8,7.5,0,.6,.4),(17.8,7.4,3,.1,.1)],7,trim=True,material='steel')
    sail(m,-17.1,-19,18.8,-.7,5)
    sail(m,17.1,-18,16.2,.5,7)
    sail(m,17.6,14,14.8,.2,6)
    # Small levitation lenses live underneath each island, not on a common slab.
    for x,y,z,bone in [(-14,3.1,-16,5),(-14,3.1,12,5),(14.3,3.2,9,6),(13.6,4.3,-18,7)]:
        ovoid(m,(x,y,z),(1.7,.35,2.5),bone,'joint',stations=7)
        ring(m,(x,y-.25,z),1.25,.10,bone,'lens')
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
        yaw=9+i*3; pitch=yaw+1
        ovoid(m,(x,y-.8,z),(3.6,1.0,3.8),AA_HULLS[i],'joint',stations=9)
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
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-textures',action='store_true')
    parser.add_argument('--skip-previews',action='store_true')
    args=parser.parse_args()
    if not args.skip_textures: make_textures(ASSETS,UNIT,save_dds_dxt5)
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
    report['bones']=[{'name':n,'parent':p,'local_position':list(v)} for n,p,v in zip(NAMES,PARENTS,PIVOTS)]
    (ASSETS/'export_findings.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['lods']),flush=True)
    if args.skip_previews: return
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


if __name__=='__main__': main()
