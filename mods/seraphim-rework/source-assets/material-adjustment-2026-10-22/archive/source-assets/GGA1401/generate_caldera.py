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
from reactor_geometry import Mesh, export_obj, make_textures, render_scm, load_scm, load_dds_mip, load_sca_pose
from supcom_binary import write_scm, write_sca, save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
MOD = ASSETS.parent.parent
UNIT = MOD / 'units/GGA1401'
NAMES = ['GGA1401', 'Island_A', 'Island_B', 'Island_C', 'Core', 'TopIsland', 'TopSatellite']
PARENTS = [-1, 0, 0, 0, 0, 0, 0]
# Separate orbital lanes clear the central crown and the new lower petals.
ORBIT_RADII = [32, 34, 34]
ORBIT_HEIGHTS = [29, 36, 10]
ORBIT_PHASES = [math.radians(x) for x in (15, 145, 255)]
# Viewed from +Y, with +X to the right and +Z down: positive X/Z angle is CW.
ORBIT_DIRECTIONS = [1, 1, -1]
ORBIT_DURATION = 32
ISLANDS = [(r*math.cos(a),y,r*math.sin(a))
           for r,y,a in zip(ORBIT_RADII,ORBIT_HEIGHTS,ORBIT_PHASES)]
TOP_CENTER = (0, 63, 0)
TOP_RADIUS = 17
TOP_PHASE = math.radians(40)
TOP_SATELLITE = (TOP_RADIUS*math.cos(TOP_PHASE),63,TOP_RADIUS*math.sin(TOP_PHASE))
PIVOTS = [(0, 0, 0), *ISLANDS, (0, 23, 0), TOP_CENTER, TOP_SATELLITE]


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


def rotate_xz(m, angle, fn):
    start=len(m.vertices)
    fn()
    c,s=math.cos(angle),math.sin(angle)
    rotation=np.array(((c,0,-s),(0,1,0),(s,0,c)))
    for i in range(start,len(m.vertices)):
        v=m.vertices[i]
        m.vertices[i]=tuple(x for j in (0,3,6,9) for x in rotation@v[j:j+3])+v[12:]


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


def lower_petal(m, angle, length, height, width):
    a=math.radians(angle)
    radial=np.array((math.cos(a),0,math.sin(a)))
    tangent=np.array((-math.sin(a),0,math.cos(a)))
    # Two staggered tiers of outward-sweeping leaves, with rolled lens edges.
    profile=[(12,1.9,.15,.22),(15,2.3,width*.7,.7),
             (length*.82,3.5,width,1.1),(length,5,width*.8,.9),
             (length*.98,height*.68,width*.43,.6),
             (length*.89,height*.94,width*.12,.22),
             (length*.86,height,.07,.08)]
    rings=[]; centers=[]
    for r,y,w,d in curve(profile,3 if m.detail>=32 else 2):
        center=radial*r+(0,y,0)
        centers.append(center)
        rings.append([center+tangent*(max(.05,w)*math.cos(t))+
                      radial*(max(.05,d)*math.sin(t))
                      for t in np.linspace(0,2*math.pi,12 if m.detail>=32 else 8,endpoint=False)])
    m.loft(rings,centers,0,'armor')
    tube(m,[radial*(r+d+.07)+(0,y,0) for r,y,w,d in profile[1:-1]],.065)


def shard(m, bone, width, height, thickness, lean):
    """Closed, curved silver shard: broad face, asymmetric tips, no crater."""
    rings=[]; centers=[]
    profile=[(-height*.60,.025,-1.1),(-height*.52,.21,-.9),
             (-height*.30,.68,-.5),(0,1,0),
             (height*.23,.86,.35),(height*.43,.40,.8),
             (height*.53,.10,1),(height*.55,.025,1.05)]
    for y,scale,shift in curve(profile,3 if m.detail>=32 else 2):
        scale=max(.02,scale)
        center=np.array((lean*shift,y,shift*.65))
        centers.append(center)
        rings.append([center+(thickness*scale*math.sin(t),0,width*scale*math.cos(t))
                      for t in np.linspace(0,2*math.pi,12 if m.detail>=32 else 8,endpoint=False)])
    m.loft(rings,centers,bone,'armor')
    # Slim raised spine and inset lens give the fragment its engineered character.
    tube(m,[(lean*s+thickness*max(.02,k)+.055,y,s*.65)
            for y,k,s in profile[1:-1]],.075,bone)
    translate(m,(thickness+.12,0,0),lambda:shell(m,
        [(.025,-1.8),(.40,-1.45),(.6,0),(.4,1.3),(.025,1.65)],bone,'lens'))


def floating_island(m, bone, scale=1):
    """Irregular closed floating island with rounded, asymmetric lobes.

    A skewed keel blends into a broad three-lobed shell. Its upper surface is
    solid and curved: no crater, cone, circular platform or repeated petal.
    """
    profile=[(-7.5,.045,-1.5),(-6.4,1.3,-1.3),(-4.2,3.8,-.8),
             (-1.2,6.6,-.15),(1,7,.35),(2.8,5.3,.8),
             (4,2.7,1.2),(4.5,.045,1.4)]
    rings=[]; centers=[]
    sides=20 if m.detail>=32 else 12
    for y,r,shift in curve(profile,3 if m.detail>=32 else 2):
        r=max(.04,r)
        center=np.array((shift,y,-shift*.65))*scale
        centers.append(center)
        ring=[]
        for a in np.linspace(0,2*math.pi,sides,endpoint=False):
            lobe=1+.16*math.cos(3*a+.4)+.07*math.sin(5*a)
            ring.append(center+scale*np.array((r*lobe*math.cos(a),
                        .10*r*math.sin(2*a+.6),r*.74*lobe*math.sin(a))))
        rings.append(ring)
    m.loft(rings,centers,bone,'armor')
    # Narrow seams along the rounded side retain the Seraphim player-color detail.
    for a in (.3,3.7):
        points=[]
        for y,r,shift in profile[1:-1]:
            lobe=1+.16*math.cos(3*a+.4)+.07*math.sin(5*a)
            points.append(scale*np.array((shift+(r*lobe+.08)*math.cos(a),
                          y+.10*r*math.sin(2*a+.6),-shift*.65+(r*.74*lobe+.08)*math.sin(a))))
        tube(m,points,.07*scale,bone)


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
    # Broad outer petals fill the lower silhouette; smaller inner petals layer it.
    for angle in range(0,360,60):
        lower_petal(m,angle+12,27,12.5,3.8)
    for angle in range(0,360,72):
        lower_petal(m,angle+43,21,17,2.5)
    m.annulus(16.6,17.4,1.6,2.25,0,'edge')
    # Six small root conduits/pods add detail between the broader lower leaves.
    for angle in range(0,360,60):
        a=math.radians(angle+42)
        translate(m,(17*math.cos(a),2.8,17*math.sin(a)),
                  lambda:shell(m,[(.025,-1),(1.3,-.6),(1.65,0),(1.25,1.2),(.025,2.2)],0,'steel'))
    for i,((x,y,z),width,height,thickness,lean) in enumerate(zip(
            ISLANDS,[4.5,5.6,3.8],[17,21,13],[2.2,2.6,1.9],[2.6,-3.1,2])):
        bone=i+1
        translate(m,(x,y,z),lambda:rotate_xz(m,ORBIT_PHASES[i],
                  lambda:shard(m,bone,width,height,thickness,lean)))
    # Suspended central plasma seed, separate bone for gentle axial rotation.
    translate(m,PIVOTS[4],lambda:shell(m,[(.02,-4.8),(2.4,-4.2),(4,-2.5),
                  (4.7,0),(4,2.5),(2.4,4.2),(.02,4.8)],4,'steel',.025))
    # Two extra upper objects; the original three orbital shards are retained.
    translate(m,TOP_CENTER,lambda:floating_island(m,5))
    translate(m,TOP_SATELLITE,lambda:rotate_xz(m,TOP_PHASE,
              lambda:floating_island(m,6,.48)))
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


def main(rebuild_textures=True):
    UNIT.mkdir(parents=True,exist_ok=True)
    stats={}
    for lod,detail in [(0,32),(1,16)]:
        m=build_mesh(detail)
        write_scm(m,UNIT/f'GGA1401_lod{lod}.scm',NAMES,PARENTS,PIVOTS)
        if lod==0: export_obj(m,ASSETS,NAMES)
        stats[f'lod{lod}']={'triangles':len(m.indices)//3,'vertices':len(m.vertices)}
        print(f'LOD{lod}: {stats[f"lod{lod}"]}',flush=True)
    if rebuild_textures:
        make_textures(ASSETS,UNIT,save_dds_dxt5)
    frames=[]
    for j in range(129):
        t=j/128*math.pi*2
        frame=[]
        for i,p in enumerate(PIVOTS):
            q=list(p)
            if i in (1,2,3):
                theta=ORBIT_DIRECTIONS[i-1]*t
                c,s=math.cos(theta),math.sin(theta)
                q[0],q[2]=p[0]*c-p[2]*s,p[0]*s+p[2]*c
                q[1]+=.6*math.sin(2*t+(i-1)*math.pi*2/3)
                # Quaternion yaw uses the opposite sign to this X/Z angle.
                a=-theta
            elif i==5:
                # Fixed center, clockwise spin: two turns per 32-second clip.
                a=-2*t
            elif i==6:
                # Counterclockwise orbit about the upper island's fixed center.
                theta=-t
                c,s=math.cos(theta),math.sin(theta)
                dx,dz=p[0]-TOP_CENTER[0],p[2]-TOP_CENTER[2]
                q[0]=TOP_CENTER[0]+dx*c-dz*s
                q[2]=TOP_CENTER[2]+dx*s+dz*c
                a=-theta
            else:
                a=2*t if i==4 else 0
            frame.append((q,(math.cos(a/2),0,math.sin(a/2),0)))
        frames.append(frame)
    write_sca(UNIT/'GGA1401_idle.sca',NAMES,PARENTS,frames,ORBIT_DURATION)
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
    stats['orbits']={'period_seconds':ORBIT_DURATION,'directions_top_view':['CW','CW','CCW'],
                     'radii_game_units':[r*.1 for r in ORBIT_RADII],
                     'heights_game_units':[y*.1 for y in ORBIT_HEIGHTS]}
    stats['upper_islands']={'center_game_units':[x*.1 for x in TOP_CENTER],
                           'central_spin_direction_top_view':'CW','central_spin_period_seconds':16,
                           'satellite_orbit_direction_top_view':'CCW','satellite_orbit_period_seconds':32,
                           'satellite_orbit_radius_game_units':TOP_RADIUS*.1}
    # Show real exported animation poses. Fixed framing makes the orbit readable.
    animation=[]
    upper_animation=[]
    bounds=np.array([(x,y,z) for x in (-40,40) for y in (0,70) for z in (-40,40)])
    upper_bounds=np.array([(x,y,z) for x in (-24,24) for y in (53,71) for z in (-24,24)])
    for i in range(16):
        seconds=i*ORBIT_DURATION/16
        frame=render_scm(UNIT/'GGA1401_lod0.scm',ASSETS,ASSETS/'GGA1401_orbit_frame.png',
                         0,65,(.13,.78,.42),420,texture_mip=1,
                         pose=load_sca_pose(UNIT/'GGA1401_idle.sca',seconds),fixed_bounds=bounds)
        ImageDraw.Draw(frame).text((12,12),f'{seconds:02.0f}s / 32s',fill=(224,234,244))
        ImageDraw.Draw(frame).text((12,28),'10x animation preview',fill=(184,200,214))
        animation.append(frame)
        upper=render_scm(UNIT/'GGA1401_lod0.scm',ASSETS,ASSETS/'GGA1401_upper_frame.png',
                         35,30,(.13,.78,.42),420,texture_mip=0,bones=(5,6),
                         pose=load_sca_pose(UNIT/'GGA1401_idle.sca',seconds),fixed_bounds=upper_bounds)
        ImageDraw.Draw(upper).text((12,12),'Upper islands / 10x preview',fill=(224,234,244))
        upper_animation.append(upper)
        if i%4==0:print(f'Orbit preview {i+1}/16',flush=True)
    animation[0].save(ASSETS/'GGA1401_orbits.gif',save_all=True,append_images=animation[1:],
                      duration=200,loop=0,disposal=2)
    upper_animation[0].save(ASSETS/'GGA1401_upper_islands.gif',save_all=True,
                           append_images=upper_animation[1:],duration=200,loop=0,disposal=2)
    poses=Image.new('RGB',(1680,420))
    for i in range(4):poses.paste(animation[i*4],(420*i,0))
    poses.save(ASSETS/'GGA1401_orbit_phases.png')
    for i in range(4):poses.paste(upper_animation[i*4],(420*i,0))
    poses.save(ASSETS/'GGA1401_upper_phases.png')
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
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--reuse-textures',action='store_true',help='Keep existing DDS maps for a geometry-only rebuild')
    main(not parser.parse_args().reuse_textures)
