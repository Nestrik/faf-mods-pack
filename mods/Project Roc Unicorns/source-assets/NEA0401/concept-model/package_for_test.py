"""Create a deployable copy of the complete mod, excluding authoring assets."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

here=Path(__file__).resolve().parent
mod=here.parents[2]
out=here/'Project-Roc-Unicorns-NEA0401-test.zip'
excluded={'source-assets','docs'}
files=[p for p in mod.rglob('*') if p.is_file() and p.relative_to(mod).parts[0] not in excluded]
required=['mod_info.lua','units/NEA0401/NEA0401_lod0.scm',
          'units/NEA0401/NEA0401_albedo.dds','units/NEA0401/NEA0401_specteam.dds',
          'units/NEA0401/NEA0401_normalsTS.dds',
          'units/NEA0401/NEA0401_rings_idle.sca','units/NEA0401/NEA0401_script.lua',
          'units/NEA0401/NEA0401_unit.bp','units/NEA0001/NEA0001_script.lua',
          'units/NEA0001/NEA0001_unit.bp']
assert all((mod/path).is_file() for path in required)
with ZipFile(out,'w',compression=ZIP_DEFLATED,compresslevel=6) as z:
    for path in files: z.write(path,Path(mod.name)/path.relative_to(mod))
with ZipFile(out) as z:
    assert z.testzip() is None
    assert all(f'{mod.name}/{path}' in z.namelist() for path in required)
    assert len(z.namelist())==len(files)
print(f'{out}: {len(files)} files, {out.stat().st_size} bytes, integrity OK')
