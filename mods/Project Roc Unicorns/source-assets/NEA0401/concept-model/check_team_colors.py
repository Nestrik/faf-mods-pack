from pathlib import Path
import numpy as np
from PIL import Image
import geometry

here=Path(__file__).resolve().parent
original=geometry.load_dds_mip
for level in (0,1,4):
    data=np.asarray(original(here/'NEA0401_specteam.dds',level))
    h,w=data.shape[:2]
    def alpha(tile): return int(data[(tile//4*2+1)*h//4,(tile%4*2+1)*w//8,3])
    assert alpha(2)>240 and alpha(4)>240 and alpha(0)<15 and alpha(5)<15 and alpha(6)<15
def loader(path,level=0):
    im=original(path,level)
    if 'albedo' in Path(path).name:
        data=np.asarray(im).copy()
        spec=original(Path(path).with_name(Path(path).name.replace('albedo','specteam')),level)
        data[:,:,3]=np.asarray(spec)[:,:,3]
        return Image.fromarray(data)
    return im
geometry.load_dds_mip=loader
images=[]
for label,color in [('blue',(.12,.24,1.0)),('red',(1,.12,.08))]:
    images.append(geometry.render_scm(here/'NEA0401_concept_lod0.scm',here,here/f'NEA0401_team_{label}.png',azimuth=35,elevation=40,player=color,size=500,texture_mip=1))
sheet=Image.new('RGB',(1000,500))
for i,im in enumerate(images): sheet.paste(im,(500*i,0))
sheet.save(here/'NEA0401_team_colors.png')
print('Team mask checked on mip levels 0, 1, 4; previews rendered.')
