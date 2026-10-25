"""Preview the procedural rig from exported SCM and runtime DDS, without Blender.

This depicts mesh motion only. Economy, particles and firing require a FAF match.
"""
import json
import math
import re
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from preview_scm import load_scm, render_scm

HERE = Path(__file__).resolve().parent
UNIT = HERE.parents[1] / 'units/GGA2404'


def read_rig(path):
    data = path.read_bytes()
    header = struct.unpack_from('<4s11I', data)
    bones = []
    for i in range(header[3]):
        row = struct.unpack_from('<16f3f4f4i', data, header[2] + 108 * i)
        name = data[row[23]:].split(b'\0', 1)[0].decode()
        # This rig's bind rotations are identity; do not silently apply this
        # preview's simpler pose calculation to a different skeleton.
        assert np.allclose(row[19:23], (1, 0, 0, 0), atol=1e-6)
        bones.append(dict(name=name, parent=row[24], position=np.array(row[16:19]),
                          inverse=np.array(row[:16]).reshape(4, 4).T))
    return bones


def pose_vertices(path, offsets, angles):
    vertices, _ = load_scm(path)
    rig = read_rig(path)
    worlds = []
    for bone in rig:
        matrix = np.eye(4)
        for axis, degrees in angles.get(bone['name'], []):
            angle = math.radians(degrees)
            c, s = math.cos(angle), math.sin(angle)
            rotation = np.eye(4)
            a, b = {'x': (1, 2), 'y': (2, 0), 'z': (0, 1)}[axis]
            rotation[a, a] = rotation[b, b] = c
            rotation[a, b], rotation[b, a] = -s, s
            matrix = matrix @ rotation
        matrix[:3, 3] = bone['position'] + np.array(offsets.get(bone['name'], (0, 0, 0)))
        if bone['parent'] >= 0:
            matrix = worlds[bone['parent']] @ matrix
        worlds.append(matrix)
    result = vertices.copy()
    for i, bone in enumerate(rig):
        mask = vertices[:, 16] == i
        skin = worlds[i] @ bone['inverse']
        result[mask, :3] = vertices[mask, :3] @ skin[:3, :3].T + skin[:3, 3]
        for start in (3, 6, 9):
            result[mask, start:start+3] = vertices[mask, start:start+3] @ skin[:3, :3].T
    return result


def main():
    out = HERE / 'animation-rebuild-2026-10-25'
    out.mkdir(exist_ok=True)
    bp = (UNIT / 'GGA2404_unit.bp').read_text()
    def value(name):
        return float(re.search(r'\b' + name + r'\s*=\s*([\d.]+)', bp)[1])
    scale = value('UniformScale')
    amplitude = value('HoverHeight') / scale
    closed = value('ClosedInwardOffset') / scale
    path = UNIT / 'GGA2404_lod0.scm'
    frames = []
    for i, openness in enumerate((0, .15, .5, .85, 1, 1, 1, 0)):
        offsets = {'Hover': (0, amplitude * math.sin(i * math.pi / 4), 0),
                   'GondolaL': (closed * (1 - openness), 0, 0),
                   'GondolaR': (-closed * (1 - openness), 0, 0)}
        angles = {'Field': [('z', i * 60)], 'FieldBoost': [('z', i * 60)],
                  'FieldPeak': [('z', i * 60)]}
        if i == 6:
            angles['Recoil'] = [('x', -2)]
        vertices = pose_vertices(path, offsets, angles)
        frame = render_scm(path, HERE, out / f'phase_{i}.png', size=420,
                           posed_vertices=vertices, hidden_bones=[] if openness == 1 and i != 6 else [9, 10, 11],
                           runtime_textures=True)
        ImageDraw.Draw(frame).text((12, 12), f'GGA2404 | phase {i} | open {openness:.0%}', fill='white')
        frames.append(frame)
    frames[0].save(out / 'mechanical_cycle.gif', save_all=True, append_images=frames[1:],
                   duration=500, loop=0)
    sheet = Image.new('RGB', (420 * 4, 420 * 2))
    for i, frame in enumerate(frames):
        sheet.paste(frame, (420 * (i % 4), 420 * (i // 4)))
    sheet.save(out / 'mechanical_cycle.png')
    # Separate neutral views check the exported rig and clearance from each side.
    for name, azimuth, elevation in [('front', 0, 18), ('side', 90, 18), ('top', 0, 80)]:
        render_scm(path, HERE, out / (name + '.png'), azimuth, elevation, size=420,
                   runtime_textures=True)
    (out / 'preview_notes.json').write_text(json.dumps({
        'source': 'exported SCM and runtime DDS', 'particles_rendered': False,
        'in_game_verified': False, 'hover_height_game_units': value('HoverHeight'),
        'hover_period_ticks': value('HoverPeriodTicks'),
        'cycle_frames_are_illustrative': True,
    }, indent=2))
    print(out)


if __name__ == '__main__':
    main()
