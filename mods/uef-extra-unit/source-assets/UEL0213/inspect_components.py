import bpy
from pathlib import Path
S=Path(r'D:\Games\FafModsCreate\mods\uef-extra-unit\source-assets\UEL0213')
for n in ('chassis','launcher','wheel'):
 bpy.ops.import_scene.gltf(filepath=str(S/(n+'_source.glb')))
 o=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.get('seen')][-1]
 o['seen']=True
 print(n,'bounds',tuple(round(x,5) for x in o.dimensions),'location',tuple(round(x,5) for x in o.location),'vertices',len(o.data.vertices),'faces',len(o.data.polygons))
 for v in o.data.vertices: v.co.x+= {'chassis':0,'launcher':2,'wheel':4}[n]
 bpy.ops.wm.save_as_mainfile(filepath=str(S/'components_inspect.blend'))
