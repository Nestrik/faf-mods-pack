from pathlib import Path
import math,sys
from PIL import Image
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent))
from supcom_binary import save_dds_dxt5

image=Image.new('RGBA',(256,4))
for x in range(256):
    t=x/255
    opacity=round(80*(math.sin(math.pi*t)**1.3))
    color=(12,78,71,opacity)
    for y in range(4): image.putpixel((x,y),color)
target=here.parents[2]/'textures'/'particles'/'nea0401_crystal_mist_ramp.dds'
image.save(here/'NEA0401_crystal_mist_ramp_source.png')
save_dds_dxt5(image,target)
print(target)
