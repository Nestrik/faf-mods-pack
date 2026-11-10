"""Export the reviewed concept rig and install it in this mod's unit folder."""
import math, shutil, struct
from pathlib import Path
import build
from geometry import load_scm
from supcom_binary import write_scm

here=Path(__file__).resolve().parent
unit=here.parents[2]/'units'/'NEA0401'
backup=here.parent/'archive'/'before-concept-launch-2026-11-10'
backup.mkdir(parents=True,exist_ok=True)
for source in unit.iterdir():
    if source.is_file() and not (backup/source.name).exists():
        shutil.copy2(source,backup/source.name)

m=build.build()
names=['NEA0401','Crystal']+[f'Hatch{i+1}' for i in range(6)]+[f'Ring{i+1}' for i in range(4)]+['Launch']
hinges=[(build.HINGE_RADIUS*math.cos((k+.5)*math.pi/3),14.25,-12+build.HINGE_RADIUS*math.sin((k+.5)*math.pi/3)) for k in range(6)]
pivots=[(0,0,0),(0,24,3)]+hinges+[(0,y,3) for y in (20,23,26.5,30.5)]+[(0,14.25,-12)]
model=here/'NEA0401_concept_lod0.scm'
write_scm(m,model,names,[-1]+[0]*12,pivots)
vertices,faces=load_scm(model)
header=struct.unpack_from('<4s11I',model.read_bytes())
assert header[3]==len(names) and faces.max()<len(vertices)<65536
for name in ('NEA0401_concept_lod0.scm','NEA0401_rings_idle.sca',
             'NEA0401_albedo.dds','NEA0401_specteam.dds','NEA0401_normalsTS.dds'):
    target='NEA0401_lod0.scm' if name=='NEA0401_concept_lod0.scm' else name
    shutil.copy2(here/name,unit/target)
print(f'Installed {len(vertices)} vertices, {len(faces)} triangles and {len(names)} bones; backup: {backup}')
