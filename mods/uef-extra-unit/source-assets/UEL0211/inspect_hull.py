import bpy
from mathutils import Vector
from pathlib import Path
S=Path(r'D:\Games\FafModsCreate\mods\uef-extra-unit\source-assets\UEL0211');bpy.ops.wm.open_mainfile(filepath=str(S/'launcher_draft.blend'))
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.name!='SourceHull': o.hide_render=True
sc=bpy.context.scene;sc.frame_set(1);sc.render.resolution_x=1200;sc.render.resolution_y=700
for n,loc,scale in [('hull_side',(2,0,0),1.2),('hull_top',(0,0,2),1.2),('hull_iso',(1.4,-1.5,1.1),1.2)]:
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(S/(n+'.png'));bpy.ops.render.render(write_still=True)
