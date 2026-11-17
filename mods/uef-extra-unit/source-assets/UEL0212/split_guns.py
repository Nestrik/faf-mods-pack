import bpy
from pathlib import Path
p=Path(r'D:\Games\FafModsCreate\mods\uef-extra-unit\source-assets\UEL0212');bpy.ops.wm.open_mainfile(filepath=str(p/'assembled.blend'));o=bpy.data.objects['Guns'];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.00001);bpy.ops.mesh.separate(type='LOOSE');bpy.ops.object.mode_set(mode='OBJECT')
parts=[x for x in bpy.context.scene.objects if x.type=='MESH' and x.name.startswith('Guns')]
assert len(parts)==3
for x in parts:
 c=sum((x.matrix_world@v.co for v in x.data.vertices),start=__import__('mathutils').Vector())/len(x.data.vertices)
 x.name='Gun_Top' if c.z>.45 else ('Gun_Left' if c.x<0 else 'Gun_Right'); print(x.name,len(x.data.polygons),tuple(round(n,3) for n in c))
bpy.ops.wm.save_as_mainfile(filepath=r'C:\Users\Nestr\OneDrive\Документы\tank_work\assembled_separate.blend')
