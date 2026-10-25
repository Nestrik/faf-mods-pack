"""Rebuild only Ishal-Thar's material DDS and exported-SCM previews."""
from pathlib import Path
from prism_reference_model import make_textures, make_previews
from supcom_binary import save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
UNIT = ASSETS.parents[1] / 'units' / 'GGA2301'

if __name__ == '__main__':
    make_textures(ASSETS, UNIT, save_dds_dxt5)
    make_previews(UNIT, ASSETS)
    print('Rebuilt material maps and DDS/SCM previews; geometry and animations untouched.')
