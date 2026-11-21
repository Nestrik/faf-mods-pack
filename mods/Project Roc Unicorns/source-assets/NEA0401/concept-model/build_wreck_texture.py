"""Generate a charred material for the existing Halo Nest wreck mesh."""
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from supcom_binary import save_dds_dxt5

mod = HERE.parents[2]
source = mod / 'units/NEA0401/NEA0401_albedo.dds'
target = mod / 'props/NEA0401_wreck/NEA0401_wreck_albedo.dds'
rgba = np.array(Image.open(source).convert('RGBA'))
rgb = rgba[:, :, :3].astype(float)
luminance = rgb @ np.array([0.2126, 0.7152, 0.0722])
y, x = np.indices(luminance.shape)
burn = 0.14 + 0.06 * (np.sin(x * 0.031 + y * 0.012) * np.sin(y * 0.043 - x * 0.008) + 1) / 2
rgba[:, :, :3] = np.clip(luminance[:, :, None] * burn[:, :, None] * np.array([1.0, 0.95, 0.88]) + 3, 0, 255).astype(np.uint8)
rgba[:, :, 3] = 0
save_dds_dxt5(Image.fromarray(rgba), target, independent_channels=True)
