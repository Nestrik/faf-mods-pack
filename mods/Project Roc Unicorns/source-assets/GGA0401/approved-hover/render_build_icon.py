"""Render the actual exported Dush'Nai geometry as transparent construction art."""
import bpy
from pathlib import Path
from mathutils import Vector
SOURCE_DIR=Path(__file__).resolve().parent
MOD=SOURCE_DIR.parents[2]
ROOT=MOD.parents[1];OUT=ROOT/'outputs/Dush_Nai_Icon_Targeting_v4'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/Itha_Yen_Metal_v2/GGA0401_game_ready.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48
s.render.resolution_x=768;s.render.resolution_y=768;s.render.resolution_percentage=100
s.render.film_transparent=True
bpy.data.objects['Studio floor'].hide_render=True
for o in bpy.data.objects:
 if o.type=='LIGHT':o.data.energy*=.60
s.world.color=(.055,.055,.055)
mat=bpy.data.materials['Decoded shipped Unit shader atlas'];mat.node_tree.nodes['ARMY_COLOR'].outputs[0].default_value=(.32,.025,1,1)
cam=s.camera;cam.location=(10,-14,16);cam.rotation_euler=(Vector((0,-.1,1.7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.4
# The model's paired rings and eight-petal hull stay unobscured for readability
# when the icon is reduced to FAF's 64-pixel construction-button size.
s.render.filepath=str(OUT/'Dush_Nai_icon_art.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Dush_Nai_icon_scene.blend'))
print('ICON_ART_DONE',flush=True)
