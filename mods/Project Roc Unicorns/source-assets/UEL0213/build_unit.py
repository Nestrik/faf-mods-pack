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
from uef_armor import armor_detail, material_tiles
from supcom_binary import write_scm, write_sca, save_dds_dxt5

# Match the 1.181-unit chassis width; stretch only across the vehicle.
LAUNCHER_WIDTH_SCALE = 1.18063057 / .48241497576236725
LAUNCHER_WIDTH_RATIO = LAUNCHER_WIDTH_SCALE / 1.1

NAMES = ['UEL0213', 'Launcher', 'Muzzle_1', 'Muzzle_2', 'Muzzle_3', 'Muzzle_4']
PARENTS = [-1, 0, 1, 1, 1, 1]
HINGE = (0, .95, -2.02)
WIDTH = 1.18063057
BODY_FRONT = .20
BODY_REAR = BODY_FRONT - WIDTH
BODY_BOTTOM = -.95
BODY_TOP = 2.47
PIVOTS = [(0, 0, 0), HINGE]
# A 90-degree folded bind pose; muzzle bones follow the housing.
for x in (-WIDTH / 4, WIDTH / 4):
    for z in (BODY_REAR + WIDTH / 4, BODY_REAR + 3 * WIDTH / 4):
        PIVOTS.append((x, -z, BODY_TOP))
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
# Rebuild the housing with a square cross section and a ground-bearing tail.
# All points below are in the deployed launcher coordinates, relative to hinge.
images['launcher'] = glb('launcher')[4]
TILES = {name: i for i, name in enumerate(('armor','edge','dark','team','vent','optic'))}
def face(points, outward, material='armor', bone=1):
    points = [np.array(p, dtype=float) for p in points]
    n = np.cross(points[1]-points[0], points[2]-points[0])
    if np.dot(n, outward) < 0: points.reverse(); n = -n
    n /= max(np.linalg.norm(n), 1e-9)
    # Bind pose is folded +90 degrees about X.
    rotate = lambda v: np.array((v[0], -v[2], v[1])) if bone == 1 else v
    normal = rotate(n)
    ref = np.array((0.,1.,0.)) if abs(normal[1]) < .9 else np.array((0.,0.,1.))
    tangent = np.cross(ref,normal); tangent /= max(np.linalg.norm(tangent),1e-9)
    bitangent = np.cross(normal,tangent)
    # Map each face across its own atlas tile, preserving hard normals.
    base = len(mesh.vertices)
    largest = int(np.argmax(np.abs(n)))
    axes = [(2,1),(0,2),(0,1)][largest]
    projected = np.asarray(points)[:,axes]
    coords = (projected-projected.min(axis=0))/np.maximum(np.ptp(projected,axis=0),1e-8)
    tile = TILES[material]
    for point, coord in zip(points,coords):
        uv=((512+(tile%2)*256+4+coord[0]*248)/1024,
            ((tile//2)*128+4+(1-coord[1])*120)/1024)
        pos = rotate(point) + np.array(HINGE) if bone == 1 else point
        mesh.vertices.append(tuple(pos)+tuple(normal)+tuple(tangent)+tuple(bitangent)+uv+uv+(bone,))
    for i in range(1,len(points)-1):mesh.indices.extend((base,base+i,base+i+1))

def box(x0,x1,y0,y1,z0,z1,material='armor',bone=1):
    face([(x0,y0,z0),(x0,y1,z0),(x0,y1,z1),(x0,y0,z1)],(-1,0,0),material,bone)
    face([(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],(1,0,0),material,bone)
    face([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],(0,-1,0),material,bone)
    face([(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)],(0,1,0),material,bone)
    face([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)],(0,0,-1),material,bone)
    face([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],(0,0,1),material,bone)

w=WIDTH/2; lo=BODY_BOTTOM; hi=BODY_TOP; back=BODY_REAR; front=BODY_FRONT
# Four closed exterior walls and a full bearing base; top is four bored tiles.
face([(-w,lo,back),(-w,hi,back),(-w,hi,front),(-w,lo,front)],(-1,0,0))
face([(w,lo,back),(w,hi,back),(w,hi,front),(w,lo,front)],(1,0,0))
face([(-w,lo,back),(w,lo,back),(w,hi,back),(-w,hi,back)],(0,0,-1))
face([(-w,lo,front),(w,lo,front),(w,hi,front),(-w,hi,front)],(0,0,1))
face([(-w,lo,back),(w,lo,back),(w,lo,front),(-w,lo,front)],(0,-1,0),'edge')
for x in (-WIDTH/4,WIDTH/4):
 for z in (back+WIDTH/4,back+3*WIDTH/4):
  outside=[];inside=[];bottom=[]
  for i in range(24):
   a=2*math.pi*i/24;dx,dz=math.cos(a),math.sin(a);k=(WIDTH/4)/max(abs(dx),abs(dz))
   outside.append((x+dx*k,hi,z+dz*k));inside.append((x+dx*.235,hi,z+dz*.235));bottom.append((x+dx*.235,hi-.55,z+dz*.235))
  for i in range(24):
   j=(i+1)%24
   face([outside[i],outside[j],inside[j],inside[i]],(0,1,0),'edge')
   direction=np.array((x,hi-.25,z))-np.mean([inside[i],inside[j],bottom[j],bottom[i]],axis=0)
   face([inside[i],inside[j],bottom[j],bottom[i]],direction,'dark')
  face(bottom,(0,1,0),'dark')
# Narrow bands, team panels, and mounting cheeks.
armor_detail(face,w,back,front,hi,lambda side,i: 6+(4 if side>0 else 0)+i)
for x in (-.43,.43):
 box(x-.045,x+.045,-.10,.10,-.11,.11,'edge')
 # Fixed beams bridge the original rear mount to the new rearward hinge.
 box(x-.045,x+.045,.87,.95,-2.08,-1.40,'edge',0)
for side in (-1, 1):
    for i, z in enumerate((1.24, .70, -.60, -1.17)):
        bone = NAMES.index(f'Wheel_{"L" if side < 0 else "R"}_{i + 1}')
        add_part('wheel', bone,
                 lambda p, side=side, z=z: (side * (.67 + p[2] * .58), .30 + (p[1] - .5) * .58, z + p[0] * .58),
                 lambda n, side=side: (side * n[2], n[1], n[0]), (.5, .5), (.5, .5), flip=(side > 0))
print('SCM', len(mesh.vertices), 'vertices', len(mesh.indices) // 3, 'triangles', len(NAMES), 'bones')
write_scm(mesh, OUT / 'UEL0213_lod0.scm', NAMES, PARENTS, PIVOTS)

# One texture quadrant per source component, with the wheel reused eight times.
atlas = Image.new('RGBA', (1024, 1024), (40, 46, 55, 0))
for name, xy in [('chassis', (0, 512)), ('launcher', (0, 0)), ('wheel', (512, 512))]:
    atlas.paste(images[name].resize((512,512),Image.Resampling.LANCZOS),xy)
spec = Image.new('RGBA',(1024,1024),(60,58,0,0))
material_tiles(atlas,spec)
atlas.save(HERE / 'UEL0213_albedo_source.png')
normal = Image.new('RGBA', (1024, 1024), (128, 128, 255, 128))
for name, img in [('albedo', atlas), ('specteam', spec), ('normalsTS', normal)]:
    save_dds_dxt5(img, OUT / f'UEL0213_{name}.dds', independent_channels=True)

# Native unpack animation starts folded and ends fully upright. FAF's weapon
# state machine waits for WaitFor(unpackAnimator) before allowing a salvo.
unpack = []
for i in range(31):
    angle = math.radians(-90 * i / 30)
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




