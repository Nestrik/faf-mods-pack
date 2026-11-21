"""Assemble the three supplied GLBs into FAF SCM/SCA and material DDS files."""
from io import BytesIO
from pathlib import Path
import json
import math
import struct
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / 'units' / 'UEL0213'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE))
from supcom_binary import write_scm, write_sca, save_dds_dxt5

# Match the 1.181-unit chassis width; stretch only across the vehicle.
LAUNCHER_WIDTH_SCALE = 1.18063057 / .48241497576236725
LAUNCHER_WIDTH_RATIO = LAUNCHER_WIDTH_SCALE / 1.1

NAMES = ['UEL0213', 'Launcher', 'Muzzle_1', 'Muzzle_2', 'Muzzle_3', 'Muzzle_4']
PARENTS = [-1, 0, 1, 1, 1, 1]
PIVOTS = [(0, 0, 0), (0, .95, -1.44)]
for x in (-.12, .12):
    for z in (-.44, -.25):
        angle = math.radians(80)
        PIVOTS.append((x * LAUNCHER_WIDTH_RATIO, 0.957 * math.cos(angle) - z * math.sin(angle),
                       0.957 * math.sin(angle) + z * math.cos(angle)))
for side in (-1, 1):
    for i, z in enumerate((1.24, .70, -.60, -1.17)):
        NAMES.append(f'Wheel_{"L" if side < 0 else "R"}_{i + 1}')
        PARENTS.append(0)
        PIVOTS.append((side * .67, .30, z))


def glb(name):
    data = (HERE / (name + '_source.glb')).read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + length])
    start = 28 + length
    counts = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    dtypes = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}

    def read(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        dtype = np.dtype(dtypes[a['componentType']])
        count = counts[a['type']]
        return np.ndarray((a['count'], count), dtype=dtype, buffer=data,
                          offset=start + view.get('byteOffset', 0) + a.get('byteOffset', 0),
                          strides=(view.get('byteStride', dtype.itemsize * count), dtype.itemsize)).copy()

    def picture(index):
        view = doc['bufferViews'][doc['images'][index]['bufferView']]
        return Image.open(BytesIO(data[start + view.get('byteOffset', 0):
                                       start + view.get('byteOffset', 0) + view['byteLength']])).convert('RGBA')

    prim = doc['meshes'][0]['primitives'][0]
    a = prim['attributes']
    return read(a['POSITION']), read(a['NORMAL']), read(a['TEXCOORD_0']), read(prim['indices']).reshape(-1), picture(0)


class Mesh:
    def __init__(self):
        self.vertices = []
        self.indices = []


mesh = Mesh()
images = {}


def add_part(name, bone, transform, normal_transform, uv_offset, uv_scale, flip=True):
    positions, normals, uv, indices, image = glb(name)
    images[name] = image
    start = len(mesh.vertices)
    for p, n, t in zip(positions, normals, uv):
        pos = transform(p)
        norm = np.asarray(normal_transform(n), dtype=float)
        norm /= max(1e-8, np.linalg.norm(norm))
        ref = np.array((0, 1, 0), dtype=float) if abs(norm[1]) < .9 else np.array((0, 0, 1), dtype=float)
        tangent = np.cross(ref, norm)
        tangent /= max(1e-8, np.linalg.norm(tangent))
        bitangent = np.cross(norm, tangent)
        tex = (uv_offset[0] + t[0] * uv_scale[0], uv_offset[1] + t[1] * uv_scale[1])
        mesh.vertices.append(tuple(pos) + tuple(norm) + tuple(tangent) + tuple(bitangent) + tex + tex + (bone,))
    tris = indices.astype(int).reshape(-1, 3) + start
    if flip: tris = tris[:, [0, 2, 1]]
    mesh.indices.extend(tris.reshape(-1).tolist())


# GLB accessor coordinates use Y up, X along the vehicle, Z across it. FAF uses Y up, Z forward.
add_part('chassis', 0, lambda p: (-p[2] * 3.6, p[1] * 3.6 + .18, -p[0] * 3.6),
         lambda n: (-n[2], n[1], -n[0]), (0, .5), (.5, .5))
# Source launcher axle is along X, centered at Y=.08, Z=.17.
# Rotate around that axle, not the GLB origin.
add_part('launcher', 1, lambda p: (p[0] * LAUNCHER_WIDTH_SCALE,
    .95 + 1.1 * ((p[1]-.08)*math.cos(math.radians(80))-(p[2]-.17)*math.sin(math.radians(80))),
    -1.44 + 1.1 * ((p[1]-.08)*math.sin(math.radians(80))+(p[2]-.17)*math.cos(math.radians(80)))),
    lambda n: (n[0] / LAUNCHER_WIDTH_RATIO, n[1]*math.cos(math.radians(80))-n[2]*math.sin(math.radians(80)),
               n[1]*math.sin(math.radians(80))+n[2]*math.cos(math.radians(80))),
    (0, 0), (.5, .5), flip=False)
for side in (-1, 1):
    for i, z in enumerate((1.24, .70, -.60, -1.17)):
        bone = NAMES.index(f'Wheel_{"L" if side < 0 else "R"}_{i + 1}')
        add_part('wheel', bone,
                 lambda p, side=side, z=z: (side * (.67 + p[2] * .58), .30 + (p[1] - .5) * .58, z + p[0] * .58),
                 lambda n, side=side: (side * n[2], n[1], n[0]), (.5, 0), (.5, .5), flip=(side > 0))
print('SCM', len(mesh.vertices), 'vertices', len(mesh.indices) // 3, 'triangles', len(NAMES), 'bones')
write_scm(mesh, OUT / 'UEL0213_lod0.scm', NAMES, PARENTS, PIVOTS)

# One texture quadrant per source component, with the wheel reused eight times.
atlas = Image.new('RGBA', (1024, 1024), (40, 46, 55, 0))
for name, xy in [('chassis', (0, 0)), ('launcher', (0, 512)), ('wheel', (512, 512))]:
    atlas.paste(images[name].resize((512, 512), Image.Resampling.LANCZOS), xy)
atlas.save(HERE / 'UEL0213_albedo_source.png')
spec = Image.new('RGBA', (1024, 1024), (75, 72, 0, 0))
normal = Image.new('RGBA', (1024, 1024), (128, 128, 255, 128))
for name, img in [('albedo', atlas), ('specteam', spec), ('normalsTS', normal)]:
    save_dds_dxt5(img, OUT / f'UEL0213_{name}.dds', independent_channels=True)

# Native unpack animation starts folded and ends fully upright. FAF's weapon
# state machine waits for WaitFor(unpackAnimator) before allowing a salvo.
unpack = []
for i in range(31):
    angle = math.radians(-80 * i / 30)
    unpack.append([(PIVOTS[0], (1, 0, 0, 0)),
                   (PIVOTS[1], (math.cos(angle / 2), math.sin(angle / 2), 0, 0))])
write_sca(OUT / 'UEL0213_deploy.sca', NAMES[:2], PARENTS[:2], unpack, 3.0)

wheel_names = [NAMES[0]] + NAMES[6:]
wheel_parents = [-1] + [0] * 8
wheel_frames = []
for i in range(31):
    angle = 2 * math.pi * i / 30
    wheel_frames.append([(PIVOTS[0], (1, 0, 0, 0))] +
                        [(PIVOTS[k], (math.cos(angle / 2), math.sin(angle / 2), 0, 0))
                         for k in range(6, 14)])
write_sca(OUT / 'UEL0213_wheels.sca', wheel_names, wheel_parents, wheel_frames,
          2 * math.pi * .29 / 2.2)




