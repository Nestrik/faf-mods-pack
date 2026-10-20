"""Build GGA2401's original five-launcher SCMs, materials and SCM previews.

Run with Python + numpy + Pillow. Y up, +Z forward, game scale 0.1.
The common yaw/pitch cradle aims all five parallel launch tubes together.
"""
from pathlib import Path
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from artillery_geometry import Mesh, export_obj, make_textures, render_scm
from supcom_binary import write_scm, save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
UNIT = ASSETS.parents[1] / 'units' / 'GGA2401'
NAMES = ['GGA2401', 'Turret', 'Turret_Barrel'] + [f'Muzzle_{i:02}' for i in range(1, 6)]
PARENTS = [-1, 0, 1] + [2] * 5
LAUNCHERS = [(-12, -2), (-6, 0), (0, 2), (6, 0), (12, -2)]
PIVOTS = [(0, 0, 0), (0, 8, 0), (0, 3.5, 0)] + [(x, 0, z + 10.1) for x, z in LAUNCHERS]


def translated(mesh, offset, operation):
    start = len(mesh.vertices)
    operation()
    for i in range(start, len(mesh.vertices)):
        vertex = mesh.vertices[i]
        mesh.vertices[i] = tuple(np.array(vertex[:3]) + offset) + vertex[3:]


def tube(mesh, x, z, profile, material='edge'):
    """Closed cross-section around a real open bore; no cap over the muzzle."""
    rings, centers = [], []
    radius_mid = (min(r for r, _ in profile) + max(r for r, _ in profile)) / 2
    z_mid = (min(f for _, f in profile) + max(f for _, f in profile)) / 2
    for a in range(mesh.detail):
        angle = a * 2 * math.pi / mesh.detail
        rings.append([(x + radius * math.cos(angle), 11.5 + radius * math.sin(angle), z + forward)
                      for radius, forward in profile])
        centers.append((x + radius_mid * math.cos(angle), 11.5 + radius_mid * math.sin(angle), z + z_mid))
    mesh.loft(rings, centers, 2, material, loop=True)


def build_mesh(detail):
    m = Mesh(detail)
    # Low layered platform fits within the 4 x 4 placement square (3.8 diameter).
    m.column([(16.5, 0), (18.5, .5), (19, 1.2), (18.5, 2.1), (16.8, 2.7)], material='dark')
    m.annulus(16.0, 18.7, 1.7, 2.5, material='edge')
    m.column([(15.8, 2.6), (15.4, 3.3), (13, 3.7)], material='armor')
    m.annulus(12.3, 13.1, 3.7, 3.95, material='team')
    m.column([(8.5, 3.7), (8.5, 4.3), (7.1, 5.2), (6.5, 6.2)], material='steel')
    m.annulus(6.2, 7.3, 5.8, 6.4, material='edge')
    # Four swept buttresses and radial player-color conduits.
    for i in range(4):
        angle = math.pi / 4 + i * math.pi / 2
        m.foot([(7, 4.7, 1.2, .5), (12, 3.9, 2.2, .65), (17.3, 2.0, 2.4, .6)], angle, 'armor')
        m.foot([(8.6, 5.0, .18, .12), (12.0, 4.6, .20, .12), (16.4, 2.9, .18, .12)], angle, 'team')
    # The yaw carriage and two smooth side cheeks support the elevating cradle.
    m.column([(6.3, 6.2), (6.1, 7.7), (4.5, 8.5)], bone=1, material='dark')
    for x in (-5.1, 5.1):
        translated(m, (x, 0, 0), lambda: m.column([(2.1, 7.0), (2.4, 9.3), (1.9, 11.8)], bone=1, material='armor'))
    # Curved rear beam joining the five pods; rigidly attached to pitch bone.
    rings = []
    centers = []
    for x, z in LAUNCHERS:
        center = np.array((x, 10.3, z - 1.5))
        centers.append(center)
        rings.append([center + (0, dy, dz) for dy, dz in [(-.9, -1.5), (.9, -1.5), (1.2, 0), (.9, 1.5), (-.9, 1.5), (-1.2, 0)]])
    m.loft(rings, centers, 2, 'steel')
    for x, z in LAUNCHERS:
        # Elliptical organic shell tapering to the artillery launch aperture.
        sections = [(-5.5, .55, .65), (-4.5, 1.7, 1.6), (-1.5, 2.45, 2.4),
                    (2.0, 2.35, 2.25), (5.0, 1.9, 1.8), (7.8, 1.35, 1.25)]
        rings, centers = [], []
        for forward, width, height in sections:
            centers.append((x, 11.5, z + forward))
            rings.append([(x + width * math.cos(a * 2 * math.pi / detail),
                           11.5 + height * math.sin(a * 2 * math.pi / detail), z + forward)
                          for a in range(detail)])
        m.loft(rings, centers, 2, 'armor')
        # A dark recessed bore, thick chrome rim and a luminous inner collar.
        tube(m, x, z, [(1.2, 6.6), (1.4, 7.5), (1.4, 9.5), (1.25, 10),
                        (.88, 10), (.82, 9.5), (.82, 7.5), (.9, 6.6)], 'edge')
        tube(m, x, z, [(.83, 7.3), (.86, 7.5), (.86, 9.25), (.82, 9.4),
                        (.73, 9.4), (.73, 7.3)], 'joint')
        tube(m, x, z, [(.84, 9.15), (.9, 9.25), (.9, 9.5), (.84, 9.6),
                        (.74, 9.6), (.74, 9.15)], 'team')
        # Narrow dorsal power spine follows the curved housing.
        spine_rings = []
        spine_centers = []
        for forward, height in [(-4, 1.7), (-1.5, 2.45), (2, 2.3), (5, 1.85), (7.2, 1.35)]:
            c = np.array((x, 11.5 + height, z + forward))
            spine_centers.append(c)
            spine_rings.append([c + (dx, dy, 0) for dx, dy in [(-.17, -.05), (.17, -.05), (.17, .15), (-.17, .15)]])
        m.loft(spine_rings, spine_centers, 2, 'team')
    m.smooth()
    return m


def main():
    UNIT.mkdir(parents=True, exist_ok=True)
    for lod, detail in ((0, 24), (1, 12)):
        mesh = build_mesh(detail)
        write_scm(mesh, UNIT / f'GGA2401_lod{lod}.scm', NAMES, PARENTS, PIVOTS)
        if lod == 0:
            export_obj(mesh, ASSETS)
        print(f'LOD{lod}: {len(mesh.indices)//3} triangles / {len(mesh.vertices)} vertices', flush=True)
    make_textures(ASSETS, UNIT, save_dds_dxt5)
    views = []
    for name, azimuth, elevation, color in [('Front', 0, 17, (.12, .32, 1)),
                                           ('Side', 90, 15, (.12, .32, 1)),
                                           ('Game view', 35, 48, (.95, .22, .1))]:
        im = render_scm(UNIT / 'GGA2401_lod0.scm', ASSETS, ASSETS / f'GGA2401_{name.lower().replace(" ", "_")}.png',
                        azimuth, elevation, color, 720)
        ImageDraw.Draw(im).text((24, 24), name, fill=(220, 230, 240), font=ImageFont.load_default(size=20))
        views.append(im)
    sheet = Image.new('RGB', (2160, 720))
    for i, view in enumerate(views):
        sheet.paste(view, (i * 720, 0))
    sheet.save(ASSETS / 'GGA2401_views.png')
    print('Exported GGA2401 model and previews.', flush=True)


if __name__ == '__main__':
    main()
