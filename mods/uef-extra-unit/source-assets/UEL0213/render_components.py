import bpy
from pathlib import Path
from mathutils import Vector
S=Path(r'D:\Games\FafModsCreate\mods\uef-extra-unit\source-assets\UEL0213')
for n in ('chassis','launcher','wheel'):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(S/(n+'_source.glb')))
 o=next(o for o in bpy.context.scene.objects if o.type=='MESH');print(n,'min',tuple(round(min(v.co[i] for v in o.data.vertices),3) for i in range(3)),'max',tuple(round(max(v.co[i] for v in o.data.vertices),3) for i in range(3)))
 sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE';sc.world.color=(.15,.15,.15);sc.render.resolution_x=800;sc.render.resolution_y=600
 for view,loc in [('iso',(1.5,-1.5,1.2)),('top',(0,0,2))]:
  bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.35;sc.camera=cam;sc.render.filepath=str(S/(n+'_'+view+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
