"""Build Uya-Iava: original T4 reactor geometry, BC3 maps, SCA and SCM previews.

Run with Python + numpy + Pillow. Source units are 10 per game unit.
Geometry/material/export helpers derive from this mod's rounded GGA2401 workflow.
All runtime assets and reproducible sources live under GGA1401.
"""
from pathlib import Path
import math
import json
import zipfile
from io import BytesIO
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reactor_geometry import Mesh, export_obj, make_textures, render_scm, load_scm, load_dds_mip
from supcom_binary import write_scm, write_sca, save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
MOD = ASSETS.parent.parent
UNIT = MOD / 'units/GGA1401'
NAMES = ['GGA1401', 'Island_A', 'Island_B', 'Island_C', 'Core']
PARENTS = [-1, 0, 0, 0, 0]
# Deliberately different elevations and sizes, arranged around a real open crater.
ISLANDS = [(24, 18, 7), (-21, 24, 14), (-7, 15, -25)]
PIVOTS = [(0, 0, 0), *ISLANDS, (0, 23, 0)]


def curve(points, steps):
    p = [np.array(x, dtype=float) for x in points]
    result = []
    for i in range(len(p)-1):
        a,b,c,d = p[max(0,i-1)],p[i],p[i+1],p[min(len(p)-1,i+2)]
        for j in range(steps):
            t = j/steps
            result.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return result+[p[-1]]


def shell(m, profile, bone=0, material='armor', lobes=0, phase=0):
    """Surface of revolution with rounded, continuous radial/vertical sections.

    The profile runs from underside through outer wall over the rolled lip and
    down the inner crater wall. Outward normals follow that profile, including
    inward-facing cavity normals; no invisible cap closes the crater mouth.
    """
    profile = curve(profile, 3 if m.detail >= 40 else 2)
    n = m.detail
    for i in range(len(profile)-1):
        r,y = profile[i]; rr,yy = profile[i+1]
        for j in range(n):
            a,b = j*2*math.pi/n,(j+1)*2*math.pi/n
            def point(rad,h,angle):
                flute = 1 + lobes*math.cos(angle*5+phase)*math.sin(math.pi*min(1,max(0,h/30)))**2
                return (rad*flute*math.cos(angle),h,rad*flute*math.sin(angle))
            mid = (a+b)/2
            normal = ((yy-y)*math.cos(mid),r-rr,(yy-y)*math.sin(mid))
            m.face([point(r,y,a),point(rr,yy,a),point(rr,yy,b),point(r,y,b)],
                   bone,material,normal,
                   [(j/n,i/(len(profile)-1)),(j/n,(i+1)/(len(profile)-1)),
                    ((j+1)/n,(i+1)/(len(profile)-1)),((j+1)/n,i/(len(profile)-1))])


def translate(m, offset, fn):
    start = len(m.vertices)
    fn()
    for i in range(start,len(m.vertices)):
        v=m.vertices[i]
        m.vertices[i]=tuple(np.array(v[:3])+offset)+v[3:]


def tube(m, points, radius, bone=0, material='team'):
    points=curve(points,3 if m.detail>=40 else 2)
    rings=[]
    for i,p in enumerate(points):
        direction=points[min(i+1,len(points)-1)]-points[max(0,i-1)]
        direction/=max(1e-9,np.linalg.norm(direction))
        u=np.cross(direction,(0,0,1))
        if np.linalg.norm(u)<.01: u=np.cross(direction,(1,0,0))
        u/=np.linalg.norm(u); v=np.cross(direction,u)
        rings.append([p+radius*(u*math.cos(a)+v*math.sin(a)) for a in np.linspace(0,2*math.pi,8,endpoint=False)])
    m.loft(rings,points,bone,material)


def caldera(m, radius, height, bone, small=False):
    # Broad organic shoulders taper to a rolled, open throat and recessed well.
    profile=[(.03,0),(radius*.65,0),(radius*.94,.35),(radius,1.3),
             (radius*.96,height*.16),(radius*.79,height*.36),
             (radius*.62,height*.66),(radius*.51,height*.90),
             (radius*.49,height),(radius*.46,height+radius*.035),
             (radius*.41,height),(radius*.38,height*.92),
             (radius*.36,height*.75),(radius*.26,height*.65),(.03,height*.65)]
    shell(m,profile,bone,'armor',.045)
    # Real concentric field-coil geometry inside the crater, below its rim.
    translate(m,(0,height*.69,0),lambda:m.annulus(radius*.13,radius*.30,0,.27,bone,'team'))
    translate(m,(0,height*.70,0),lambda:m.column([(radius*.12,0),(radius*.1,.4),(.02,.6)],bone,'lens'))
    # Thin energy channels climb shoulders, following their curvature.
    for k in range(5):
        a=k*math.pi*2/5+.22
        points=[(radius*r*math.cos(a),height*y+.13,radius*r*math.sin(a))
                for r,y in [(1,.08),(.84,.29),(.69,.49),(.56,.73),(.50,.93)]]
        tube(m,points,.045 if small else .085,bone)


def leaf(m, angle, height, radius=1, bone=0):
    """Swept lenticular armor petal with a rounded perimeter and smooth tip.

    Width runs tangentially and thickness radially. Unlike a cone, each petal
    has a broad engraved face and a thin rolled edge; genuine gaps separate it
    from its neighbors. The outer and inner faces share consistent normals.
    """
    a=math.radians(angle)
    radial=np.array((math.cos(a),0,math.sin(a)))
    tangent=np.array((-math.sin(a),0,math.cos(a)))
    # radius, height fraction, half-width, half-thickness, sideways sweep
    profile=[(24,0,1,.55,0),(24,.035,4.8,1.1,0),
             (22,.12,6.2,1.65,.3),(18,.34,5.8,1.6,.8),
             (14,.61,4.1,1.15,1.2),(12.4,.82,2.3,.75,1.5),
             (12.1,.95,.82,.35,1.5),(12.2,.994,.20,.16,1.5),
             (12.25,1,.035,.04,1.5)]
    sections=curve(profile,3 if m.detail>=32 else 2)
    rings=[]; centers=[]
    count=12 if m.detail>=32 else 8
    for r,y,w,d,sweep in sections:
        center=radial*(r*radius)+tangent*(sweep*radius)+(0,y*height,0)
        centers.append(center)
        rings.append([center+tangent*(w*radius*math.cos(t))+
                      radial*(d*radius*math.sin(t))
                      for t in np.linspace(0,2*math.pi,count,endpoint=False)])
    m.loft(rings,centers,bone,'armor')
    # Restrained energy seam follows the outer face; most color remains in
    # the longitudinal engraved circles on the broad armor faces.
    points=[]
    for r,y,w,d,sweep in profile[1:-1]:
        points.append(radial*((r+d+.045)*radius)+tangent*(sweep*radius)+(0,y*height,0))
    tube(m,points,.06*radius,bone)


def build_mesh(detail):
    m=Mesh(detail)
    # Compact ring foundation leaves the stock ground circles visible around it.
    shell(m,[(.03,.1),(14,.1),(17,.35),(18,.9),(17.8,1.4),
             (16,1.8),(.03,1.8)],0,'dark')
    m.annulus(12.5,16.4,1.5,2.3,0,'steel')
    m.annulus(13.1,13.35,2.35,2.46,0,'team')
    # Low open energy throat, framed by tall asymmetrical petals like XSB1301.
    translate(m,(0,1.8,0),lambda:caldera(m,12.8,11.5,0))
    for angle,height in [(18,36),(90,52),(162,43),(234,29),(306,38)]:
        leaf(m,angle,height)
    for i,((x,y,z),radius,height) in enumerate(zip(ISLANDS,[4.6,5.4,4.1],[5.5,6.5,5])):
        bone=i+1
        def island():
            # Rounded floating keel is visibly separated from the ground platform.
            shell(m,[(.02,-6),(radius*.18,-5.6),(radius*.48,-3.7),
                     (radius*.89,-1.3),(radius,-.4),(radius,0),(.02,0)],bone,'steel')
            caldera(m,radius,height,bone,True)
            m.annulus(radius*.45,radius*.78,-1.8,-1.4,bone,'team')
            # Smaller split crowns echo the main generator, rather than cups.
            for angle in [65,245]:
                leaf(m,angle,height*1.9,radius/23,bone)
        translate(m,(x,y,z),island)
    # Suspended central plasma seed, separate bone for gentle axial rotation.
    translate(m,PIVOTS[4],lambda:shell(m,[(.02,-4.8),(2.4,-4.2),(4,-2.5),
                  (4.7,0),(4,2.5),(2.4,4.2),(.02,4.8)],4,'steel',.025))
    m.smooth()
    vertices,indices,lookup=[],[],{}
    for old in m.indices:
        v=m.vertices[old]
        key=tuple(round(float(x),8) for x in v[:16])+(int(v[16]),)
        if key not in lookup:
            lookup[key]=len(vertices); vertices.append(v)
        indices.append(lookup[key])
    m.vertices,m.indices=vertices,indices
    return m


def main():
    UNIT.mkdir(parents=True,exist_ok=True)
    stats={}
    for lod,detail in [(0,32),(1,16)]:
        m=build_mesh(detail)
        write_scm(m,UNIT/f'GGA1401_lod{lod}.scm',NAMES,PARENTS,PIVOTS)
        if lod==0: export_obj(m,ASSETS,NAMES)
        stats[f'lod{lod}']={'triangles':len(m.indices)//3,'vertices':len(m.vertices)}
        print(f'LOD{lod}: {stats[f"lod{lod}"]}',flush=True)
    make_textures(ASSETS,UNIT,save_dds_dxt5)
    frames=[]
    for j in range(65):
        t=j/64*math.pi*2
        frame=[]
        for i,p in enumerate(PIVOTS):
            q=list(p)
            if i in (1,2,3): q[1]+=.6*math.sin(t+(i-1)*math.pi*2/3)
            # Central orb makes a full continuous turn. Islands keep their places.
            a=t if i==4 else 0
            frame.append((q,(math.cos(a/2),0,math.sin(a/2),0)))
        frames.append(frame)
    write_sca(UNIT/'GGA1401_idle.sca',NAMES,PARENTS,frames,16)
    views=[]
    for name,az,el in [('Front',0,16),('Side',90,16),('Game view',35,38)]:
        im=render_scm(UNIT/'GGA1401_lod0.scm',ASSETS,ASSETS/f'GGA1401_{name.lower().replace(" ","_")}.png',
                      az,el,(.13,.78,.42),800,texture_mip=2 if name=='Game view' else 0)
        ImageDraw.Draw(im).text((22,22),name,fill=(220,232,240),font=ImageFont.load_default(size=21))
        views.append(im)
    sheet=Image.new('RGB',(2400,800))
    for i,im in enumerate(views): sheet.paste(im,(800*i,0))
    sheet.save(ASSETS/'GGA1401_views.png')
    stock_env=Path('D:/Steam/steamapps/common/Supreme Commander Forged Alliance/gamedata/env.scd')
    if stock_env.exists():
        with zipfile.ZipFile(stock_env) as archive:
            texture=Image.open(BytesIO(archive.read('env/Common/decals/Tarmacs/Tar12x_seraphim_01_albedo.dds'))).convert('RGBA')
        render_scm(UNIT/'GGA1401_lod0.scm',ASSETS,ASSETS/'GGA1401_ground_view.png',
                   35,48,(.13,.78,.42),1000,texture_mip=1,ground_tarmac=texture)
    # True silhouette transparency comes from the SCM depth buffer. Material
    # alpha contains team colors and must never be used as image transparency.
    game=render_scm(UNIT/'GGA1401_lod0.scm',ASSETS,ASSETS/'GGA1401_icon_render.png',
                    35,38,(.13,.78,.42),512,transparent=True)
    icon=game.resize((64,64),Image.Resampling.LANCZOS)
    icon.save(ASSETS/'GGA1401_icon_64.png')
    for folder in [MOD/'icons/units',MOD/'textures/ui/common/icons/units']:
        folder.mkdir(parents=True,exist_ok=True)
        save_dds_dxt5(icon,folder/'GGA1401_icon.dds')
    # Read the actual exported data for bounds and data-channel mip inspection.
    v,_=load_scm(UNIT/'GGA1401_lod0.scm')
    stats['bounds_game_units']=[(v[:,:3].min(0)*.1).tolist(),(v[:,:3].max(0)*.1).tolist()]
    stats['dds_mips']={}
    for suffix in ['albedo','specteam','normalsTS']:
        stats['dds_mips'][suffix]=[]
        for level in [0,2,4,6]:
            a=np.array(load_dds_mip(UNIT/f'GGA1401_{suffix}.dds',level))
            stats['dds_mips'][suffix].append({'level':level,'size':list(a.shape[:2]),
                                             'mean_rgba':a.mean(axis=(0,1)).tolist()})
    (ASSETS/'export_findings.json').write_text(json.dumps(stats,indent=2)+'\n')
    print('Exported GGA1401 model, animation, materials, icon and SCM views.',flush=True)


if __name__=='__main__':
    main()
