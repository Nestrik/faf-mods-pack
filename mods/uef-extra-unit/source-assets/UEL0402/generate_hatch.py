from pathlib import Path
import math
from PIL import Image, ImageDraw
from geometry import Mesh, render_scm
from supcom_binary import write_scm, save_dds_dxt5

source = Path(__file__).resolve().parent
out = source.parents[1] / 'meshes' / 'launch-hatch'
out.mkdir(parents=True, exist_ok=True)
m = Mesh(48)
# Annular frame and a deeply recessed dark centre. Dimensions are game units.
m.annulus(1.95, 2.45, 0.00, 0.20, material='edge')
m.annulus(1.62, 1.95, 0.02, 0.13, material='steel')
for i in range(48):
    a, b = 2*math.pi*i/48, 2*math.pi*(i+1)/48
    m.face([(0,.025,0),(1.70*math.cos(b),.025,1.70*math.sin(b)),(1.70*math.cos(a),.025,1.70*math.sin(a))], material='dark', outward=(0,1,0))
# Overlapping, fixed iris leaves leave a dark opening at the centre.
for i in range(8):
    a = i * math.pi/4
    def p(r, angle, y): return (r*math.cos(angle),y,r*math.sin(angle))
    m.face([p(.50,a+.35,.07+i*.001),p(1.70,a-.05,.07+i*.001),p(1.70,a+.72,.07+i*.001),p(.50,a+.62,.07+i*.001)], material='steel', outward=(0,1,0))
    m.face([p(.53,a+.35,.075+i*.001),p(1.67,a-.05,.075+i*.001),p(1.67,a+.00,.075+i*.001),p(.54,a+.40,.075+i*.001)], material='edge', outward=(0,1,0))
write_scm(m, out/'launch_hatch_lod0.scm', ['LaunchHatch'], [-1], [(0,0,0)])
# Atlas used by Mesh: eight independent material tiles; no transparency.
colors=[(88,99,105,255),(18,23,28,255),(155,167,174,255),(68,80,88,255),(50,80,115,255),(80,95,105,255),(90,120,130,255),(30,37,42,255)]
albedo=Image.new('RGBA',(128,128)); draw=ImageDraw.Draw(albedo)
for i,col in enumerate(colors):
    x,y=(i%4)*32,(i//4)*64
    draw.rectangle((x,y,x+31,y+63),fill=col)
spec=Image.new('RGBA',(128,128),(130,145,0,0))
norm=Image.new('RGBA',(128,128),(128,128,255,128))
for suffix,im in [('albedo',albedo),('specteam',spec),('normalsTS',norm)]:
    im.save(source/('launch_hatch_'+suffix+'_source.png'))
    save_dds_dxt5(im,out/('launch_hatch_'+suffix+'.dds'),independent_channels=True)
for name,az,el in [('top',0,89),('side',90,18),('perspective',35,43)]:
    render_scm(out/'launch_hatch_lod0.scm',source,source/('launch_hatch_'+name+'.png'),az,el,size=600)
print('vertices',len(m.vertices),'triangles',len(m.indices)//3)
