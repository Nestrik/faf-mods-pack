"""Render Mobile Hive's construction icon from its exported SCM and DDS maps."""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from model_geometry import render_scm
from supcom_binary import save_dds_dxt5

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
MODEL = MOD / 'units/CRL0401/CRL0401_lod0.scm'

render = render_scm(MODEL, HERE, HERE / 'CRL0401_icon_render.png',
                    azimuth=35, elevation=38, player=(.9, .08, .06),
                    size=512, transparent=True)
icon = render.resize((64, 64), Image.Resampling.LANCZOS)
alpha = icon.getchannel('A')
rgb = ImageEnhance.Brightness(icon.convert('RGB')).enhance(1.4)
rgb = rgb.filter(ImageFilter.UnsharpMask(radius=.6, percent=120, threshold=3))
rgb.putalpha(alpha)
icon = rgb
icon.save(HERE / 'CRL0401_icon_source.png')
paths = [MOD / 'icons/units/CRL0401_icon.dds',
         MOD / 'textures/ui/common/icons/units/CRL0401_icon.dds']
for path in paths:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Icon alpha is real transparency; use ordinary premultiplied-alpha resize
    # for its mipmaps, unlike the unit's packed material-data textures.
    save_dds_dxt5(icon, path)
assert paths[0].read_bytes() == paths[1].read_bytes()
decoded = Image.open(paths[0]).convert('RGBA')
assert decoded.size == (64, 64) and decoded.getchannel('A').getextrema() == (0, 255)
background = Image.new('RGB', (64, 64), (33, 38, 45))
background.paste(decoded, mask=decoded.getchannel('A'))
background.resize((384, 384), Image.Resampling.NEAREST).save(HERE / 'CRL0401_icon_preview.png')
print('Created identical 64x64 BC3 icons in both FAF lookup locations.')
