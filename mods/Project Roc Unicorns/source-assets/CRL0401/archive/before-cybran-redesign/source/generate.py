"""Generate the CRL0401 prototype, using the project's SCM/DDS writer."""
from pathlib import Path
import math
from PIL import Image, ImageDraw
from model_geometry import Mesh
from supcom_binary import write_scm, save_dds_dxt5

HERE = Path(__file__).resolve().parent
UNIT = HERE.parents[1] / 'units' / 'CRL0401'

def box(m, x, y, z, sx, sy, sz, mat):
    rings = [[(x-sx/2,y-sy/2,z+q*sz/2),(x+sx/2,y-sy/2,z+q*sz/2),
              (x+sx/2,y+sy/2,z+q*sz/2),(x-sx/2,y+sy/2,z+q*sz/2)] for q in (-1,1)]
    m.loft(rings, [(x,y,z-sz/2),(x,y,z+sz/2)], material=mat)

def wheel(m, x, z):
    n=m.detail
    rings=[]
    centers=[]
    for dx,r in [(-.19,.32),(-.15,.38),(.15,.38),(.19,.32)]:
        centers.append((x+dx,.4,z))
        rings.append([(x+dx,.4+r*math.cos(i*2*math.pi/n),z+r*math.sin(i*2*math.pi/n)) for i in range(n)])
    m.loft(rings,centers,material='dark')

def model(detail):
    m=Mesh(detail)
    box(m,0,.71,0,2.35,.42,2.8,'dark')
    box(m,0,.99,0,2.13,.2,2.45,'armor')
    for side in (-1,1):
        for z in (-1.02,-.34,.34,1.02): wheel(m,side*1.27,z)
        box(m,side*1.0,1.12,0,.12,.12,2.45,'team')
    box(m,0,1.3,0,1.48,.52,1.52,'steel')
    box(m,0,1.75,0,1.15,.42,1.18,'armor')
    m.column([(0.5,1.95),(.62,2.1),(.55,2.3),(.3,2.48)],material='dark')
    for side in (-1,1):
        box(m,side*.73,1.66,0,.22,.84,.65,'dark')
        box(m,side*.76,2.05,0,.33,.16,.85,'team')
    box(m,0,2.52,0,.22,.13,.8,'team')
    return m

def textures():
    colors=[(75,72,70,0),(29,31,34,0),(105,99,93,0),(115,112,108,0),
            (125,125,125,0),(75,35,30,0),(220,50,30,0),(38,38,40,0)]
    al=Image.new('RGBA',(256,128)); draw=ImageDraw.Draw(al)
    for i,c in enumerate(colors): draw.rectangle(((i%4)*64,(i//4)*64,(i%4+1)*64-1,(i//4+1)*64-1),fill=c)
    spec=Image.new('RGBA',al.size,(90,115,0,0))
    ImageDraw.Draw(spec).rectangle((0,64,63,127),fill=(90,115,0,255))
    normal=Image.new('RGBA',al.size,(128,128,255,128))
    for name,img in [('albedo',al),('specteam',spec),('normalsTS',normal)]:
        img.save(HERE / ('CRL0401_'+name+'.png'))
        save_dds_dxt5(img,UNIT/('CRL0401_'+name+'.dds'),independent_channels=True)

if __name__ == '__main__':
    UNIT.mkdir(parents=True,exist_ok=True)
    for lod,detail in [(0,16),(1,8)]:
        mesh=model(detail)
        write_scm(mesh,UNIT/f'CRL0401_lod{lod}.scm',['CRL0401','BuildPoint'],[-1,0],[(0,0,0),(0,2.5,0)])
        print('LOD',lod,'triangles',len(mesh.indices)//3)
    textures()
