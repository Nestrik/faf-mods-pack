import bpy
from pathlib import Path
from mathutils import Vector
s=Path(r'D:\Games\FafModsCreate\mods\Project Roc Unicorns\source-assets\UEL0210')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(s/'sonic_1.glb'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');bpy.context.view_layer.objects.active=o;o.select_set(True)
m=o.modifiers.new('10 percent','DECIMATE');m.ratio=.1;m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name);print('SIMPLIFIED',len(o.data.vertices),len(o.data.polygons),flush=True)
bpy.ops.export_scene.gltf(filepath=str(s/'sonic_1_reduced.glb'),export_format='GLB',use_selection=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE';sc.display.shading.show_cavity=True;sc.world.color=(.15,.15,.15);sc.render.resolution_x=900;sc.render.resolution_y=700
for name,loc in [('perspective',(1.4,-1.5,1.1)),('side',(2,0,0)),('front',(0,-2,0)),('top',(0,0,2))]:
 bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.45;sc.camera=cam;sc.render.filepath=str(s/('reduced_'+name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
