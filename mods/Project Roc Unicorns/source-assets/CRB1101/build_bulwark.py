"""Rebuild the Bulwark mechanical shield projector in game units (Y up)."""
from pathlib import Path
from math import pi, sin, cos
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
UNIT = HERE.parents[1] / 'units' / 'CRB1101'
from model_geometry import Mesh, MATERIALS, render_scm, load_scm
from supcom_binary import write_scm, save_dds_dxt5


def shell(mesh, outline, levels, angle, material, bone=0):
    """Extrude a beveled footprint about its own center and rotate around the hub."""
    points = np.array(outline)
    center = points.mean(axis=0)
    rings, centers = [], []
    for y, scale in levels:
        ring = []
        for x, z in center + scale * (points - center):
            ring.append((x*cos(angle)+z*sin(angle), y, z*cos(angle)-x*sin(angle)))
        rings.append(ring)
        centers.append(np.mean(ring, axis=0))
    mesh.loft(rings, centers, material=material, bone=bone)


def geometry(detailed):
    mesh = Mesh(12 if detailed else 8)
    mesh.column([(.45,0),(.51,.055),(.51,.17),(.43,.24)], material='dark')
    mesh.column([(.33,.17),(.33,.32),(.29,.37)], material='armor')
    mesh.column([(.305,.345),(.32,.375),(.32,.40),(.265,.42)], material='edge')
    mesh.column([(.255,.41),(.255,.50)], material='joint')
    mesh.column([(.28,.48),(.305,.505),(.285,.56)], bone=1, material='steel')
    if detailed:
        for i in range(18):
            angle=2*pi*i/18
            shell(mesh,[(-.012,.246),(.012,.246),(.012,.264),(-.012,.264)],
                  [(.415,1),(.478,1)],angle,'edge')
    foot = [(-.16,.23),(.16,.23),(.28,.47),(.27,.68),(.155,.81),(-.155,.81),(-.27,.68),(-.28,.47)]
    for i in range(3):
        angle = i * 2*pi/3
        shell(mesh, foot, [(0,.92),(.045,1),(.14,1),(.235,.84)], angle, 'armor')
        # Two red armor insets frame the ribbed vent on each foot.
        for hand in (-1,1):
            panel = [(hand*x,z) for x,z in [(.07,.51),(.18,.48),(.215,.59),(.14,.719),(.072,.729)]]
            shell(mesh, panel, [(.232,.94),(.242,1)], angle, 'team')
        if detailed:
            for hand in (-1,1):
                outline=[(hand*.166+.014*cos(j*pi/3),.416+.014*sin(j*pi/3)) for j in range(6)]
                shell(mesh,outline,[(.233,1),(.246,.8)],angle,'steel')
            for z in (.58,.62,.66,.70,.74):
                shell(mesh,[(-.048,z),(.048,z),(.048,z+.015),(-.048,z+.015)],
                      [(.228,1),(.247,.95)], angle,'steel')
        # Rigid radial brackets cantilever each spire from the moving hub.
        arm = [(-.083,.21),(.083,.21),(.089,.50),(.063,.61),(-.063,.61),(-.089,.50)]
        shell(mesh, arm, [(.487,.91),(.51,1),(.56,.94)], angle, 'armor', bone=1)

        def tower(radius, levels, material, sides=6):
            if not detailed:
                sides = 4
                levels = [levels[0],levels[-1]]
            outline=[(radius*cos(2*pi*j/sides),.54+radius*sin(2*pi*j/sides)) for j in range(sides)]
            shell(mesh,outline,levels,angle,material,bone=1)
        tower(.094,[(.52,1),(.59,.93),(.66,.57)],'dark')
        tower(.055,[(.645,1),(.74,.78),(1.49,.48)],'steel',4)
        tower(.03,[(1.48,1),(1.55,.76),(1.80,.045)],'edge',4)

    # A steel spindle shows through the slots between four separate bolted vanes.
    mesh.column([(.095,.54),(.095,1.73),(.074,1.79)],bone=1,material='joint',sides=8)
    for y in (.65,1.09,1.56):
        mesh.column([(.10,y),(.155,y+.018),(.155,y+.057),(.10,y+.07)],bone=1,material='steel',sides=8)

    for i in range(4):
        angle = pi/4+i*pi/2
        def plate(profile, material):
            rings=[]
            for y,w,inner,outer in profile:
                # Chamfer both outer corners of each machined plate.
                local=[(-w,inner),(w,inner),(w,outer-.012),(.79*w,outer),
                       (-.79*w,outer),(-w,outer-.012)]
                rings.append([(x*cos(angle)+z*sin(angle),y,z*cos(angle)-x*sin(angle)) for x,z in local])
            mesh.loft(rings,[np.mean(r,axis=0) for r in rings],bone=1,material=material)
        plate([(.615,.052,.084,.16),(.92,.124,.115,.245),(1.48,.118,.105,.21),
               (1.84,.060,.083,.166),(1.98,.033,.079,.125)],'dark')
        # The narrow gap between armor panels exposes the backing and breaks up the silhouette.
        plate([(.72,.050,.152,.205),(.94,.096,.202,.254),(1.115,.095,.196,.244)],'team')
        plate([(1.146,.094,.183,.245),(1.46,.094,.17,.227),(1.80,.047,.135,.185),
               (1.918,.023,.108,.15)],'team')
        if detailed:
            for j in range(3):
                y=1.18+j*.052
                z=.245-(y-1.146)*.057
                plate([(y,.055,z-.007,z+.009),(y+.009,.05,z-.007,z+.008)],'joint')
    return mesh


def materials():
    # 4 x 2 atlas tiles in the same order as the mesh UV writer.
    palette = {
        'armor': ((59,63,68),(95,100,0,0)), 'dark': ((33,36,42),(70,70,0,0)),
        'edge': ((113,119,126),(145,180,0,0)), 'steel': ((84,89,98),(139,155,0,0)),
        'team': ((106,106,106),(100,140,0,190)), 'crystal': ((208,12,29),(125,212,100,0)),
        'lens': ((154,5,24),(130,205,94,0)), 'joint': ((42,45,47),(83,80,0,0)),
    }
    w,h = 256,128
    maps = [np.zeros((h,w,4),np.uint8) for _ in range(3)]
    y,x = np.mgrid[0:64,0:64]
    noise=np.random.default_rng(1101).normal(0,1.3,(64,64))
    for i,name in enumerate(MATERIALS):
        color, packed=palette[name]
        grain=noise.copy()
        if name in ('crystal','lens'):
            grain += 13*np.sin(x*.038+y*.064) + 19*np.exp(-abs((x+.47*y)%48-25)/1.5)
        if name=='joint':
            grain+=(x%8<2)*22
        region=np.s_[i//4*64:(i//4+1)*64,i%4*64:(i%4+1)*64]
        maps[0][region][:,:,:3]=np.clip(np.array(color)+grain[:,:,None],0,255)
        maps[0][region][:,:,3]=255
        maps[1][region]=packed
        maps[2][region]=(128,128,255,128)
    for data,suffix in zip(maps,['albedo','specteam','normalsTS']):
        save_dds_dxt5(Image.fromarray(data),UNIT/f'CRB1101_{suffix}.dds',independent_channels=True)


if __name__ == '__main__':
    materials()
    for lod in (0,1):
        path=UNIT/f'CRB1101_lod{lod}.scm'
        write_scm(geometry(lod==0),path,['CRB1101','ShieldRotor'],[-1,0],[(0,0,0),(0,.48,0)])
        vertices,faces=load_scm(path)
        assert faces.max()<len(vertices) and np.allclose(np.linalg.norm(vertices[:,3:6],axis=1),1)
        print(path.name, len(vertices),'vertices,',len(faces),'triangles')
    views=[]
    for angle,elev in [(12,19),(60,4),(0,89.9)]:
        views.append(render_scm(UNIT/'CRB1101_lod0.scm',HERE,HERE/'bulwark-preview.png',
                                angle,elev,player=(.66,.06,.82),size=440,texture_prefix='CRB1101'))
    sheet=Image.new('RGB',(440*3,440))
    for i,view in enumerate(views):
        sheet.paste(view,(i*440,0))
    sheet.save(HERE/'bulwark-preview.png')
