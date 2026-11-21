from pathlib import Path
from PIL import Image
import sys
base=Path(r'D:/Games/FafModsCreate/mods/Project Roc Unicorns')
s=Path(base/'source-assets/UEL0213/scm_preview.py').read_text().replace('UEL0210','UEL0213')
ns={'__name__':'icon_renderer'}
exec(compile(s,'icon_renderer','exec'),ns)
unit=base/'units/UEL0213';source=base/'source-assets/UEL0213'
ns['render_scm'](unit/'UEL0213_lod0.scm',source,source/'UEL0213_icon_render.png',35,28,size=512,transparent=True)
im=Image.open(source/'UEL0213_icon_render.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS)
im.save(source/'UEL0213_icon_source.png')
sys.path.insert(0,str(base/'source-assets/UEL0213'))
from supcom_binary import save_dds_dxt5
for folder in (base/'icons/units',base/'textures/ui/common/icons/units'):
 folder.mkdir(parents=True,exist_ok=True)
 save_dds_dxt5(im,folder/'UEL0213_icon.dds')
