import bpy
from mathutils import Vector
from pathlib import Path
s=Path(r'D:\Games\FafModsCreate\mods\Project Roc Unicorns\source-assets\UEL0210')
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(s/'sonic_1.glb'))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH'); print('OBJ',ob.name,len(ob.data.vertices),len(ob.data.polygons),ob.matrix_world[:],flush=True)
scene=bpy.context.scene; scene.render.engine='BLENDER_WORKBENCH'; scene.display.shading.light='STUDIO'; scene.display.shading.color_type='TEXTURE'; scene.display.shading.show_cavity=True; scene.world.color=(.15,.15,.15); scene.render.resolution_x=900; scene.render.resolution_y=700; scene.render.resolution_percentage=100
for name,loc in [('perspective',(1.4,-1.5,1.1)),('front',(0,-2,0)),('side',(2,0,0)),('top',(0,0,2))]:
 bpy.ops.object.camera_add(location=loc); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.45;scene.camera=cam;scene.render.filepath=str(s/('original_'+name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
