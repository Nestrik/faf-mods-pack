"""Itha-Vael: five detached, rounded leaves from the user's pencil drawing.

Y up, +Z forward, scale 0.1. Exports SCM, DDS, OBJ and SCM/DDS previews.
All helpers are project-owned copies local to this unit. No ImageGen geometry.
"""
from pathlib import Path
import argparse
import json
import math
import struct
import numpy as np
from PIL import Image, ImageDraw
from vael_geometry import Mesh, normalized, make_textures, export_obj, load_scm, load_dds_mip, render_scm
from supcom_binary import write_scm, save_dds_dxt5

SOURCE = Path(__file__).resolve().parent
MOD = SOURCE.parents[1]
UNIT = MOD / 'units/GGA0403'
NAMES = ['GGA0403', 'MainYaw', 'MainPitch', 'MainMuzzle', 'ShieldCore',
         'PortHull', 'StarboardFore', 'StarboardAft', 'AftShard']
PARENTS = [-1, 0, 1, 2, 0, 0, 0, 0, 0]
PIVOTS = [(0,0,0), (0,10,-2), (0,2,0), (0,0,27), (0,7,-15),
          (-14,5,11), (14,5,17), (14,5,-13), (-14,5,-22)]
AA_POSITIONS = [(-15.1,7.9,13), (14,7.7,19), (-14,7.4,-23), (15.3,8.1,-10)]
AA_HULLS = [5,6,8,7]
for i, p in enumerate(AA_POSITIONS, 1):
    yaw = len(NAMES)
    NAMES.extend([f'AA{i}Yaw', f'AA{i}Pitch', f'AA{i}Muzzle'])
    parent = AA_HULLS[i-1]
    PARENTS.extend([parent,yaw,yaw+1])
    PIVOTS.extend([tuple(np.asarray(p)-PIVOTS[parent]), (0,.65,0), (0,0,2.6)])


def curve(points, subdivisions, closed=False):
    p = np.asarray(points,float)
    result = []
    for i in range(len(p) if closed else len(p)-1):
        a = p[(i-1)%len(p)] if closed else p[max(0,i-1)]
        b, c = p[i], p[(i+1)%len(p)]
        d = p[(i+2)%len(p)] if closed else p[min(len(p)-1,i+2)]
        for t in np.linspace(0,1,subdivisions,endpoint=False):
            result.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    if not closed: result.append(p[-1])
    return np.asarray(result)


def tube(m, points, radius, bone=0, material='team', sides=6):
    points = np.asarray(points,float)
    rings = []
    for i,p in enumerate(points):
        axis = normalized(points[min(i+1,len(points)-1)]-points[max(i-1,0)])
        u = normalized(np.cross(axis,(0,1,0) if abs(axis[1])<.95 else (1,0,0)))
        v = np.cross(axis,u)
        rings.append([p+radius*(math.cos(a)*u+math.sin(a)*v)
                      for a in np.linspace(0,2*math.pi,sides,endpoint=False)])
    m.loft(rings,points,bone,material)


def ring(m, x, y, z, radius, bone=0, material='team', width=.075, vertical=False):
    points = [(x+radius*math.cos(a), y+radius*math.sin(a) if vertical else y,
               z if vertical else z+radius*math.sin(a))
              for a in np.linspace(0,2*math.pi,m.detail+1)]
    tube(m,points,width,bone,material)


def ellipsoid(m, center, radii, bone=0, material='steel'):
    x,y,z = center
    rx,ry,rz = radii
    rings=[]; centers=[]
    for t in np.linspace(-.999,.999,9 if m.detail>=20 else 6):
        r=math.sqrt(1-t*t)
        rings.append([(x+rx*r*math.cos(a), y+ry*r*math.sin(a), z+rz*t)
                      for a in np.linspace(0,2*math.pi,m.detail,endpoint=False)])
        centers.append((x,y,z+rz*t))
    m.loft(rings,centers,bone,material)


def plate(m, outline, center, top, thickness, bone=0, trim=True):
    """Closed cambered shell with a rolled edge, not an extruded flat polygon."""
    contour=curve(outline,5 if m.detail>=20 else 3,True)
    center=np.asarray(center,float)
    mid=top-thickness/2
    profile=[(.035,top),(.38,top-.015),(.74,top-.12),(.89,top-.30),
             (.97,mid+.24),(1,mid+.04),(.995,mid-.20),(.94,top-thickness+.12),
             (.72,top-thickness),(.035,top-thickness)]
    rings=[]
    for scale,y in profile:
        points=center+(contour-center)*scale
        rings.append([(x,y,z) for x,z in points])
    for k in range(len(rings)-1):
        for j in range(len(contour)):
            jj=(j+1)%len(contour)
            points=[rings[k][j],rings[k][jj],rings[k+1][jj],rings[k+1][j]]
            mean=np.mean(points,axis=0)
            outward=(0,1,0) if k<4 else ((0,-1,0) if k>=7 else (mean[0]-center[0],0,mean[2]-center[1]))
            material='armor' if k<3 else ('edge' if k<6 else 'dark')
            m.face(points,bone,material,outward,
                   [((p[0]-center[0])/35+.5,(p[2]-center[1])/65+.5) for p in points])
    for index,normal in ((0,(0,1,0)),(-1,(0,-1,0))):
        for j in range(len(contour)):
            m.face([(center[0],profile[index][1],center[1]),rings[index][j],rings[index][(j+1)%len(contour)]],
                   bone,'armor' if index==0 else 'dark',normal)
    if trim:
        points=center+(contour-center)*.87
        tube(m,[(x,top-.23,z) for x,z in np.vstack((points,points[:1]))],.065,bone,'team')


def build(detail):
    m=Mesh(detail)
    # Fore is +Z. Four curved islands surround the central almond, with open
    # diagonal cuts. There are no bridges or hidden supporting slab in the gaps.
    plate(m,[(0,24),(-5,19),(-9.1,8),(-9.4,-3),(-6.4,-16),(0,-23),
             (5.8,-16),(9.2,-4),(9,8),(5,19)],(0,0),7.4,3.1)
    plate(m,[(-4.7,28),(-10.8,29),(-16.2,23),(-19,12),(-19.2,-3),
             (-15.2,1),(-12.9,10),(-9.2,21)],(-14,13),7.5,2.8,5)
    plate(m,[(4.9,28.2),(10.9,28.8),(16.2,24.7),(19.2,17),
             (19.4,8),(15.8,10.3),(12.4,18.7),(8.9,24.6)],(14.3,21),7.3,2.6,6)
    plate(m,[(18.6,3.5),(19.3,-7),(17.5,-18),(12.9,-26.1),(5.2,-29.1),
             (3.7,-25),(9.2,-20.8),(12.3,-13.2),(13.3,-3.2)],(14,-13),7.7,2.8,7)
    plate(m,[(-12.9,-10.8),(-17.7,-15.6),(-19.2,-24.6),(-12.7,-29),
             (-4.8,-27.5),(-6.8,-23),(-11,-18.8)],(-13.3,-23.3),7,2.5,8)
    # Graphic circles and crossing double veins in the sketch become real
    # rounded inlays; the atlas adds restrained smaller crop-circle etching.
    for x,y,z,r,b in [(-14.9,7.56,13,2.1,5),(14.1,7.38,19,1.9,6),
                       (15.3,7.79,-10,1.65,7),(-14,7.11,-23,2.2,8),
                       (10.8,7.79,-22,1.1,7),(0,7.48,-15,2.0,0)]:
        ring(m,x,y,z,r,b,'dark',.18)
        ring(m,x,y+.1,z,r,b,'team',.08)
        ring(m,x,y+.1,z,r+.33,b,'edge',.075)
    for points,bone,top in [([(-18,0),(-15.2,10),(-10,23),(-8,27)],5,7.5),
                            ([(6.8,27),(12.5,23),(18,17)],6,7.3),
                            ([(17.9,0),(15,-9),(10.4,-24)],7,7.7),
                            ([(-18,-24),(-13.5,-22),(-8,-26)],8,7)]:
        for dx in (-.16,.16):
            tube(m,curve([(x+dx,top+.055,z) for x,z in points],4),.055,bone)
    # Main weapon is a low, leaf-shaped rotating dorsal assembly, so the
    # silhouette stays close to the drawing. All aiming bones remain native.
    ellipsoid(m,(0,9,-2),(5.3,1.3,8),1,'joint')
    plate(m,[(0,19),(-3.8,12),(-6.1,2),(-5.1,-9),(0,-14),
             (5.1,-9),(6.1,2),(3.8,12)],(0,1),12.8,3.5,2)
    for side in (-1,1):
        ellipsoid(m,(side*1.8,12,19.7),(.85,.9,5.1),2,'edge')
        tube(m,[(side*1.8,12.8,16),(side*1.8,12.8,21),(side*1.8,12.3,24.1)],.08,2)
    ring(m,0,12,23,1.18,2,'edge',.22,True)
    ring(m,0,12,23.1,.88,2,'lens',.105,True)
    ellipsoid(m,(0,12,21.8),(.65,.65,.5),2,'lens')
    ring(m,0,12.91,-4,2.05,2,'team',.075)
    ring(m,0,12.91,-4,2.48,2,'edge',.08)
    for side in (-1,1):
        tube(m,[(side*.18,12.86,-1.9),(side*.18,12.86,1),
                (side*3.1,12.86,5.5),(side*2.7,12.86,9.5)],.055,2)
        ring(m,side*3.1,12.88,5.5,.65,2,'team',.055)
    tube(m,[(0,12.86,-6.5),(0,12.86,-10.3)],.055,2)
    # Shield lens is a flush rear circular node; AA mounts occupy the four
    # circular island hardpoints and move with those islands.
    ellipsoid(m,(0,7.7,-15),(1.4,.5,1.4),4,'lens')
    for i,(x,y,z) in enumerate(AA_POSITIONS):
        yaw=9+i*3; pitch=yaw+1
        ellipsoid(m,(x,y-.1,z),(1.6,.48,1.6),AA_HULLS[i],'joint')
        ellipsoid(m,(x,y+.35,z),(1.35,.7,1.55),yaw,'steel')
        for dx in (-.5,.5):
            ellipsoid(m,(x+dx,y+.65,z+.8),(.32,.35,1.75),pitch,'edge')
            ellipsoid(m,(x+dx,y+.65,z+2.55),(.20,.20,.1),pitch,'lens')
        tube(m,[(x,y+1.05,z-.6),(x,y+1.05,z+.8)],.065,pitch)
    m.smooth()
    lookup={}; vertices=[]; indices=[]
    for index in m.indices:
        v=m.vertices[index]; key=tuple(round(float(x),6) for x in v)
        if key not in lookup: lookup[key]=len(vertices); vertices.append(v)
        indices.append(lookup[key])
    m.vertices=vertices; m.indices=indices
    return m


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-textures',action='store_true')
    parser.add_argument('--skip-previews',action='store_true')
    args=parser.parse_args()
    if not args.skip_textures: make_textures(SOURCE,UNIT,save_dds_dxt5)
    report={'unit':'GGA0403','scale':.1,'lods':[],'mipmaps':{},'game_tested':False}
    for lod,detail in enumerate((24,12)):
        mesh=build(detail); target=UNIT/f'GGA0403_lod{lod}.scm'
        write_scm(mesh,target,NAMES,PARENTS,PIVOTS)
        v,f=load_scm(target)
        assert np.isfinite(v).all() and f.max()<len(v)<65536
        assert np.max(np.abs(np.linalg.norm(v[:,3:6],axis=1)-1))<1e-5
        assert np.max(np.abs(np.sum(v[:,3:6]*v[:,6:9],axis=1)))<1e-5
        area=np.linalg.norm(np.cross(v[f[:,1],:3]-v[f[:,0],:3],v[f[:,2],:3]-v[f[:,0],:3]),axis=1)
        assert area.min()>1e-8
        raw=target.read_bytes(); h=struct.unpack_from('<4s11I',raw)
        assert h[:2]==(b'MODL',5) and h[3]==len(NAMES)
        for i,(name,parent,pivot) in enumerate(zip(NAMES,PARENTS,PIVOTS)):
            bone=struct.unpack_from('<16f3f4f4i',raw,h[2]+i*108)
            assert raw[bone[23]:].split(b'\0')[0].decode()==name
            assert bone[24]==parent and np.allclose(bone[16:19],pivot)
        report['lods'].append({'vertices':len(v),'triangles':len(f),
                              'bounds_game':(np.array([v[:,:3].min(0),v[:,:3].max(0)])*.1).tolist()})
        if lod==0: export_obj(mesh,SOURCE,NAMES)
    for suffix in ('albedo','specteam','normalsTS'):
        means=[]
        for level in range(10):
            a=np.asarray(load_dds_mip(UNIT/f'GGA0403_{suffix}.dds',level))
            assert a[:,:,:3].max()>0
            if suffix=='specteam': assert a[:,:,3].max()==0
            means.append(np.round(a.mean(axis=(0,1)),2).tolist())
        report['mipmaps'][suffix]=means
    report['bones']=[{'name':n,'parent':p,'local_position':list(map(float,v))} for n,p,v in zip(NAMES,PARENTS,PIVOTS)]
    (SOURCE/'export_findings.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['lods']),flush=True)
    if args.skip_previews: return
    for name,az,el in [('game_view',35,43),('front',0,12),('side',90,12),('top',180,88),('rear',155,28)]:
        render_scm(UNIT/'GGA0403_lod0.scm',SOURCE,SOURCE/f'GGA0403_{name}.png',azimuth=az,elevation=el,size=720,texture_mip=1)
        print('Rendered '+name,flush=True)
    render_scm(UNIT/'GGA0403_lod0.scm',SOURCE,SOURCE/'GGA0403_alt_color.png',azimuth=35,elevation=43,size=720,texture_mip=2,player=(1,.18,.05))
    render_scm(UNIT/'GGA0403_lod0.scm',SOURCE,SOURCE/'GGA0403_hull_top.png',azimuth=180,elevation=88,size=720,texture_mip=1,bones=(0,4,5,6,7,8))
    sheet=Image.new('RGB',(1440,1440),(24,28,33)); draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(('game_view','top','front','side')):
        xy=((i%2)*720,(i//2)*720)
        sheet.paste(Image.open(SOURCE/f'GGA0403_{name}.png'),xy)
        draw.text((xy[0]+20,xy[1]+20),'GGA0403 / '+name,fill=(190,205,215))
    sheet.save(SOURCE/'GGA0403_views.png')
    icon=render_scm(UNIT/'GGA0403_lod0.scm',SOURCE,SOURCE/'GGA0403_icon_render.png',azimuth=35,elevation=43,size=256,texture_mip=0,transparent=True).resize((64,64),Image.Resampling.LANCZOS)
    for folder in ('icons/units','textures/ui/common/icons/units'):
        save_dds_dxt5(icon,MOD/folder/'GGA0403_icon.dds')
    icon.save(SOURCE/'GGA0403_icon.png')


if __name__=='__main__': main()
