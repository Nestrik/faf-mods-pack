"""Original Thuunar T1 chassis, open missile cradle, reload and damaged wreck.

Python + numpy + Pillow. No stock geometry, textures or animations are exported.
Source axes: Y up, +Z forward. Unit scale: 0.1.
"""
from pathlib import Path
import argparse
import math
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from launcher_geometry import Mesh, normalized, export_obj, make_textures, render_scm, load_scm
from supcom_binary import write_scm, write_sca, save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
MOD = ASSETS.parents[1]
UNIT = MOD/'units/GGA0101'
WRECK = MOD/'props/GGA0101_wreck'
NAMES = ['GGA0101', 'Turret', 'missile']
PARENTS = [-1, 0, 1]
PIVOTS = [(0,0,0), (0,3.65,-2.7), (0,0,9.0)]
ELEVATION = math.radians(30)
ROTATIONS = [(1,0,0,0), (math.cos(ELEVATION/2),-math.sin(ELEVATION/2),0,0), (1,0,0,0)]


def append_transformed(dst, src, rotation=None, offset=(0,0,0), bone=0):
    rotation = np.eye(3) if rotation is None else np.asarray(rotation)
    start = len(dst.vertices)
    for v in src.vertices:
        p=rotation@v[:3]+offset
        vectors=[rotation@v[k:k+3] for k in (3,6,9)]
        dst.vertices.append(tuple(p)+tuple(np.concatenate(vectors))+v[12:16]+(bone,))
    dst.indices.extend(start+i for i in src.indices)
    dst.materials.extend(src.materials)


def rotate_x(a):
    c,s=math.cos(a),math.sin(a)
    return np.array(((1,0,0),(0,c,-s),(0,s,c)))


def shell(mesh, sections, bone=0, material='armor', sides=None):
    """Smooth longitudinal elliptical sections, with geometry-rounded shoulders."""
    n=sides or mesh.detail
    rings=[]; centers=[]
    for x,y,z,rx,ry in sections:
        centers.append((x,y,z))
        rings.append([(x+rx*math.cos(j*2*math.pi/n),
                       y+ry*math.sin(j*2*math.pi/n),z) for j in range(n)])
    mesh.loft(rings,centers,bone,material)


def tube(mesh, points, radius, material='edge', bone=0, sides=8):
    points=np.asarray(points,dtype=float)
    rings=[]
    for i,p in enumerate(points):
        axis=normalized(points[min(i+1,len(points)-1)]-points[max(i-1,0)])
        u=normalized(np.cross(axis,(0,1,0) if abs(axis[1])<.95 else (1,0,0)))
        v=np.cross(axis,u)
        rings.append([p+radius*(u*math.cos(j*2*math.pi/sides)+v*math.sin(j*2*math.pi/sides))
                      for j in range(sides)])
    mesh.loft(rings,points,bone,material)


def capsule_ring(mesh,x,zcenter,length,radius,width,material='joint'):
    """Closed caterpillar belt, with a genuine gap around the road wheels."""
    n=max(12,mesh.detail)
    path=[]
    for end,base in ((1,0),(-1,math.pi)):
        for i in range(n//2+1):
            a=base+i*math.pi/(n//2)
            path.append(np.array((x,1.35+radius*math.cos(a),zcenter+end*length/2+radius*math.sin(a))))
    rings=[]
    for p in path:
        dy,dz=p[1]-1.35,p[2]-zcenter
        dz-=np.clip(dz,-length/2,length/2)
        radial=normalized((0,dy,dz))
        rings.append([p+(-width/2,0,0)-radial*.14,
                      p+(width/2,0,0)-radial*.14,
                      p+(width/2,0,0)+radial*.14,
                      p+(-width/2,0,0)+radial*.14])
    mesh.loft(rings,path,0,material,loop=True)


def wheel(mesh, x,y,z, radius, width, detail, material='steel'):
    n=max(8,detail//2)
    rings=[]; centers=[]
    for dx,r in [(-width/2,.83*radius),(-width*.36,radius),(width*.36,radius),(width/2,.83*radius)]:
        centers.append((x+dx,y,z))
        rings.append([(x+dx,y+r*math.cos(i*2*math.pi/n),z+r*math.sin(i*2*math.pi/n)) for i in range(n)])
    mesh.loft(rings,centers,0,material)


def chassis(mesh,wreck=False):
    # A small two-track carrier, instead of the T2 launcher's broad three-prong hull.
    factor=.72 if wreck else 1
    shell(mesh,[(0,.95,-6.7,.5,.3),(0,1.4,-6.2,2.1,.8),
                (0,1.65,-4.5,2.7,1.15),(0,1.65,2.8,2.65,1.15),
                (0,1.5,5.6,2.0,.9),(0,1.45,6.5,.35,.25)],material='dark')
    shell(mesh,[(0,2.1*factor,-5.9,.5,.35),(0,2.6*factor,-4.8,2.2,.75),
                (0,2.8*factor,-2,2.45,.9),(0,2.65*factor,2.9,2.2,.65),
                (0,2.35*factor,5.6,.8,.4),(0,2.2*factor,6.0,.2,.12)])
    for side in (-1,1):
        x=side*(3.65+(.45 if wreck and side==1 else 0))
        zoffset=-.65 if wreck and side==1 else 0
        capsule_ring(mesh,x,zoffset,9.1,1.0,1.5)
        for z in ((-4.5,-1.5,1.5,4.5) if mesh.detail>=16 else (-4.5,0,4.5)):
            wheel(mesh,x,1.3,z+zoffset,.83,1.38,mesh.detail,'dark')
            if mesh.detail>=16:
                wheel(mesh,x+side*.74,1.3,z+zoffset,.48,.12,mesh.detail,'steel')
            if mesh.detail>=16:
                wheel(mesh,x+side*.83,1.3,z+zoffset,.21,.08,mesh.detail,'edge')
        # Rounded light fenders: open lower track sides, visibly simpler than T2.
        shell(mesh,[(x,1.9,-5.9+zoffset,.12,.16),(x,2.25,-5.25+zoffset,.88,.48),
                    (x,2.4,-2.5+zoffset,.98,.48),(x,2.4,2.7+zoffset,.98,.48),
                    (x,2.05,5.2+zoffset,.78,.4),(x,1.7,5.9+zoffset,.08,.1)],material='armor')
        # Thin continuous player-color trim. It is separate raised geometry.
        tube(mesh,[(x,2.8,-4.5+zoffset),(x,2.91,-1+zoffset),(x,2.91,2.5+zoffset),
                   (x,2.55,4.6+zoffset)],.045,'team',sides=6)
        if mesh.detail>=16:
            # Short tread cleats on the exposed lower run.
            for z in np.linspace(-4.35,4.35,13):
                tube(mesh,[(x-.77,.27,z+zoffset),(x+.77,.27,z+zoffset)],.075,'steel',sides=4)
        # Two compact shoulder plates, with broad silver fields between inlays.
        shell(mesh,[(side*1.7,2.9*factor,-3.9,.18,.18),
                    (side*1.8,3.05*factor,-2.8,.53,.38),
                    (side*1.7,2.95*factor,.5,.6,.34),
                    (side*1.45,2.75*factor,3.6,.4,.25),
                    (side*1.3,2.6*factor,4.2,.1,.1)],material='steel')
    # Small rear engine cover and cooling ribs, no tall aerials or decorative wings.
    shell(mesh,[(0,2.95*factor,-5.9,.5,.12),(0,3.15*factor,-5.3,1,.32),
                (0,3.2*factor,-3.8,1.05,.35),(0,3.0*factor,-3.5,.6,.15)],material='dark')
    if mesh.detail>=16:
        for z in np.linspace(-5.15,-3.95,5):
            tube(mesh,[(-.8,3.43*factor,z),(.8,3.43*factor,z)],.07,'steel',sides=6)
    # Launcher's compact transverse trunnion and saddle.
    for side in (-1,1):
        shell(mesh,[(side*.95,2.8*factor,-3.3,.3,.3),
                    (side*1.05,3.3*factor,-2.8,.5,.65),
                    (side*.95,3.3*factor,-2.2,.4,.6),
                    (side*.85,2.9*factor,-1.8,.25,.2)],material='dark')
        wheel(mesh,side*1.05,3.65*factor,-2.7,.47,.3,mesh.detail,'edge')


def launcher(detail,wreck=False):
    """New open twin-leaf cradle echoing XSL0111's silhouette, no copied vertices."""
    m=Mesh(detail)
    for side in (-1,1):
        end=5.6 if wreck and side==1 else 8.3
        shell(m,[(side*.65,-.05,-1.2,.12,.15),(side*.8,-.05,-.5,.38,.4),
                 (side*.91,0,1,.47,.49),(side*.9,.04,4.2,.45,.46),
                 (side*.72,.04,end-.7,.28,.27),(side*.59,.04,end,.08,.09)],
              material='armor')
        # Visible inner rails leave an open center around the launchable missile.
        tube(m,[(side*.46,.05,-.45),(side*.47,.1,3.5),(side*.43,.12,end-.3)],.09,'edge')
        tube(m,[(side*.93,.46,-.2),(side*1.02,.48,2.9),
                (side*.81,.37,end-1)],.036,'team',sides=6)
    shell(m,[(0,-.32,-1.4,.18,.16),(0,-.35,-.6,.78,.32),
             (0,-.35,1.1,.78,.25),(0,-.28,1.5,.35,.13)],material='dark')
    if detail>=16:
        # Restrained split tail brace at the cradle's heel.
        for side in (-1,1):
            tube(m,[(side*.45,-.05,-.8),(side*1.0,.13,-1.4),(side*1.25,.17,-1.6)],.1,'steel')
    return m


def rocket(detail):
    m=Mesh(detail)
    # Nose is at the missile bone origin: +Z is the real emission direction.
    shell(m,[(0,0,-6.4,.08,.08),(0,0,-6.1,.3,.3),(0,0,-1.5,.31,.31),
             (0,0,-.6,.2,.2),(0,0,0,.035,.035)],material='steel',sides=max(8,detail//2))
    for side in (-1,1):
        tube(m,[(side*.24,.22,-5.6),(side*.26,.23,-2)],.035,'team',sides=5)
    return m


def compact(mesh):
    mesh.smooth()
    vertices=[]; indices=[]; lookup={}
    for old in mesh.indices:
        v=mesh.vertices[old]
        key=tuple(round(float(x),7) for x in v[:16])+(int(v[16]),)
        if key not in lookup:
            lookup[key]=len(vertices); vertices.append(v)
        indices.append(lookup[key])
    mesh.vertices,mesh.indices=vertices,indices
    return mesh


def build(detail,wreck=False):
    mesh=Mesh(detail)
    chassis(mesh,wreck)
    if wreck:
        append_transformed(mesh,launcher(detail,True),rotate_x(math.radians(-8)),(.45,2.65,-3.1))
        # Broken forward rail on the ground beside the chassis.
        fragment=Mesh(detail)
        shell(fragment,[(0,.1,-1.2,.1,.1),(0,.2,0,.35,.25),(0,.15,1.5,.2,.18),
                        (0,.1,1.8,.08,.08)],material='steel')
        angle=math.radians(43)
        rot=np.array(((math.cos(angle),0,math.sin(angle)),(0,1,0),(-math.sin(angle),0,math.cos(angle))))
        append_transformed(mesh,fragment,rot,(3.0,.2,4.2))
    else:
        rotation=rotate_x(-ELEVATION)
        append_transformed(mesh,launcher(detail),rotation,PIVOTS[1],1)
        nose=np.array(PIVOTS[1])+rotation@PIVOTS[2]
        append_transformed(mesh,rocket(detail),rotation,nose,2)
    return compact(mesh)


def write_mesh_bp(path,prefix,shader='Seraphim',wreck=False):
    base=f'/mods/Project Roc Unicorns/{"props/GGA0101_wreck" if wreck else "units/GGA0101"}/'
    albedo='GGA0101_wreck_albedo.dds' if wreck else 'GGA0101_albedo.dds'
    maps='/mods/Project Roc Unicorns/units/GGA0101/'
    lods=[]
    for lod,cutoff in [(0,90),(1,220)]:
        lods.append(f"""        {{
            MeshName = '{base}{prefix}_lod{lod}.scm',
            AlbedoName = '{base if wreck else maps}{albedo}',
            SpecularName = '{'/env/common/props/wreckage_noise.dds' if wreck else maps+'GGA0101_specteam.dds'}',
            NormalsName = '{maps}GGA0101_normalsTS.dds',
            ShaderName = '{shader}',
            LookupName = '/textures/environment/Falloff_seraphim_lookup.dds',
            LODCutoff = {cutoff},
        }},""")
    path.write_text('MeshBlueprint {\n    IconFadeInZoom = 130,\n    LODs = {\n'+'\n'.join(lods)+'\n    },\n}\n',encoding='utf8')


def reload_animation():
    frames=[]
    for i in range(25):
        t=i/24
        # Dip and settle the cradle; preserve both local bind translations.
        angle=-ELEVATION+math.radians(7)*math.sin(math.pi*t)**2
        frames.append([((0,0,0),(1,0,0,0)),
                       (PIVOTS[1],(math.cos(angle/2),math.sin(angle/2),0,0))])
    write_sca(UNIT/'GGA0101_areload.sca',NAMES[:2],PARENTS[:2],frames,2.3333333)


def textures():
    make_textures(ASSETS,UNIT,save_dds_dxt5)
    color=np.array(Image.open(ASSETS/'GGA0101_albedo_source.png').convert('RGBA'))
    y,x=np.mgrid[:color.shape[0],:color.shape[1]]
    burn=.48+.25*(np.sin(x*.031+y*.012)*np.sin(y*.043-x*.008)+1)/2
    rgb=color[:,:,:3].astype(float)*burn[:,:,None]
    rgb+=np.array((10,8,6))
    color[:,:,:3]=np.clip(rgb,0,255).astype(np.uint8)
    color[:,:,3]=0
    im=Image.fromarray(color)
    im.save(ASSETS/'GGA0101_wreck_albedo_source.png')
    save_dds_dxt5(im,WRECK/'GGA0101_wreck_albedo.dds',independent_channels=True)


def previews():
    views=[]
    font=ImageFont.load_default(size=20)
    for label,a,e,team in [('Front',0,18,(.1,.8,.3)),('Side',90,12,(.1,.8,.3)),
                            ('Game view',35,34,(.1,.8,.3)),('Rear / blue team',145,24,(.12,.35,1))]:
        im=render_scm(UNIT/'GGA0101_lod0.scm',ASSETS,ASSETS/f'GGA0101_{label.split(" /")[0].lower().replace(" ","_")}.png',
                      a,e,team,720,texture_mip=1 if a==35 else 0)
        ImageDraw.Draw(im).text((20,20),label,fill=(220,230,240),font=font)
        views.append(im)
    sheet=Image.new('RGB',(1440,1440))
    for i,v in enumerate(views): sheet.paste(v,((i%2)*720,(i//2)*720))
    sheet.save(ASSETS/'GGA0101_views.png')
    render_scm(WRECK/'GGA0101_wreck_lod0.scm',ASSETS,ASSETS/'GGA0101_wreck.png',
               35,34,(.1,.8,.3),720,wreck=True)
    render_scm(UNIT/'GGA0101_lod1.scm',ASSETS,ASSETS/'GGA0101_lod1.png',35,34,(.1,.8,.3),540,texture_mip=3)
    icon=render_scm(UNIT/'GGA0101_lod0.scm',ASSETS,ASSETS/'GGA0101_icon_source.png',
                    35,34,(.16,.8,.3),512,transparent=True)
    icon=icon.resize((64,64),Image.Resampling.LANCZOS)
    for folder in (MOD/'icons/units',MOD/'textures/ui/common/icons/units'):
        save_dds_dxt5(icon,folder/'GGA0101_icon.dds')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-textures',action='store_true')
    parser.add_argument('--skip-previews',action='store_true')
    args=parser.parse_args()
    UNIT.mkdir(exist_ok=True); WRECK.mkdir(parents=True,exist_ok=True)
    stats={}
    for wreck in (False,True):
        for lod,detail in ((0,16),(1,8)):
            mesh=build(detail,wreck)
            prefix='GGA0101_wreck' if wreck else 'GGA0101'
            destination=WRECK if wreck else UNIT
            names,parents,pivots,rotations=([prefix],[-1],[(0,0,0)],None) if wreck else (NAMES,PARENTS,PIVOTS,ROTATIONS)
            write_scm(mesh,destination/f'{prefix}_lod{lod}.scm',names,parents,pivots,rotations)
            if lod==0 and not wreck: export_obj(mesh,ASSETS,NAMES)
            stats[f'{prefix}_lod{lod}']={'triangles':len(mesh.indices)//3,'vertices':len(mesh.vertices)}
            print(prefix,'LOD',lod,stats[f'{prefix}_lod{lod}'],flush=True)
    write_mesh_bp(UNIT/'GGA0101_mesh.bp','GGA0101')
    write_mesh_bp(WRECK/'GGA0101_wreck_mesh.bp','GGA0101_wreck','Wreckage',True)
    reload_animation()
    if not args.skip_textures: textures()
    if not args.skip_previews: previews()
    (ASSETS/'model_stats.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    main()
