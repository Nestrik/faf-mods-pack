"""Repair the imported orb's inward surface without changing its shape or UVs.

Run with Python + numpy + Pillow. Input is the archived original, so rebuilding
is repeatable and never flips an already repaired mesh back inside out.
"""
import math
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
ORIGINAL = HERE / 'archive/before-outward-surface-2026-10-21/ball_lightning_lod0.scm'
OUTPUT = MOD / 'meshes/ball_lightning/ball_lightning_lod0.scm'


def read_mesh(data):
    header = struct.unpack_from('<4s11I', data)
    assert header[:2] == (b'MODL', 5)
    vertices = np.array([struct.unpack_from('<16f4B', data, header[4] + i * 68)
                         for i in range(header[6])])
    faces = np.frombuffer(data, dtype='<u2', count=header[8], offset=header[7]).reshape(-1, 3).copy()
    assert faces.max() < len(vertices) and np.isfinite(vertices).all()
    return header, vertices, faces


def preview(data, azimuth, elevation, grounded):
    """Diagnostic SCM render: back-face culling and opaque ground clipping.

    Neutral shading isolates geometry; particles, bloom and game materials are
    deliberately outside this diagnostic. Grounded centre is at terrain height,
    matching GGP2404_script.lua after the three sinking ticks.
    """
    _, vertices, faces = read_mesh(data)
    positions = vertices[:, :3]
    a, e = math.radians(azimuth), math.radians(elevation)
    view = np.array((math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)))
    right = np.array((math.cos(a), 0, -math.sin(a)))
    up = np.cross(view, right)
    size, scale = 360, 22
    projected = np.stack((positions @ right, -positions @ up), axis=1) * scale + (180, 190)
    depth = positions @ view
    canvas = np.full((size, size, 3), (27, 32, 41), dtype=float)
    zbuffer = np.full((size, size), -np.inf)
    if grounded:
        yy, xx = np.mgrid[:size, :size]
        # Intersection of each orthographic view ray with the horizontal plane.
        vertical = (190 - (yy + .5)) / scale
        ground_depth = -vertical * up[1] / view[1]
        zbuffer[:] = ground_depth
        canvas[:] = (47, 50, 49)
    sun = np.array((-.35, .8, .48))
    sun /= np.linalg.norm(sun)
    for face in faces:
        p3 = positions[face]
        geometric = np.cross(p3[1] - p3[0], p3[2] - p3[0])
        if geometric @ view <= 0:
            continue
        p = projected[face]
        lo = np.maximum(np.floor(p.min(0)).astype(int), 0)
        hi = np.minimum(np.ceil(p.max(0)).astype(int), size - 1)
        if np.any(lo > hi):
            continue
        x, y = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5, np.arange(lo[1], hi[1]+1)+.5)
        denominator = ((p[1, 1]-p[2, 1])*(p[0, 0]-p[2, 0])
                       + (p[2, 0]-p[1, 0])*(p[0, 1]-p[2, 1]))
        if abs(denominator) < 1e-10:
            continue
        w0 = ((p[1, 1]-p[2, 1])*(x-p[2, 0])+(p[2, 0]-p[1, 0])*(y-p[2, 1]))/denominator
        w1 = ((p[2, 1]-p[0, 1])*(x-p[2, 0])+(p[0, 0]-p[2, 0])*(y-p[2, 1]))/denominator
        w2 = 1-w0-w1
        z = w0*depth[face[0]]+w1*depth[face[1]]+w2*depth[face[2]]
        region = np.s_[lo[1]:hi[1]+1, lo[0]:hi[0]+1]
        mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (z > zbuffer[region])
        weights = np.stack((w0[mask], w1[mask], w2[mask]), axis=1)
        normals = weights @ vertices[face, 3:6]
        normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-10)
        lighting = .27+.73*np.clip(normals @ sun, 0, 1)
        canvas[region][mask] = lighting[:, None] * (160, 191, 235)
        zbuffer[region][mask] = z[mask]
    return Image.fromarray(np.uint8(np.clip(canvas, 0, 255)))


def main():
    original = ORIGINAL.read_bytes()
    header, before, faces = read_mesh(original)
    data = bytearray(original)
    # Reverse the surface normal and binormal, keeping tangent and TBN handedness.
    # Positions, UVs, skeleton, bounds, scale and material references stay intact.
    for i, vertex in enumerate(before):
        for start in (3, 9):
            struct.pack_into('<3f', data, header[4]+i*68+start*4, *(-vertex[start:start+3]))
    faces = faces[:, [0, 2, 1]]
    data[header[7]:header[7]+header[8]*2] = faces.astype('<u2').tobytes()
    _, after, faces = read_mesh(data)
    triangles = after[faces, :3]
    geometric = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    assert np.all(np.sum(geometric * triangles.mean(1), axis=1) > 0)
    assert np.all(np.sum(after[:, :3] * after[:, 3:6], axis=1) > 0)
    assert np.allclose(np.linalg.norm(after[:, 3:6], axis=1), 1, atol=1e-6)
    assert np.allclose(np.sum(np.cross(after[:, 6:9], after[:, 9:12])*after[:, 3:6], axis=1), -1, atol=1e-6)
    assert np.array_equal(before[:, :3], after[:, :3])
    assert np.array_equal(before[:, 12:], after[:, 12:])
    OUTPUT.write_bytes(data)
    # Read the actual output file back for all preview views.
    fixed = OUTPUT.read_bytes()
    sheet = Image.new('RGB', (1440, 720))
    views = [(0, 18, True, 'Ground: front'), (90, 18, True, 'Ground: side'),
             (35, 45, True, 'Ground: game angle'), (35, 25, False, 'Full sphere')]
    for row, (content, label) in enumerate([(original, 'Before'), (fixed, 'Fixed')]):
        for col, (azimuth, elevation, grounded, title) in enumerate(views):
            im = preview(content, azimuth, elevation, grounded)
            ImageDraw.Draw(im).text((12, 12), f'{label} | {title}', fill='white')
            sheet.paste(im, (col*360, row*360))
    sheet.save(HERE / 'orb_surface_comparison.png')
    print(f'Validated {len(after)} vertices, {len(faces)} outward triangles; shape/UVs preserved.')


if __name__ == '__main__':
    main()
