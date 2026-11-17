from pathlib import Path
import shutil,sys
from PIL import Image
src=Path(__file__).resolve().parent;mod=src.parents[1];unit=mod/'units/NEL0208';stage=src/'icon_render';stage.mkdir(exist_ok=True)
from geometry import render_scm
from supcom_binary import save_dds_dxt5
for k in ['albedo','specteam','normalsTS']:shutil.copy2(unit/('NEL0208_'+k+'.dds'),stage/('rocket_rack_'+k+'.dds'))
shutil.copy2(unit/'NEL0208_lod0.scm',stage/'NEL0208_lod0.scm')
render_scm(stage/'NEL0208_lod0.scm',src,src/'NEL0208_icon_render.png',35,35,size=512,transparent=True)
im=Image.open(src/'NEL0208_icon_render.png').convert('RGBA').resize((64,64),Image.Resampling.LANCZOS);im.save(src/'NEL0208_icon_source.png');im.resize((320,320),Image.Resampling.NEAREST).save(src/'NEL0208_icon_preview.png')
for folder in [mod/'icons/units',mod/'textures/ui/common/icons/units']:
 folder.mkdir(parents=True,exist_ok=True);save_dds_dxt5(im,folder/'NEL0208_icon.dds')
print('created icon for NEL0208 from active SCM',flush=True)
