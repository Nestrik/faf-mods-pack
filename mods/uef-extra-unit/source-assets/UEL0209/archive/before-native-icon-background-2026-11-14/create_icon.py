from pathlib import Path
from PIL import Image, ImageOps
from supcom_binary import save_dds_dxt5
h=Path(__file__).resolve().parent
mod=h.parents[1]
im=Image.open(h/'perspective.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS)
for folder in [mod/'icons/units',mod/'textures/ui/common/icons/units']:
 folder.mkdir(parents=True,exist_ok=True); save_dds_dxt5(im,folder/'UEL0209_icon.dds')
