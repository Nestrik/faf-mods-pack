"""Author finite bright phason-impact emitters using native game sprites.

This writes only the three GGA0401 emitters. It does not modify the weapon,
stock effects, charge animation or another unit's resources.
"""
from pathlib import Path

MOD = Path(__file__).resolve().parents[2]
EFFECTS = MOD / 'effects/emitters'


def curve(value, spread=0):
    return {'XRange': 1, 'Keys': [{'x': 0, 'y': value, 'z': spread}]}


def lua(value, depth=0):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return "'" + value + "'"
    if isinstance(value, (int, float)):
        return str(value)
    indent = '    ' * depth
    if isinstance(value, list):
        return '{ ' + ', '.join(lua(x, depth) for x in value) + ' }'
    if set(value) <= {'x', 'y', 'z'}:
        return '{ ' + ', '.join(f'{k} = {lua(v)}' for k, v in value.items()) + ' }'
    return '{\n' + ''.join(f'{indent}    {k} = {lua(v, depth+1)},\n' for k, v in value.items()) + indent + '}'


def emitter(texture, ramp, duration, particle_life, rate, start, end, flat=False):
    result = {
        'Lifetime': duration, 'Repeattime': 1,
        'Blendmode': 3, 'LODCutoff': 400,
        'LowFidelity': True, 'MedFidelity': True, 'HighFidelity': True,
        'LocalVelocity': False, 'LocalAcceleration': False, 'Gravity': False,
        'AlignRotation': False, 'AlignToBone': False, 'Flat': flat,
        'EmitIfVisible': True, 'CreateIfVisible': False, 'CatchupEmit': True,
        'InterpolateEmission': True,
        'Texture': '/textures/particles/' + texture,
        'RampTexture': '/textures/particles/' + ramp,
        'TextureFramecount': 1, 'TextureStripcount': 1,
        'EmitRateCurve': curve(rate), 'LifetimeCurve': curve(particle_life),
        'VelocityCurve': curve(0), 'ResistanceCurve': curve(0),
        'SizeCurve': curve(0), 'StartSizeCurve': curve(start), 'EndSizeCurve': curve(end),
        'InitialRotationCurve': curve(180, 360), 'RotationRateCurve': curve(0),
        'FrameRateCurve': curve(0), 'TextureSelectionCurve': curve(0),
        'RampSelectionCurve': curve(0),
    }
    for axis in 'XYZ':
        result[axis + 'DirectionCurve'] = curve(0)
        result[axis + 'PosCurve'] = curve(0.15 if axis == 'Y' else 0)
        result[axis + 'AccelCurve'] = curve(0)
    return result


def main():
    # Several overlapping additive sprites make a white hot initial flash;
    # short lifetimes keep the target readable after the impact.
    flash = emitter('glow_02.dds', 'ramp_white_29.dds', .10, .30, 40, 5.5, .5)
    ring = emitter('ring_11.dds', 'ramp_blue_16.dds', .10, .65, 20, .6, 9, flat=True)
    arcs = emitter('electricity_09.dds', 'ramp_lightning_01.dds', .15, .45, 90, 1.8, .15)
    arcs['LifetimeCurve'] = curve(.45, .12)
    arcs['VelocityCurve'] = curve(5, 2)
    arcs['RotationRateCurve'] = curve(220, 140)
    for axis in 'XYZ':
        arcs[axis + 'DirectionCurve'] = curve(0, 1)
        arcs[axis + 'PosCurve'] = curve(.25 if axis == 'Y' else 0, .3)
    EFFECTS.mkdir(parents=True, exist_ok=True)
    for name, data in [('flash', flash), ('ring', ring), ('arcs', arcs)]:
        (EFFECTS / f'gga0401_impact_{name}_emit.bp').write_text(
            '-- GGA0401 phason impact: finite visual particles, no damage.\n'
            + 'EmitterBlueprint ' + lua(data) + '\n', encoding='utf-8')
    print('Wrote GGA0401 flash, expanding ring and electrical arcs.')


if __name__ == '__main__':
    main()
