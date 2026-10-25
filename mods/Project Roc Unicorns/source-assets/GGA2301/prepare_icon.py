"""Package original transparent Ishal-Thar artwork for the FAF build menu."""
from pathlib import Path
from io import BytesIO
import struct
from PIL import Image

ASSETS = Path(__file__).resolve().parent
MOD = ASSETS.parents[1]


def save_icon_dds(image, path):
    """Use Pillow's BC3 encoder; alpha is real transparency for this artwork."""
    current = image
    levels = []
    while True:
        stream = BytesIO()
        current.save(stream, format='DDS', pixel_format='DXT5')
        levels.append(stream.getvalue()[128:])
        if current.size == (1, 1):
            break
        current = current.resize((max(1, current.width//2), max(1, current.height//2)),
                                 Image.Resampling.LANCZOS)
    w, h = image.size
    header = [124, 0xA1007, h, w, ((w+3)//4)*((h+3)//4)*16, 0, len(levels)]
    header += [0]*11 + [32, 4, 0x35545844, 0, 0, 0, 0, 0] + [0x401008, 0, 0, 0, 0]
    path.write_bytes(b'DDS ' + struct.pack('<31I', *header) + b''.join(levels))

if __name__ == '__main__':
    source = Image.open(ASSETS / 'GGA2301_icon_generated.png').convert('RGBA')
    # Keep all generated artwork with transparent padding around the silhouette.
    icon = Image.new('RGBA', (64, 64))
    source.thumbnail((60, 60), Image.Resampling.LANCZOS)
    icon.paste(source, ((64-source.width)//2, (64-source.height)//2))
    icon.save(ASSETS / 'GGA2301_icon_64.png')
    for folder in ('icons/units', 'textures/ui/common/icons/units'):
        save_icon_dds(icon, MOD / folder / 'GGA2301_icon.dds')
    decoded = Image.open(MOD / 'icons/units/GGA2301_icon.dds').convert('RGBA')
    decoded.resize((384, 384), Image.Resampling.NEAREST).save(ASSETS / 'GGA2301_icon_game_preview.png')
    print('Packaged matching 64x64 BC3 icons with transparency and seven mip levels.')
