"""Package the generated transparent artwork into both FAF unit-icon locations."""
from pathlib import Path
from PIL import Image
from supcom_binary import save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
MOD = ASSETS.parents[1]


def main():
    source = Image.open(ASSETS / 'GGA2401_icon_generated.png').convert('RGBA')
    # Preserve the generated artwork and alpha; only resample for the game UI.
    icon = source.resize((64, 64), Image.Resampling.LANCZOS)
    icon.save(ASSETS / 'GGA2401_icon_64.png')
    for relative in ('icons/units', 'textures/ui/common/icons/units'):
        save_dds_dxt5(icon, MOD / relative / 'GGA2401_icon.dds')
    decoded = Image.open(MOD / 'icons/units/GGA2401_icon.dds').convert('RGBA')
    decoded.resize((384, 384), Image.Resampling.NEAREST).save(ASSETS / 'GGA2401_icon_game_preview.png')
    print('Prepared two matching 64x64 BC3/DXT5 unit icons with seven mip levels.')


if __name__ == '__main__':
    main()
