from pathlib import Path
import numpy as np
from PIL import Image
import geometry

here=Path(__file__).resolve().parent
original=geometry.load_dds_mip
def loader(path,level=0):
    im=original(path,level)
    if 'albedo' in Path(path).name:
        data=np.asarray(im).copy()
        spec=original(Path(path).with_name(Path(path).name.replace('albedo','specteam')),level)
        data[:,:,3]=np.asarray(spec)[:,:,3]
        return Image.fromarray(data)
    return im
geometry.load_dds_mip=loader
geometry.render_scm(here/'NEA0401_concept_lod0.scm',here,here/'NEA0401_crystal_mist_preview.png',
                    azimuth=35,elevation=30,size=800,texture_mip=1)
