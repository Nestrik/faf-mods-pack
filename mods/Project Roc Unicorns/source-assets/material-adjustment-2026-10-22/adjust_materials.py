"""Texture-only rebuild and exported-SCM/DDS previews; never writes geometry.

Run with the project's Python + numpy + Pillow. Original materials are archived
beside this script. The stock XSL0307 reused by GGA0102 and energy effects are
intentionally outside the custom hull material pass.
"""
from pathlib import Path
from io import BytesIO
import importlib.util
import inspect
import json
import hashlib
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ARCHIVE = HERE / 'archive'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def save_dds(image, path, *, independent_channels=True):
    """BC3 via Pillow's compiled encoder, independent data-channel mipmaps."""
    current = image.convert('RGBA')
    levels = []
    while True:
        stream = BytesIO()
        current.save(stream, format='DDS', pixel_format='DXT5')
        levels.append(stream.getvalue()[128:])
        if current.size == (1, 1):
            break
        size = (max(1, current.width // 2), max(1, current.height // 2))
        current = Image.merge('RGBA', tuple(c.resize(size, Image.Resampling.LANCZOS)
                                            for c in current.split()))
    w, h = image.size
    header = [124, 0xA1007, h, w, ((w+3)//4)*((h+3)//4)*16, 0, len(levels)]
    header += [0]*11 + [32, 4, 0x35545844, 0, 0, 0, 0, 0] + [0x401008, 0, 0, 0, 0]
    Path(path).write_bytes(b'DDS ' + struct.pack('<31I', *header) + b''.join(levels))


def load_mip(path, level=0):
    data = Path(path).read_bytes()
    h, w = struct.unpack_from('<II', data, 12)
    count = struct.unpack_from('<I', data, 28)[0]
    assert 0 <= level < count
    offset = 128
    for _ in range(level):
        offset += ((w+3)//4)*((h+3)//4)*16
        w, h = max(1, w//2), max(1, h//2)
    header = bytearray(data[:128])
    struct.pack_into('<II', header, 12, h, w)
    struct.pack_into('<I', header, 28, 1)
    length = ((w+3)//4)*((h+3)//4)*16
    return Image.open(BytesIO(header + data[offset:offset+length])).convert('RGBA')


def fabricator(unit, original_prefix, pattern):
    """Own Seraphim atlas in the existing 4x2 UV layout; no stock art copied."""
    folder = ROOT / 'units' / unit
    source = ROOT / 'source-assets' / unit
    source.mkdir(exist_ok=True)
    original = ARCHIVE / 'units' / unit
    old_spec = np.array(Image.open(original / f'{original_prefix}_specteam.dds').convert('RGBA'))
    height, width = old_spec.shape[:2]
    w, h = width//4, height//2
    u, v = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    lines, engraving = pattern(u, v)
    albedo = np.zeros_like(old_spec)
    specular = np.zeros_like(old_spec)
    normals = np.full_like(old_spec, 128)
    # Retain each tile's purpose: dark frame, armor, edge, steel, joints,
    # crystal, lights, inset panel. Old violet paint is replaced with steel.
    palette = [(32,39,44),(64,74,80),(100,111,118),(58,69,76),
               (17,23,26),(53,83,76),(47,76,65),(32,42,46)]
    reflection = [178,215,228,210,135,110,140,185]
    gloss = [165,188,207,185,130,180,165,173]
    for tile, color in enumerate(palette):
        x, y = (tile%4)*w, (tile//4)*h
        region = np.s_[y:y+h, x:x+w]
        grain = .65*np.sin(u*w*.58+v*h*.17) + .6*np.sin(v*h*.8)
        weather = np.sin(13*u+7*v)*np.sin(21*v-9*u)
        rgb = np.array(color, float) + (grain+weather*2)[:,:,None]
        s = np.zeros((h,w,4), float)
        s[:,:,0], s[:,:,1] = reflection[tile], gloss[tile]
        mask = old_spec[region][:,:,3].astype(float)
        if tile in (0,1,2,3,7):
            # Fine concentric organic motifs keep UV seams and moving parts intact.
            mask = np.maximum(mask, lines*(170 if tile in (0,7) else 220))
            rgb *= 1-.2*engraving[:,:,None]
            s[:,:,0] -= engraving*12
            gy, gx = np.gradient(-engraving)
            normals[region][:,:,1] = np.clip(127.5-gy*55,0,255).astype('uint8')
            normals[region][:,:,3] = np.clip(127.5-gx*55,0,255).astype('uint8')
        if tile in (5,6):
            s[:,:,2] = 55 if tile == 5 else 90
        albedo[region][:,:,:3] = np.clip(rgb,0,255).astype('uint8')
        albedo[region][:,:,3] = np.clip(mask,0,255).astype('uint8')
        specular[region] = np.clip(s,0,255).astype('uint8')
    for suffix, data in [('albedo',albedo),('specteam',specular),('normalsTS',normals)]:
        im = Image.fromarray(data)
        im.save(source / f'{unit}_{suffix}_source.png')
        save_dds(im, folder / f'{original_prefix}_{suffix}.dds')
    bp = folder / f'{unit}_unit.bp'
    bp.write_text(bp.read_text().replace("ShaderName = 'Unit'", "ShaderName = 'Seraphim'"))


def rebuild():
    # These generators have the darker palette adjustment in their source.
    for unit, filename in [('GGA0101','launcher_geometry.py'),
                           ('GGA1401','reactor_geometry.py'),
                           ('GGA2301','prism_reference_model.py'),
                           ('GGA2401','artillery_geometry.py')]:
        src = ROOT / 'source-assets' / unit
        geom = module(src / filename, 'material_' + unit)
        geom.make_textures(src, ROOT/'units'/unit, save_dds)
    # Rebuild the existing scorched wreck map from the newly darkened live map.
    src = ROOT/'source-assets/GGA0101'
    data = np.array(Image.open(src/'GGA0101_albedo_source.png'))
    y,x = np.mgrid[:data.shape[0], :data.shape[1]]
    burn = .48+.25*(np.sin(x*.031+y*.012)*np.sin(y*.043-x*.008)+1)/2
    data[:,:,:3] = np.clip(data[:,:,:3]*burn[:,:,None]+(10,8,6),0,255).astype('uint8')
    data[:,:,3] = 0
    im = Image.fromarray(data)
    im.save(src/'GGA0101_wreck_albedo_source.png')
    save_dds(im, ROOT/'props/GGA0101_wreck/GGA0101_wreck_albedo.dds')
    for unit, prefix in [('GGA1104','zsb1106'),('GGA1204','zsb1206'),('GGA1304','zsb1306')]:
        fabricator(unit, prefix, geom.seraphim_inlays)


def preview():
    geom = module(ROOT/'source-assets/GGA2401/artillery_geometry.py', 'preview_geometry')
    # Reuse the established exported-mesh rasterizer with generic file lookup.
    # Lighting is approximate; game PBR/cubemaps and bloom require a match.
    source = inspect.getsource(geom.render_scm)
    source = source.replace('team=base[:,3:4]', 'team=base[:,3:4] if shader == "Seraphim" else packed[:,3:4]')
    source = source.replace('base=(base[:,[2,2,1]]+np.array((.4,.43,.47)))*.8',
                            'base=(base[:,[2,2,1]]+np.array((.4,.43,.47)))*.8 if shader == "Seraphim" else base[:,:3]')
    cards = []
    for folder in sorted((ROOT/'units').iterdir()):
        alb = list(folder.glob('*albedo.dds'))
        if not alb:
            continue
        unit = folder.name
        prefix = alb[0].name[:-len('_albedo.dds')]
        scm = next(folder.glob('*lod0.scm'))
        bp = '\n'.join(p.read_text() for p in folder.glob('*.bp'))
        shader = 'Seraphim' if "ShaderName = 'Seraphim'" in bp else 'Unit'
        row = Image.new('RGB', (1200, 350), (23,26,30))
        draw = ImageDraw.Draw(row)
        for column, (label, texture_folder, angle, elevation, mip, team) in enumerate([
                ('Before', ARCHIVE/'units'/unit, 35,34,0,(.12,.8,.25)),
                ('After', folder, 35,34,0,(.12,.8,.25)),
                ('Side / blue', folder, 90,18,0,(.12,.35,1)),
                ('Top / mip2', folder, 0,68,2,(.12,.8,.25))]):
            local_shader = shader
            if label == 'Before':
                old_bp = '\n'.join(p.read_text() for p in texture_folder.glob('*.bp'))
                local_shader = 'Seraphim' if "ShaderName = 'Seraphim'" in old_bp else 'Unit'
            def lookup(path, level, texture_folder=texture_folder):
                return load_mip(texture_folder / Path(path).name.replace('GGA2401_', prefix+'_'),level)
            namespace = dict(vars(geom), load_dds_mip=lookup, shader=local_shader)
            exec(source, namespace)
            output = HERE/f'{unit}_{column}.png'
            namespace['render_scm'](scm, folder, output, azimuth=angle, elevation=elevation,
                                    texture_mip=mip, player=team, size=300)
            im = Image.open(output)
            row.paste(im,(column*300,35))
            draw.text((column*300+8,10),f'{unit}: {label}',fill='white')
        row.save(HERE/f'{unit}_comparison.jpg',quality=94)
        cards.append(row)
        print('Rendered',unit,flush=True)
    sheet = Image.new('RGB',(1200,350*len(cards)))
    for i, card in enumerate(cards):
        sheet.paste(card,(0,i*350))
    sheet.save(HERE/'all_models_comparison.jpg',quality=93)


if __name__ == '__main__':
    if '--preview' in sys.argv:
        preview()
    else:
        rebuild()
        print('Rebuilt custom hull materials; geometry and animations untouched.')
