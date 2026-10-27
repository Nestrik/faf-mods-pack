"""Itha-Suun: original geometry from the user's annotated pencil concept.

Y up, +Z forward, 0.1 game scale. No stock geometry or original-unit imports.
"""
from pathlib import Path
import argparse
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from concept_geometry import Mesh, normalized, make_textures, export_obj, load_scm, load_dds_mip, render_scm
from supcom_binary import write_scm, save_dds_dxt5

SOURCE=Path(__file__).resolve().parent
MOD=SOURCE.parents[1]
UNIT=MOD/'units/GGA0402'
NAMES=['GGA0402','MainForeYaw','MainForePitch','MainForeMuzzle',
       'MainAftYaw','MainAftPitch','MainAftMuzzle','ShieldCore',
       'ForeLeftShard','PortIsland','PortAftIsland','StarboardTip']
PARENTS=[-1,0,1,2,0,4,5,0,0,0,0,0]
PIVOTS=[(0,0,0),(0,12,10),(0,3,0),(0,0,11.5),
        (0,18,-9),(0,3,0),(0,0,11.5),(5,8,-23),
        (-11,5,22),(-15,5,-1),(-10,5,-17),(17,6,3)]
AA_POSITIONS=[(10.3,9,17),(-15,9,-1),(10.7,9,0),(-9.8,9,-17)]
AA_HULLS=[0,9,0,10]
AA_BONES=[]
for i,position in enumerate(AA_POSITIONS,1):
    yaw=len(NAMES); AA_BONES.append(yaw)
    NAMES.extend([f'AA{i}Yaw',f'AA{i}Pitch',f'AA{i}Muzzle'])
    parent=AA_HULLS[i-1]
    PARENTS.extend([parent,yaw,yaw+1])
    PIVOTS.extend([tuple(float(x) for x in np.asarray(position)-PIVOTS[parent]),(0,1.5,0),(0,0,4.7)])


def path(points, detail):
    points=np.asarray(points,float); result=[]
    for i in range(len(points)-1):
        a,b,c,d=points[max(i-1,0)],points[i],points[i+1],points[min(i+2,len(points)-1)]
        for t in np.linspace(0,1,detail,endpoint=False):
            result.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return np.asarray(result+[points[-1]])


def tube(mesh, points, radius, bone=0, material='team', sides=6):
    points=np.asarray(points,float)
    if len(points)<2:return
    rings=[]
    for i,p in enumerate(points):
        axis=normalized(points[min(i+1,len(points)-1)]-points[max(i-1,0)])
        u=normalized(np.cross(axis,(0,1,0) if abs(axis[1])<.95 else (1,0,0)))
        v=np.cross(axis,u)
        rings.append([p+radius*(u*math.cos(a)+v*math.sin(a)) for a in np.linspace(0,2*math.pi,sides,endpoint=False)])
    mesh.loft(rings,points,bone,material)


def leaf(mesh, sections, bone=0, material='armor', trim=True, subdivisions=None):
    profile=path(sections,subdivisions or (3 if mesh.detail>=20 else 1))
    sides=16 if mesh.detail>=20 else 10
    rings=[]
    for x,y,z,w,h in profile:
        rings.append([(x+max(.08,w)*math.cos(a),y+max(.08,h)*math.sin(a),z)
                      for a in np.linspace(0,2*math.pi,sides,endpoint=False)])
    finishes=[material if j<sides//2 else 'dark' for j in range(sides)]
    mesh.loft(rings,profile[:,:3],bone,material,sides=finishes)
    if trim:
        for side in (-1,1):
            tube(mesh,[(x+side*w*.86,y+h*.55+.025,z) for x,y,z,w,h in profile[1:-1]],.075,bone)


def ovoid(mesh, center, radii, bone=0, material='armor', stations=11):
    x,y,z=center;rx,ry,rz=radii
    sections=[(x,y,z+t*rz,rx*math.sqrt(1-t*t),ry*math.sqrt(1-t*t)) for t in np.linspace(-.999,.999,stations)]
    leaf(mesh,sections,bone,material,False,subdivisions=1)


def ring(mesh, center, radius, thickness, bone=0, material='edge', vertical=False):
    x,y,z=center
    points=[(x+radius*math.cos(a),y+radius*math.sin(a) if vertical else y,z if vertical else z+radius*math.sin(a))
            for a in np.linspace(0,2*math.pi,mesh.detail+1)]
    tube(mesh,points,thickness,bone,material,8)


def rounded_outline(points, radius=.20, steps=3):
    """Preserve designed concave notches; round their corners in real geometry."""
    points=np.asarray(points,float)
    area=np.sum(points[:,0]*np.roll(points[:,1],-1)-points[:,1]*np.roll(points[:,0],-1))
    if area<0:points=points[::-1]
    out=[]
    for i,p in enumerate(points):
        a=points[i-1]-p;b=points[(i+1)%len(points)]-p
        da,db=np.linalg.norm(a),np.linalg.norm(b)
        distance=min(radius,da*.22,db*.22)
        begin=p+a/da*distance;end=p+b/db*distance
        for t in np.linspace(0,1,steps,endpoint=False):
            out.append(begin*(1-t)**2+2*p*t*(1-t)+end*t*t)
    return np.asarray(out)


def triangulate_polygon(poly):
    """Ear clipping, required for the new stepped/concave armor contours."""
    remaining=list(range(len(poly)));triangles=[]
    def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])
    while len(remaining)>3:
        for k,b in enumerate(remaining):
            a,c=remaining[k-1],remaining[(k+1)%len(remaining)]
            pa,pb,pc=poly[[a,b,c]]
            if cross(pb-pa,pc-pb)<=1e-10:continue
            blocked=False
            for other in remaining:
                if other in (a,b,c):continue
                p=poly[other]
                if min(cross(pb-pa,p-pa),cross(pc-pb,p-pb),cross(pa-pc,p-pc))>=-1e-10:
                    blocked=True;break
            if not blocked:
                triangles.append((a,b,c));remaining.pop(k);break
        else:raise ValueError('Invalid armor contour: no triangulation ear')
    triangles.append(tuple(remaining))
    return triangles


def armor_panel(mesh, outline, y, thickness=.85, bone=0, material='armor', trim=True, corner_radius=.20):
    """Closed cambered armor, with a rolled bevel and a properly capped concave top."""
    p=rounded_outline(outline,corner_radius,3 if mesh.detail>=20 else 2)
    center=p.mean(0);rings=[]
    for scale,height in [(.96,-.5),(.985,-.42),(1,-.20),(1,.19),(.985,.40),(.96,.5)]:
        q=center+(p-center)*scale
        rings.append([(x,y+thickness*height+.10*math.sin(z*.22),z) for x,z in q])
    for level in range(len(rings)-1):
        finish='dark' if level==0 else ('steel' if level==1 else material)
        for i in range(len(p)):
            j=(i+1)%len(p);dx,dz=p[j]-p[i]
            mesh.face([rings[level][i],rings[level][j],rings[level+1][j],rings[level+1][i]],bone,finish,
                      outward=(dz,0,-dx),uvs=[(i/len(p),level/5),(j/len(p),level/5),(j/len(p),(level+1)/5),(i/len(p),(level+1)/5)])
    uv=(p-p.min(0))/np.maximum(np.ptp(p,axis=0),1e-6)
    for face in triangulate_polygon(p):
        mesh.face([rings[-1][i] for i in face],bone,material,outward=(0,1,0),uvs=[tuple(uv[i]) for i in face])
        mesh.face([rings[0][i] for i in face],bone,'dark',outward=(0,-1,0),uvs=[tuple(uv[i]) for i in face])
    if trim:
        # Fine raised inlay follows the silhouette's notches and ledges.
        points=[(x,py+.035,z) for x,py,z in rings[-1]]
        tube(mesh,points+[points[0]],.052,bone,'team',5)


def detailed_inner_armor(mesh):
    # The red zigzags were hatching, not teeth: grow one smooth solid shoulder.
    armor_panel(mesh,[(-5.5,9),(-7.2,5.8),(-9.5,3),(-11.3,.2),
                     (-10.8,-2),(-9,-5.3),(-6.7,-8.5),(-5.3,-10),
                     (-5.0,-3),(-5.1,4)],5.7,1.1,corner_radius=.65)
    armor_panel(mesh,[(-5.8,5.1),(-8.1,2.3),(-9.4,.1),
                     (-8.7,-2.6),(-6.7,-5.7),(-5.5,-6.2)],6.55,.45,
                material='steel',corner_radius=.55)
    # Upper starboard armor is broken into separate raised panels rather than
    # one smooth lozenge. The gaps expose the darker structural layer below.
    for polygon,y in [
        ([(8.8,23),(11.4,20.8),(13.1,16.5),(12.5,11),(10.7,9.1),(8.5,13.5),(7.9,18.4)],6.35),
        ([(12.1,7),(15.4,4.6),(17.4,2.6),(16.6,.2),(13.3,-2.7),(11.2,-1),(10.9,3.2)],6.55),
        ([(9.6,-6.5),(13.2,-8.6),(14.5,-13.5),(14.7,-17),(12.2,-20.5),(9.4,-22),(8.1,-18.2),(9,-13)],6.4)]:
        armor_panel(mesh,polygon,y,.6)
    # Arched structural ribs cross the now-solid starboard infill. These are
    # raised details, with no open slots between the bearing and the main hull.
    for z,width in [(16,7),(6,9),(-5,8),(-15,8.5)]:
        rib=path([(4.3,6.15,z),(6,6.6,z+.25),(8.5,6.8,z-.15),
                  (width+3,6.15,z-1.1)],3 if mesh.detail>=20 else 1)
        tube(mesh,rib,.16,0,'steel',8)
        tube(mesh,[(x,y+.13,pz) for x,y,pz in rib],.045,0,'team',5)
    # Small port AA islands gain shoulders and low-profile ventilating ribs.
    for x,z,bone in [(-15.7,0,9),(-9.8,-17,10)]:
        armor_panel(mesh,[(x-2.5,z+2.1),(x-2.7,z-1.2),(x-1.4,z-3.3),
                         (x-.8,z-2),(x-1.0,z+.8)],6.85,.48,bone,trim=False)
        for dz in (-2,-.8,.4):
            tube(mesh,[(x+1.1,6.95,z+dz),(x+1.8,7.15,z+dz+.5),(x+2.3,6.9,z+dz+.8)],.14,bone,'steel',6)


def concept_hull(mesh):
    # The top sketch has an open double rail, two centered gun bearings, a
    # scalloped right wing, and unequal detached leaves on the left and right.
    leaf(mesh,[(-4,4,-29.5,.1,.1),(-4.7,4.6,-25,1.7,1.3),
               (-4.5,5,-15,2.0,1.5),(-4.3,5,-2,1.7,1.5),
               (-4.5,5.2,12,1.7,1.6),(-3.5,5.6,20,.1,.1)])
    leaf(mesh,[(2,4.3,-29,.1,.1),(3.7,4.8,-24,1.3,1.3),
               (4.1,5,-12,1.6,1.5),(4.0,5.2,2,1.5,1.7),
               (4.2,5.5,15,1.7,1.5),(4,5.9,24,.1,.1)])
    # Solid right armor reaches underneath the right bearing rail. Hatching in
    # the user's correction means filled material, not a serrated/open border.
    # The lower-right spike is part of this same continuous armor outline.
    armor_panel(mesh,[(5.8,27),(11,23),(13.7,17),(13.7,12),(13.4,7),
                     (18.6,3),(18.4,0),(14,-5),(14.2,-11),(16.4,-16),
                     (14.2,-20.2),(17.8,-21.7),(18.3,-24.3),
                     (17.5,-26.8),(15.7,-24.9),(14.9,-23.2),(11.8,-22.8),
                     (7.1,-26),(4.9,-28),(2.8,-24),(2.8,-16),
                     (2.5,-8),(2.6,0),(2.8,8),(3,16),(3.2,23)],5.25,1.65,
                corner_radius=.55)
    # Long detached fore-left petal: angled like the large upper-left drawing.
    armor_panel(mesh,[(-13.7,8),(-17.4,12),(-18.2,17.5),(-15.1,24),
                     (-9.2,29),(-3.6,30),(-3.5,26.5),(-6.2,23),
                     (-8.2,19),(-11.5,13)],5.7,1.4,8,corner_radius=.85)
    armor_panel(mesh,[(-14.8,12.9),(-16.4,17.8),(-13.0,23.9),(-8,27.5),
                     (-5.3,28.2),(-7.1,24.2),(-10.5,19.2),(-11.5,16)],6.65,.55,8,
                material='steel',corner_radius=.65)
    # Port mid and aft AA islands are short, unequal and visibly detached.
    leaf(mesh,[(-15.0,5,-9,.1,.1),(-16,5.3,-6,2.8,1.2),
               (-15.7,5.5,0,3.8,1.5),(-15.3,5.5,5,2.7,1.1),
               (-14.3,5.6,9,.1,.1)],9)
    leaf(mesh,[(-11.4,4.8,-23,.1,.1),(-10.8,5.3,-21,2.6,1.1),
               (-9.8,5.7,-17,3.4,1.4),(-9,5.7,-13,2.8,1.2),
               (-8.3,5.8,-10.5,.1,.1)],10)
    leaf(mesh,[(17,6,-3,.1,.1),(18.1,6.4,0,1.7,.7),
               (17.9,6.6,5,1.5,.7),(16.9,6.8,10,.1,.1)],11)
    # Small swept trailing hooks, as in the sketched rear corners.
    leaf(mesh,[(-11.2,4,-29,.1,.1),(-13,4.3,-27,1.0,.5),
               (-14,4.7,-24.5,.8,.4),(-13.1,5,-23,.1,.1)],10,material='steel')
    # Smaller smooth port heel; the starboard spike is integrated above.
    armor_panel(mesh,[(-13.1,-23.5),(-14.5,-25),(-13.9,-26.3),
                     (-12.5,-26.5),(-11.6,-24.4)],5.1,.55,10,corner_radius=.45)
    detailed_inner_armor(mesh)
    # Two exposed circular hardpoints keep the central layout legible.
    for z in (10,-9):
        ovoid(mesh,(0,7.0,z),(4.6,1.4,4.9),material='joint')
        for radius,y in [(4.6,7.8),(4.0,8.4),(3.4,8.7)]:
            ring(mesh,(0,y,z),radius,.22,material='edge')
        ring(mesh,(0,8.5,z),4.3,.09,material='team')
    # Organic bearing pedestals visibly connect the two sketched hardpoints
    # to their guns. The raised rear gun has a taller, slimmer armored neck.
    ovoid(mesh,(0,10.1,10),(1.8,2.4,2.3),material='dark')
    ovoid(mesh,(0,13.6,-9),(2.0,5.1,2.7),material='dark',stations=13)
    for side in (-1,1):
        support=path([(side*1.25,8.6,-9),(side*2.0,11,-9.7),
                      (side*2.05,14.5,-9.9),(side*1.2,18,-9.3)],3 if mesh.detail>=20 else 1)
        tube(mesh,support,.26,0,'steel',8)
        tube(mesh,[(x+side*.22,y,z) for x,y,z in support],.055,0,'team',6)
    # Recessed shield lens and underside lift points keep the hull understated.
    ovoid(mesh,(5,8,-23),(1.3,1.3,1.6),7,'crystal')
    for x,y,z,bone in [(-12,4.1,21,8),(-15.5,3.9,0,9),(-10,4,-17,10),(12,3.7,-11,0)]:
        ring(mesh,(x,y,z),1.2,.11,bone,'lens')


def main_cannon(mesh, zcenter, height, yaw, pitch):
    # The right-hand sketch is an elongated pod wrapped by spiral bands. Its
    # front detail is interpreted as a three-petal muzzle around one charge.
    ring(mesh,(0,height-2.8,zcenter),3.5,.28,yaw,'edge')
    ovoid(mesh,(0,height-1.6,zcenter),(3.1,1.2,3.8),yaw,'steel')
    leaf(mesh,[(0,height,zcenter-6.8,.1,.12),(0,height,zcenter-5.2,1.9,1.9),
               (0,height,zcenter-2.4,3.2,3.0),(0,height,zcenter+.3,3.4,3.1),
               (0,height,zcenter+3.1,2.8,2.5),(0,height,zcenter+4.0,1.6,1.5)],pitch)
    # Triple focusing leaves are rounded thick geometry with real openings.
    for angle in (math.pi/2,math.pi/2+2*math.pi/3,math.pi/2+4*math.pi/3):
        rings=[];centers=[]
        radial=np.array((math.cos(angle),math.sin(angle),0))
        tangent=np.array((-math.sin(angle),math.cos(angle),0))
        for dz,r,w,h in [(1.8,2.2,.65,.6),(4.8,3.1,.8,.65),(7.8,3.0,.7,.55),(10,2.0,.43,.38),(11.2,1.3,.12,.13)]:
            center=np.array((0,height,zcenter+dz))+radial*r
            centers.append(center)
            rings.append([center+tangent*w*math.cos(a)+radial*h*math.sin(a) for a in np.linspace(0,2*math.pi,12 if mesh.detail>=20 else 8,endpoint=False)])
        mesh.loft(rings,centers,pitch,'steel')
        tube(mesh,[c+radial*.57 for c in centers[1:-1]],.075,pitch)
    # Two physical, counterposed spiral ribs and very thin player-color veins.
    for phase in (0,math.pi):
        ribs=[];lights=[]
        for t in np.linspace(0,1,55 if mesh.detail>=20 else 28):
            dz=-5.0+t*8.5; a=phase+t*math.pi*2.1
            r=math.sqrt(max(.05,1-((dz+.5)/6.7)**2))
            ribs.append((3.45*r*math.cos(a),height+3.23*r*math.sin(a),zcenter+dz))
            lights.append((3.60*r*math.cos(a),height+3.38*r*math.sin(a),zcenter+dz))
        tube(mesh,ribs,.16,pitch,'edge',8)
        tube(mesh,lights,.055,pitch,'team',6)
    ovoid(mesh,(0,height,zcenter+6),(1.15,1.15,1.4),pitch,'lens',stations=7)


def model(detail):
    mesh=Mesh(detail);concept_hull(mesh)
    main_cannon(mesh,10,15,1,2)
    main_cannon(mesh,-9,21,4,5)
    for i,(x,y,z) in enumerate(AA_POSITIONS):
        yaw=AA_BONES[i];pitch=yaw+1
        ovoid(mesh,(x,y-.8,z),(2.8,.8,3.0),AA_HULLS[i],'joint',stations=9)
        ovoid(mesh,(x,y+.2,z),(2.4,1.4,2.7),yaw,'steel',stations=9)
        for dx in (-.8,.8):
            leaf(mesh,[(x+dx,y+1.5,z-1.5,.1,.1),(x+dx,y+1.5,z-.5,.7,.7),
                       (x+dx,y+1.5,z+2,.6,.55),(x+dx,y+1.5,z+4.5,.25,.3)],pitch)
            ovoid(mesh,(x+dx,y+1.5,z+4.55),(.2,.23,.12),pitch,'lens',stations=5)
    mesh.smooth()
    vertices=[];indices=[];lookup={};groups=[]
    for index in mesh.indices:
        v=mesh.vertices[index]
        # Share identical position/normal/UV/bone records; smooth their tangent
        # frames within the same UV chart, preserving every UV and bone seam.
        key=tuple(round(float(x),6) for x in v[:6]+v[12:])
        if key not in lookup:
            lookup[key]=len(vertices);vertices.append(v);groups.append([])
        groups[lookup[key]].append(v)
        indices.append(lookup[key])
    for i,group in enumerate(groups):
        v=vertices[i];normal=np.asarray(v[3:6]);tangent=np.sum([x[6:9] for x in group],axis=0)
        tangent=normalized(tangent-normal*np.dot(normal,tangent))
        handedness=1 if np.dot(np.cross(normal,tangent),np.sum([x[9:12] for x in group],axis=0))>=0 else -1
        vertices[i]=v[:6]+tuple(tangent)+tuple(np.cross(normal,tangent)*handedness)+v[12:]
    mesh.vertices=vertices;mesh.indices=indices
    return mesh


def render_views():
    for name,az,el in [('game_view',35,38),('front',0,13),('side',90,12),('top',0,88),('rear',150,28)]:
        render_scm(UNIT/'GGA0402_lod0.scm',SOURCE,SOURCE/f'GGA0402_{name}.png',azimuth=az,elevation=el,size=720,texture_mip=1,player=(.12,.75,.25),plan_view=name=='top')
    render_scm(UNIT/'GGA0402_lod0.scm',SOURCE,SOURCE/'GGA0402_alt_color.png',azimuth=35,elevation=38,size=720,texture_mip=2,player=(1,.15,.04))
    render_scm(UNIT/'GGA0402_lod0.scm',SOURCE,SOURCE/'GGA0402_hull_top.png',azimuth=0,elevation=88,size=720,texture_mip=1,player=(.12,.75,.25),bones=[0]+list(range(7,len(NAMES))),plan_view=True)
    sheet=Image.new('RGB',(1440,1440),(24,28,33));draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(['hull_top','game_view','front','side']):
        sheet.paste(Image.open(SOURCE/f'GGA0402_{name}.png'),(i%2*720,i//2*720))
        draw.text((i%2*720+20,i//2*720+20),f'GGA0402 / {name}',fill=(190,205,215))
    sheet.save(SOURCE/'GGA0402_views.png')
    icon=render_scm(UNIT/'GGA0402_lod0.scm',SOURCE,SOURCE/'GGA0402_icon_render.png',azimuth=35,elevation=40,size=256,transparent=True,player=(.12,.75,.25)).resize((64,64),Image.Resampling.LANCZOS)
    icon.save(SOURCE/'GGA0402_icon.png')
    for folder in ['icons/units','textures/ui/common/icons/units']:save_dds_dxt5(icon,MOD/folder/'GGA0402_icon.dds')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--skip-textures',action='store_true');parser.add_argument('--skip-previews',action='store_true');parser.add_argument('--previews-only',action='store_true');args=parser.parse_args()
    if args.previews_only:
        render_views();return
    if not args.skip_textures:make_textures(SOURCE,UNIT,save_dds_dxt5)
    report={'unit':'GGA0402','scale':.1,'lods':[],'bones':[],'mipmaps':{}}
    for lod,detail in enumerate((24,12)):
        m=model(detail);p=UNIT/f'GGA0402_lod{lod}.scm'
        assert len(m.vertices)<65536, (lod,len(m.vertices),len(m.indices)//3)
        write_scm(m,p,NAMES,PARENTS,PIVOTS)
        v,f=load_scm(p)
        assert np.isfinite(v).all() and f.max()<len(v)
        assert np.max(abs(np.linalg.norm(v[:,3:6],axis=1)-1))<1e-5
        assert np.min(np.linalg.norm(np.cross(v[f[:,1],:3]-v[f[:,0],:3],v[f[:,2],:3]-v[f[:,0],:3]),axis=1))>1e-8
        report['lods'].append({'vertices':len(v),'triangles':len(f),'bounds':(np.array([v[:,:3].min(0),v[:,:3].max(0)])*.1).tolist()})
        if lod==0:export_obj(m,SOURCE,NAMES)
    for suffix in ['albedo','specteam','normalsTS']:
        report['mipmaps'][suffix]=[]
        for mip in range(10):
            a=np.asarray(load_dds_mip(UNIT/f'GGA0402_{suffix}.dds',mip));assert a[:,:,:3].max()>0
            report['mipmaps'][suffix].append(a.mean(axis=(0,1)).tolist())
    report['bones']=[{'name':n,'parent':p,'position':list(v)} for n,p,v in zip(NAMES,PARENTS,PIVOTS)]
    (SOURCE/'export_findings.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['lods']),flush=True)
    if args.skip_previews:return
    render_views()



if __name__=='__main__':main()
