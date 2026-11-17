import bpy
from pathlib import Path
from mathutils import Vector
s=Path(r'D:\Games\FafModsCreate\mods\Project Roc Unicorns\source-assets\UEL0210')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(s/'sonic_1.glb'))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');bpy.context.view_layer.objects.active=ob
# Weld coincident positions before simplification; UVs remain per loop.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=0.00001);bpy.ops.object.mode_set(mode='OBJECT')
# Partition on triangle centers: dish and emitter, rotating mount, chassis.
for p in ob.data.polygons:
 c=sum((ob.data.vertices[v].co for v in p.vertices),Vector())/len(p.vertices)
 p.material_index=2 if c.z>-.035 and c.y<-.245 and abs(c.x)<.19 else 1 if c.z>-.115 and c.y<.055 and abs(c.x)<.245 else 0
while len(ob.data.materials)<3: ob.data.materials.append(ob.data.materials[0])
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for group in (2,1):
 for p in ob.data.polygons:p.select=p.material_index==group
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
 bpy.context.view_layer.objects.active=ob;ob.select_set(True)
parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
print('PARTS',[(o.name,len(o.data.polygons)) for o in parts],flush=True)
for o in parts:
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 mod=o.modifiers.new('Reduce polygons','DECIMATE');mod.ratio=.10;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 print('REDUCED',o.name,len(o.data.vertices),len(o.data.polygons),flush=True)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(s/'sonic_1_reduced_parts.glb'),export_format='GLB',use_selection=True)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.world.color=(.15,.15,.15);scene.render.resolution_x=900;scene.render.resolution_y=700
for i,o in enumerate(parts):
 mat=bpy.data.materials.new('check'+str(i));mat.diffuse_color=[(.45,.45,.45,1),(.1,.55,.9,1),(.95,.35,.1,1)][i];o.data.materials.clear();o.data.materials.append(mat)
bpy.ops.object.camera_add(location=(1.4,-1.5,1.1));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.45;scene.camera=cam;scene.render.filepath=str(s/'parts_check.png');bpy.ops.render.render(write_still=True)

