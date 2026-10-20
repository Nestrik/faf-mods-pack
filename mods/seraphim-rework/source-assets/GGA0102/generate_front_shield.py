"""Generate the closed, curved front-shield mesh used by GGA0102.

The shield entity scales this mesh by Defense.Shield.ShieldSize (3), so the
source geometry is authored at one third of its intended in-game dimensions.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path


MOD_ROOT = Path(__file__).resolve().parents[1]
UNIT_DIR = MOD_ROOT / "units" / "GGA0102"
SCM_PATH = UNIT_DIR / "GGA0102_frontshield_lod0.scm"
OBJ_PATH = Path(__file__).resolve().parent / "GGA0102_frontshield.obj"

SCALE = 3.0
WIDTH_SCALE = 8.0
FORWARD_SCALE = 4.0
SEGMENTS = 16
RADIUS = 0.72
THICKNESS = 0.06
HEIGHT = 0.81
ARC_DEGREES = 120.0
ROOT_BONE = "XSL0307"


def pad(size: int) -> int:
    value = 16 - (size % 16)
    return value + 16 if value < 4 else value


def normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(component * component for component in vector))
    if length < 1e-9:
        return (0.0, 1.0, 0.0)
    return tuple(component / length for component in vector)


def subtract(a: tuple[float, float, float], b: tuple[float, float, float]):
    return tuple(a[index] - b[index] for index in range(3))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalize_uv_basis(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    uv0: tuple[float, float],
    uv1: tuple[float, float],
    uv2: tuple[float, float],
):
    edge1 = subtract(p1, p0)
    edge2 = subtract(p2, p0)
    du1, dv1 = uv1[0] - uv0[0], uv1[1] - uv0[1]
    du2, dv2 = uv2[0] - uv0[0], uv2[1] - uv0[1]
    determinant = du1 * dv2 - du2 * dv1
    if abs(determinant) < 1e-9:
        return (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    reciprocal = 1.0 / determinant
    tangent = tuple((edge1[i] * dv2 - edge2[i] * dv1) * reciprocal for i in range(3))
    bitangent = tuple((edge2[i] * du1 - edge1[i] * du2) * reciprocal for i in range(3))
    return normalize(tangent), normalize(bitangent)


def panel_point(angle: float, radius: float, y: float) -> tuple[float, float, float]:
    # The unit faces +Z in its local coordinate system.
    return (
        WIDTH_SCALE * radius * math.sin(angle),
        y,
        FORWARD_SCALE * radius * math.cos(angle),
    )


def main() -> None:
    UNIT_DIR.mkdir(parents=True, exist_ok=True)
    positions: list[tuple[float, float, float]] = []
    faces: list[int] = []
    uv_values: list[tuple[float, float]] = []

    def add_triangle(points, uvs):
        p0, p1, p2 = points
        normal = normalize(cross(subtract(p1, p0), subtract(p2, p0)))
        tangent, bitangent = normalize_uv_basis(p0, p1, p2, *uvs)
        for point, uv in zip(points, uvs):
            positions.append(point)
            uv_values.append(uv)
            faces.append(len(positions) - 1)
        # SCM vertices are emitted per triangle, so each triangle uses its last
        # three newly appended vertices.
        for local_index in range(3):
            vertex_position = positions[-3 + local_index]
            vertex_uv = uv_values[-3 + local_index]
            vertex = (
                *vertex_position,
                *normal,
                *tangent,
                *bitangent,
                *vertex_uv,
                *vertex_uv,
                0,
                0,
                0,
                0,
            )
            vertices.extend(vertex)

    # A double-sided, closed curved plate: the broad faces curve around the
    # unit's front, while the top, bottom, and end caps give it collision depth.
    vertices: list[float | int] = []
    inner_radius = RADIUS - THICKNESS / 2
    outer_radius = RADIUS + THICKNESS / 2
    start = math.radians(-ARC_DEGREES / 2)
    stop = math.radians(ARC_DEGREES / 2)
    angles = [start + (stop - start) * index / SEGMENTS for index in range(SEGMENTS + 1)]

    for index in range(SEGMENTS):
        u0, u1 = index / SEGMENTS, (index + 1) / SEGMENTS
        outer0b = panel_point(angles[index], outer_radius, 0.0)
        outer1b = panel_point(angles[index + 1], outer_radius, 0.0)
        outer1t = panel_point(angles[index + 1], outer_radius, HEIGHT)
        outer0t = panel_point(angles[index], outer_radius, HEIGHT)
        inner0b = panel_point(angles[index], inner_radius, 0.0)
        inner1b = panel_point(angles[index + 1], inner_radius, 0.0)
        inner1t = panel_point(angles[index + 1], inner_radius, HEIGHT)
        inner0t = panel_point(angles[index], inner_radius, HEIGHT)

        add_triangle((outer0b, outer1b, outer1t), ((u0, 0), (u1, 0), (u1, 1)))
        add_triangle((outer0b, outer1t, outer0t), ((u0, 0), (u1, 1), (u0, 1)))
        add_triangle((inner0b, inner1t, inner1b), ((u0, 0), (u0, 1), (u1, 0)))
        add_triangle((inner0b, inner0t, inner1t), ((u0, 0), (u0, 1), (u1, 1)))

        add_triangle((outer0t, outer1t, inner1t), ((u0, 1), (u1, 1), (u1, 0)))
        add_triangle((outer0t, inner1t, inner0t), ((u0, 1), (u1, 0), (u0, 0)))
        add_triangle((outer0b, inner1b, outer1b), ((u0, 0), (u1, 1), (u1, 0)))
        add_triangle((outer0b, inner0b, inner1b), ((u0, 0), (u0, 1), (u1, 1)))

    # Close the two ends of the arc.
    for side_index, angle_index in enumerate((0, SEGMENTS)):
        angle = angles[angle_index]
        ob = panel_point(angle, outer_radius, 0.0)
        ot = panel_point(angle, outer_radius, HEIGHT)
        ib = panel_point(angle, inner_radius, 0.0)
        it = panel_point(angle, inner_radius, HEIGHT)
        if side_index == 0:
            triangles = ((ob, ot, it), (ob, it, ib))
        else:
            triangles = ((ob, it, ot), (ob, ib, it))
        for tri in triangles:
            add_triangle(tri, ((0, 0), (0, 1), (1, 1)))

    # SCM header offsets and sections follow the MODL v5 layout.
    encoded_name = ROOT_BONE.encode('ascii') + b'\x00'
    name_offset = 48 + pad(48)
    bone_offset = name_offset + len(encoded_name) + pad(name_offset + len(encoded_name))
    vertex_offset = bone_offset + 108 + pad(bone_offset + 108)
    face_offset = vertex_offset + len(positions) * 68
    face_offset += pad(face_offset)
    header = (
        b'MODL',
        5,
        bone_offset,
        1,
        vertex_offset,
        0,
        len(positions),
        face_offset,
        len(faces),
        0,
        0,
        1,
    )

    # The coordinate correction used by the model exporter is a -90-degree
    # rotation around X. Vertices are already in final game coordinates.
    root_matrix = (
        1.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, -1.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )
    half_sqrt = math.sqrt(0.5)
    root_bone = (
        *root_matrix,
        0.0, 0.0, 0.0,
        half_sqrt, -half_sqrt, 0.0, 0.0,
        name_offset, -1, 0, 0,
    )

    with SCM_PATH.open('wb') as output:
        output.write(struct.pack('4s11I', *header))

        def write_section(comment: bytes):
            amount = pad(output.tell()) - 4
            output.write(b'\xC5' * amount)
            output.write(comment)

        write_section(b'NAME')
        output.write(encoded_name)
        write_section(b'SKEL')
        output.write(struct.pack('16f3f4f4i', *root_bone))
        write_section(b'VTXL')
        # The last four values of every vertex are bone indices, packed as bytes.
        for index, position in enumerate(positions):
            # Rebuild each complete 68-byte record in field order.
            offset = index * 20
            values = vertices[offset:offset + 20]
            output.write(struct.pack('16f4B', *values))
        write_section(b'TRIS')
        output.write(struct.pack(f'{len(faces)}H', *faces))

    # Write an OBJ in final world units so the panel's dimensions are easy to inspect.
    obj_lines = ['# Curved forward shield for Seraphim GGA0102; local front is +Z.']
    for point in positions:
        obj_lines.append('v ' + ' '.join(f'{component * SCALE:.6f}' for component in point))
    for index in range(0, len(faces), 3):
        a, b, c = (faces[index + offset] + 1 for offset in range(3))
        obj_lines.append(f'f {a} {b} {c}')
    OBJ_PATH.write_text('\n'.join(obj_lines) + '\n', encoding='utf-8')
    print(f'Wrote {SCM_PATH} ({SCM_PATH.stat().st_size} bytes)')
    print(f'Wrote {OBJ_PATH} ({len(positions)} vertices, {len(faces) // 3} triangles)')


if __name__ == '__main__':
    main()
