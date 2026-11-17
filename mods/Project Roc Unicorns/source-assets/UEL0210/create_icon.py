from pathlib import Path
from PIL import Image
from scm_preview import render_scm
from supcom_binary import save_dds_dxt5
h=Path(__file__).resolve().parent;mod=h.parents[1];unit=mod/'units/UEL0210'
render_scm(unit/'UEL0210_lod0.scm',h,h/'UEL0210_icon_render.png',35,28,size=512,transparent=True)
im=Image.open(h/'UEL0210_icon_render.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS);im.save(h/'UEL0210_icon_source.png')
for folder in (mod/'icons/units',mod/'textures/ui/common/icons/units'):
 folder.mkdir(parents=True,exist_ok=True);save_dds_dxt5(im,folder/'UEL0210_icon.dds')
