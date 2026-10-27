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


def plate(mesh, outline, depth=.3, bone=0, material='armor'):
    """A thick convex armor petal with coherent planar UVs on its broad face."""
    top = [np.array(p, dtype=float) for p in outline]
    bottom = [p - (0, depth, 0) for p in top]
    points = np.array(top)
    lo, span = points[:, [0, 2]].min(0), np.maximum(np.ptp(points[:, [0, 2]], axis=0), .001)
    uvs = [tuple((p[[0, 2]] - lo) / span) for p in top]
    mesh.face(top, bone, material, (0, 1, 0), uvs)
    mesh.face(bottom, bone, 'dark', (0, -1, 0), uvs)
    center = np.mean(top, axis=0)
    for i in range(len(top)):
        j = (i + 1) % len(top)
        out = (top[i] + top[j]) / 2 - center
        out[1] = 0
        mesh.face([top[i], bottom[i], bottom[j], top[j]], bone, 'edge', out)


def splinter(mesh, center, width, height, depth, bone, material='dark', lean=(0, 0)):
    """Asymmetric five-sided rocky-metal shard, ending in sharp displaced tips."""
    cx, cy, cz = center
    rings, centers = [], []
    outline = [(-.9, -.6), (.3, -.95), (1, -.22), (.6, .85), (-.75, .7)]
    profile = [(-height, .018, 1), (-height * .45, .52, .45),
               (-height * .08, 1, .08), (.65, .7, -.08), (height * .3, .025, -.3)]
    if mesh.detail < 16:
        profile = [profile[j] for j in (0, 2, 4)]
    for y, scale, shift in profile:
        c = np.array((cx + lean[0] * shift, cy + y, cz + lean[1] * shift))
        centers.append(c)
        rings.append([c + (u * width * scale, 0, v * depth * scale) for u, v in outline])
    mesh.loft(rings, centers, bone, material)


def rail(mesh, points, width=.07, bone=0, material='team'):
    """Raised narrow engraving/power line following an armored ridge."""
    rings = [[(x-width, y-.025, z), (x+width, y-.025, z),
              (x+width, y+.065, z), (x-width, y+.065, z)] for x,y,z in points]
    mesh.loft(rings, points, bone, material)


def launcher(detail):
    """Reference-inspired broad breech, split blades and open triangular throat."""
    m = Mesh(detail)
    rings, centers = [], []
    for z, w, h in [(-5.3,.25,.25),(-3.4,2.3,.8),(-.5,2.65,1.0),(2.7,1.7,.8),(4.8,.35,.3)]:
        centers.append((0,-.25,z))
        rings.append([(w*u,-.25+h*v,z) for u,v in [(-1,0),(-.5,1),(.5,1),(1,0),(.5,-1),(-.5,-1)]])
    m.loft(rings, centers, 0, 'dark')
    # Broad dark central recess is enclosed by two pointed armor leaves.
    plate(m, [(-1.7,-.15,-4.5),(0,.1,-5.4),(1.7,-.15,-4.5),
              (1.1,-.15,4.6),(0,-.1,9.7),(-1.1,-.15,4.6)], .65, material='joint')
    for s in (-1, 1):
        def mirror(points):
            return [(s*x,y,z) for x,y,z in points]
        plate(m, mirror([(.18,.6,-4.7),(2.6,.75,-3.3),(3.0,1.0,-.6),
                         (1.7,.75,4.8),(.62,.42,9.95),(.45,.65,3.2)]), .42)
        # Additional swept quills give the wide forked silhouette in reference 2.
        plate(m, mirror([(2.6,.2,-3.3),(4.1,.3,-1.6),(3.65,.4,2.8),
                         (2.0,.65,6.2),(2.8,.25,.3)]), .22, material='steel')
        rail(m, mirror([(.9,.79,-4.0),(1.8,1.12,-1.1),(1.25,.94,3.7),(.7,.58,8.4)]), .055)
        # Small detached terminal blade frames the muzzle without making a tube.
        plate(m, mirror([(.32,.1,8.1),(1.05,.55,8.8),(.18,.25,10.0),(.1,.05,9.1)]), .18, material='steel')
    # Triangular inset emitter stays behind the unchanged projectile release point.
    m.face([(-.28,-.02,9.94),(.28,-.02,9.94),(0,.34,9.94)], 0, 'lens', (0,0,1))
    return m


def append_mesh(destination, source, offset, bone):
    start = len(destination.vertices)
    for v in source.vertices:
        destination.vertices.append(tuple(np.array(v[:3]) + offset) + v[3:16] + (bone,))
    destination.indices.extend(start + i for i in source.indices)
    destination.materials.extend(source.materials)


def build_mesh(detail):
    m = Mesh(detail)
    # Five separate pointed petals, with air between tips; no circular plinth.
    for i in range(5):
        a = math.radians(18 + i*72)
        radial = np.array((math.cos(a),0,math.sin(a)))
        tangent = np.array((-math.sin(a),0,math.cos(a)))
        outline = [(-2.3,2.6,3.0),(-4.7,2.3,8.0),(-3.5,1.3,13.7),
                   (0,.55,18.7),(3.4,1.3,13.7),(4.0,2.5,7.2),(2,2.6,3)]
        plate(m, [radial*r+tangent*w+(0,y,0) for w,y,r in outline], .65)
        if detail >= 16:
            plate(m, [radial*r+tangent*w+(0,y,0) for w,y,r in
                      [(-1.1,2.8,4),(-2.1,2.6,8.3),(0,.8,17.4),(1.9,2.65,8.1)]], .15, material='steel')
        rail(m, [tuple(radial*r+(0,y,0)) for r,y in [(4.4,3.0),(8.6,2.8),(15.5,1.5)]], .09)
    # Angular central lift source and three upward splinters.
    splinter(m, (0,2.7,0), 5.8, 2.2, 5.1, 0, 'dark', (.4,-.6))
    for i in range(3):
        a=i*math.pi*2/3
        splinter(m, (3.4*math.cos(a),3.8,3.4*math.sin(a)), 1.1, 2.4, 1.25, 0, 'steel')
    gun = launcher(detail)
    for (x, y, z), island, barrel in zip(ISLANDS, ISLAND_BONES, BARREL_BONES):
        def island_geometry():
            # Fractured levitating rock, with a deep sharp keel and satellite shards.
            splinter(m, (0,-.3,0), 4.2, 6.8, 4.9, island, 'dark', (.9,-1.1))
            # Broad incised frontal facet on the rock, following its tapered keel.
            front = [(-1.9,-.65,3.7),(1.6,-.6,3.6),(1.15,-3.25,2.15),
                     (.9,-5.8,.6),(-.75,-3.1,2.2)]
            m.face(front, island, 'armor', (0,0,1), [(0,0),(1,0),(.82,.55),(.5,1),(.18,.55)])
            for side in (-1,1):
                splinter(m, (side*3.2,-.6,1.0), 1.5, 4.7, 2.5, island, 'steel', (side*.9,.4))
                # Tall outer rock blades echo the suspended structures in reference 1.
                splinter(m, (side*4.8,1.3,-2.6), .8, 2.8, 2, island, 'armor', (side*.8,-.5))
                plate(m, [(side*.8,.65,-4.6),(side*3.7,.9,-3.8),
                          (side*4.0,.8,1.1),(side*2.0,.75,4.4),(side*.8,.65,.4)], .3, island)
                # Sharp, narrow trunnion cheeks; no round bearings or saucer rims.
                plate(m, [(side*1.2,1,-4.8),(side*2.2,1,-4.8),
                          (side*2.0,3.9,-3.5),(side*1.2,3.9,-3.5)], .25, island, 'steel')
                rail(m, [(side*3.0,.99,-3),(side*3.35,.9,.1),(side*2.1,.9,3.5)], .055, island)
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
    for name, azimuth, elevation, color in [('Front', 0, 17, (.12, .9, .22)),
                                           ('Side', 90, 15, (.12, .32, 1)),
                                           ('Game view', 35, 32, (.12, .9, .22))]:
        im = render_scm(UNIT / 'GGA2401_lod0.scm', ASSETS, ASSETS / f'GGA2401_{name.lower().replace(" ", "_")}.png',
                        azimuth, elevation, color, 720)
        ImageDraw.Draw(im).text((24, 24), name, fill=(220, 230, 240), font=ImageFont.load_default(size=20))
        views.append(im)
    sheet = Image.new('RGB', (2160, 720))
    for i, view in enumerate(views):
        sheet.paste(view, (i * 720, 0))
    sheet.save(ASSETS / 'GGA2401_views.png')
    render_scm(UNIT / 'GGA2401_lod0.scm', ASSETS, ASSETS / 'GGA2401_island_closeup.png',
               35, 32, (.12, .9, .22), 1000, bones=(8,9,10))
    print('Exported GGA2401 model and previews.', flush=True)


if __name__ == '__main__':
    main()
