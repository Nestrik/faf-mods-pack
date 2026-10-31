"""Compile the native-model icon into both FAF UI lookup locations."""
from pathlib import Path
import sys,shutil
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from supcom_binary import save_dds_dxt5
MOD=HERE.parents[2]
OUT=MOD.parents[1]/'outputs/Dush_Nai_Icon_Targeting_v4'
art=Image.open(OUT/'Dush_Nai_icon_art.png').convert('RGBA')
icon=art.resize((64,64),Image.Resampling.LANCZOS)
rgb=icon.convert('RGB').filter(ImageFilter.UnsharpMask(radius=.6,percent=130,threshold=3));rgb.putalpha(icon.getchannel('A'));icon=rgb
icon.save(OUT/'Dush_Nai_icon_64.png');art.save(HERE/'Dush_Nai_icon_art.png')
for folder in ['icons/units','textures/ui/common/icons/units']:
 save_dds_dxt5(icon,MOD/folder/'GGA0401_icon.dds')
a=(MOD/'icons/units/GGA0401_icon.dds').read_bytes();b=(MOD/'textures/ui/common/icons/units/GGA0401_icon.dds').read_bytes();assert a==b
image=Image.open(MOD/'icons/units/GGA0401_icon.dds').convert('RGBA');assert image.size==(64,64)
image.resize((384,384),Image.Resampling.NEAREST).save(OUT/'Dush_Nai_icon_game_preview.png')
print('ICON_DDS_DONE',len(a))
