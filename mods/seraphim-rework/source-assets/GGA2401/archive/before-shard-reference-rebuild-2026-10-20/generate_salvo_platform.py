"""Build GGA2401's five-level floating artillery tower and SCM previews.

Run with Python + numpy + Pillow. Y up, +Z forward, game scale 0.1.
The islands share yaw. Each barrel pitches about its own island's local hinge.
"""
from pathlib import Path
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from artillery_geometry import Mesh, export_obj, make_textures, render_scm
from supcom_binary import write_scm, save_dds_dxt5

ASSETS = Path(__file__).resolve().parent
UNIT = ASSETS.parents[1] / 'units' / 'GGA2401'
ISLANDS = [(-8, 13, -2), (7.8, 25, 1.5), (-6.5, 37, 5),
           (8, 49, -4.5), (-4.5, 61, -5)]
NAMES = ['GGA2401', 'Turret']
PARENTS = [-1, 0]
PIVOTS = [(0, 0, 0), (0, 0, 0)]
ISLAND_BONES, BARREL_BONES = [], []
for i, position in enumerate(ISLANDS, 1):
    island, barrel = len(NAMES), len(NAMES) + 1
    ISLAND_BONES.append(island)
    BARREL_BONES.append(barrel)
    NAMES += [f'Island_{i:02}', 'Turret_Barrel' if i == 3 else f'Barrel_{i:02}', f'Muzzle_{i:02}']
    PARENTS += [1, island, barrel]
    # Rear hinge keeps the breech clear of the island through 0..90 deg elevation.
    PIVOTS += [position, (0, 3.8, -4), (0, 0, 14.1)]


def translated(mesh, offset, operation):
    start = len(mesh.vertices)
    operation()
    for i in range(start, len(mesh.vertices)):
        vertex = mesh.vertices[i]
        mesh.vertices[i] = tuple(np.array(vertex[:3]) + offset) + vertex[3:]


def tube(mesh, profile, material='edge'):
    """Closed cross-section around a real open bore; no cap over the muzzle."""
    rings, centers = [], []
    radius_mid = (min(r for r, _ in profile) + max(r for r, _ in profile)) / 2
    z_mid = (min(f for _, f in profile) + max(f for _, f in profile)) / 2
    for a in range(mesh.detail):
        angle = a * 2 * math.pi / mesh.detail
        rings.append([(radius * math.cos(angle), radius * math.sin(angle), forward)
                      for radius, forward in profile])
        centers.append((radius_mid * math.cos(angle), radius_mid * math.sin(angle), z_mid))
    mesh.loft(rings, centers, 0, material, loop=True)


def launcher(detail):
    """One organic silver cannon, centred on its own pitch hinge."""
    m = Mesh(detail)
    sections = [(-5.5, .55, .65), (-4.5, 1.7, 1.6), (-1.5, 2.45, 2.4),
                (2.0, 2.35, 2.25), (5.0, 1.9, 1.8), (7.8, 1.35, 1.25)]
    rings, centers = [], []
    for forward, width, height in sections:
        centers.append((0, 0, forward))
        rings.append([(width * math.cos(a * 2 * math.pi / detail),
                       height * math.sin(a * 2 * math.pi / detail), forward)
                      for a in range(detail)])
    m.loft(rings, centers, 0, 'armor')
    tube(m, [(1.2, 6.6), (1.4, 7.5), (1.4, 9.5), (1.25, 10),
             (.88, 10), (.82, 9.5), (.82, 7.5), (.9, 6.6)], 'edge')
    tube(m, [(.83, 7.3), (.86, 7.5), (.86, 9.25), (.82, 9.4),
             (.73, 9.4), (.73, 7.3)], 'joint')
    tube(m, [(.84, 9.15), (.9, 9.25), (.9, 9.5), (.84, 9.6),
             (.74, 9.6), (.74, 9.15)], 'team')
    rings, centers = [], []
    for forward, height in [(-4, 1.7), (-1.5, 2.45), (2, 2.3), (5, 1.85), (7.2, 1.35)]:
        c = np.array((0, height, forward))
        centers.append(c)
        rings.append([c + (dx, dy, 0) for dx, dy in [(-.17, -.05), (.17, -.05), (.17, .15), (-.17, .15)]])
    m.loft(rings, centers, 0, 'team')
    return m


def append_mesh(destination, source, offset, bone):
    start = len(destination.vertices)
    for v in source.vertices:
        destination.vertices.append(tuple(np.array(v[:3]) + offset) + v[3:16] + (bone,))
    destination.indices.extend(start + i for i in source.indices)
    destination.materials.extend(source.materials)


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
    # A levitation source in the ground plinth; clear air separates all islands.
    m.column([(3.8, 6.3), (3.2, 7.3), (1.4, 8.8), (.3, 9.4)], material='edge')
    m.annulus(2, 3.1, 7.4, 7.8, material='team')
    gun = launcher(detail)
    for (x, y, z), island, barrel in zip(ISLANDS, ISLAND_BONES, BARREL_BONES):
        def island_geometry():
            # Pointed floating underside, beveled saucer deck and inset halo.
            m.column([(.3, -4.8), (1.8, -3.6), (4.4, -2.2), (6.2, -1.1),
                      (6.6, -.4), (6.1, .3), (5.4, .6)], island, 'dark')
            m.annulus(5.3, 6.5, -.5, .35, island, 'edge')
            m.column([(5.3, .35), (5.0, .85), (3.7, 1.05)], island, 'armor')
            m.annulus(4.3, 4.8, .85, 1.1, island, 'team')
            # Small suspended induction ring underneath, with no connecting rod.
            m.annulus(1.1, 2.1, -5.9, -5.55, island, 'team')
            m.column([(.2, -4.9), (1.05, -4.0), (.6, -3.5)], island, 'crystal')
            # Two cheeks physically attach the cannon to its own island.
            for side in (-1.8, 1.8):
                translated(m, (side, 0, -4), lambda: m.column([(.8, .8), (.9, 2.4), (.65, 4.0)], island, 'steel'))
        translated(m, (x, y, z), island_geometry)
        append_mesh(m, gun, (x, y + 3.8, z), barrel)
    m.smooth()
    return m


def main():
    UNIT.mkdir(parents=True, exist_ok=True)
    for lod, detail in ((0, 24), (1, 12)):
        mesh = build_mesh(detail)
        write_scm(mesh, UNIT / f'GGA2401_lod{lod}.scm', NAMES, PARENTS, PIVOTS)
        if lod == 0:
            export_obj(mesh, ASSETS, NAMES)
        print(f'LOD{lod}: {len(mesh.indices)//3} triangles / {len(mesh.vertices)} vertices', flush=True)
    make_textures(ASSETS, UNIT, save_dds_dxt5)
    views = []
    for name, azimuth, elevation, color in [('Front', 0, 17, (.12, .32, 1)),
                                           ('Side', 90, 15, (.12, .32, 1)),
                                           ('Game view', 35, 32, (.95, .22, .1))]:
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
