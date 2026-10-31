"""Rebuild native tank and optional previews; requires model source from release."""
import argparse,subprocess,sys,shutil
from pathlib import Path
SRC=Path(__file__).resolve().parent
MOD=SRC.parents[2]
ROOT=MOD.parents[1]
p=argparse.ArgumentParser()
p.add_argument('--blender',required=True,help='Blender 4.5 executable')
p.add_argument('--previews',action='store_true',help='Render native mesh views and rebuild UI icon')
a=p.parse_args()
if not (SRC/'approved_hover_v23.blend').is_file():
 p.error('Extract Dush_Nai_Model_Source_v23.zip here first; see README.md')
for name in ['Itha_Yen_Approved_Integration/GGA0401','Itha_Yen_Metal_v2/GGA0401','Dush_Nai_Icon_Targeting_v4']:
 (ROOT/'outputs'/name).mkdir(parents=True,exist_ok=True)
def blender(script):
 subprocess.run([a.blender,'-b','-t','6','--python',str(SRC/script)],check=True)
blender('export_approved_model.py')
subprocess.run([sys.executable,str(SRC/'build_native_materials.py')],check=True)
geo=ROOT/'outputs/Itha_Yen_Approved_Integration/GGA0401'
mat=ROOT/'outputs/Itha_Yen_Metal_v2/GGA0401'
for f in geo.glob('*.scm'):
 shutil.copy2(f,mat/f.name);shutil.copy2(f,MOD/'units/GGA0401'/f.name)
for f in mat.glob('*.dds'):shutil.copy2(f,MOD/'units/GGA0401'/f.name)
# Original projectile previews read these old DDS, deliberately untouched.
from PIL import Image
for suffix in ['albedo','specteam']:
 Image.open(MOD/f'units/GGA0401/GGA0401_{suffix}.dds').save(ROOT/f'outputs/Itha_Yen_Approved_Integration/old_projectile_{suffix}.png')
if a.previews:
 blender('render_metal_review.py')
 blender('render_build_icon.py')
 subprocess.run([sys.executable,str(SRC/'build_build_icon.py')],check=True)
print('Native model/material rebuild completed; game scripts and balance were not rewritten.')
