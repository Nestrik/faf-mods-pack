import bpy
from pathlib import Path
from mathutils import Vector
S=Path(r'D:\Games\FafModsCreate\mods\Project Roc Unicorns\source-assets\UEL0210\meshy-retexture')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S/'chassis_repaint.glb'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE';sc.display.shading.show_cavity=True;sc.world.color=(.15,.15,.15);sc.render.resolution_x=900;sc.render.resolution_y=700
for name,loc in [('perspective',(1.4,-1.5,1.1)),('side',(2,0,0))]:
 bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.rotation_euler=(Vector((0,0,.13))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=1.45;sc.camera=c;sc.render.filepath=str(S/('final_'+name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(c,do_unlink=True)

