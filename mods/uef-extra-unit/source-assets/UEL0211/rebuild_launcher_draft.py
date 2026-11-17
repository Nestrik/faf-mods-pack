import bpy, bmesh, math
from pathlib import Path
from mathutils import Vector
S=Path(r'D:\Games\FafModsCreate\mods\uef-extra-unit\source-assets\UEL0211')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(S/'4_rocket_launcher_reduced.glb'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
# Remove the original fixed twin-tube block and its lifting strut. The hull is retained.
bm=bmesh.new();bm.from_mesh(body.data)
faces=[]
for f in bm.faces:
 c=f.calc_center_median()
 if (c.y>.255 and c.z>-.075) or (.035<c.y<.35 and c.z>-.075) or any(abs(v.co.x)>.082 and v.co.z<-.075 and -.29<v.co.y<.47 for v in f.verts) or (abs(c.x)>.105 and c.z<-.075 and -.315<c.y<-.29) or (abs(c.x)>.075 and c.z<-.135 and abs(c.y+.35)<.068): faces.append(f)
bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(body.data);bm.free();body.name='SourceHull'
mat=bpy.data.materials.new('Module armor');mat.diffuse_color=(.12,.15,.20,1)
metal=bpy.data.materials.new('Mechanism');metal.diffuse_color=(.26,.29,.32,1)
dark=bpy.data.materials.new('Tube interior');dark.diffuse_color=(.025,.03,.04,1)
team=bpy.data.materials.new('Blue accents');team.diffuse_color=(.015,.08,.45,1)
def cube(name,loc,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
# Simple flat plates cover the local cuts and retain the supplied cab.
deck=cube('Flat replacement deck',(0,.04,-.095),(.205,.77,.015),mat)
for side in (-1,1):
 panel=cube('Flat side armor',(side*.105,.035,-.16),(.008,.79,.12),mat)
 accent=cube('Side team panel',(side*.1095,.19,-.111),(.001,.105,.016),team)
# Launcher in its own coordinate system: bottom at the hinge, +Z toward tube mouths.
rack=cube('Launcher',(0,0,.195),(.225,.195,.39),mat)
for x in (-.053,.053):
 for y in (-.047,.047):
  bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.038,depth=.115,location=(x,y,.372));cut=bpy.context.object
  mod=rack.modifiers.new('Tube bore','BOOLEAN');mod.object=cut;mod.operation='DIFFERENCE';bpy.context.view_layer.objects.active=rack;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# Make bottom of the blind bores dark.
for x in (-.053,.053):
 for y in (-.047,.047):
  bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.037,depth=.004,location=(x,y,.316));o=bpy.context.object;o.name='Bore shadow';o.data.materials.append(dark);o.parent=hinge if False else None
bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0,.395,-.075));hinge=bpy.context.object;hinge.name='Launcher hinge';rack.parent=hinge
for o in [o for o in bpy.context.scene.objects if o.name.startswith('Bore shadow')]: o.parent=hinge
hinge.rotation_euler[0]=math.radians(82);hinge.keyframe_insert(data_path='rotation_euler',frame=1)
hinge.rotation_euler[0]=math.radians(12);hinge.keyframe_insert(data_path='rotation_euler',frame=61)
# Low-poly wheels and separate steering joints. This is a demonstration pose,
# not yet the runtime steering controller.
for side in (-1,1):
 for i,y in enumerate((-.35,-.19,.13,.27)):
  bpy.ops.object.empty_add(type='PLAIN_AXES',location=(side*.125,y,-.205)); steer=bpy.context.object;steer.name=f'Steer_{side}_{i}'
  bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0,0,0));spin=bpy.context.object;spin.name=f'Spin_{side}_{i}';spin.parent=steer
  bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.054,depth=.045,location=(0,0,0),rotation=(0,math.pi/2,0));wheel=bpy.context.object;wheel.name=f'Wheel_{side}_{i}';wheel.data.materials.append(dark);wheel.parent=spin
  bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.023,depth=.049,location=(0,0,0),rotation=(0,math.pi/2,0));hub=bpy.context.object;hub.data.materials.append(team);hub.parent=spin
  spin.rotation_euler.x=0;spin.keyframe_insert(data_path='rotation_euler',frame=1)
  spin.rotation_euler.x=math.pi*2;spin.keyframe_insert(data_path='rotation_euler',frame=61)
  if i<2:
   steer.rotation_euler.z=0;steer.keyframe_insert(data_path='rotation_euler',frame=1)
   steer.rotation_euler.z=math.radians(22);steer.keyframe_insert(data_path='rotation_euler',frame=61)
# Four stabilizers, each with a sideways travel followed by vertical extension.
for side in (-1,1):
 for i,y in enumerate((-.275,.40)):
  bpy.ops.object.empty_add(type='PLAIN_AXES',location=(side*.105,y,-.12));arm=bpy.context.object;arm.name=f'Outrigger_{side}_{i}'
  block=cube('Outrigger arm',(-side*.02,0,0),(.08,.045,.035),mat);block.parent=arm
  bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0,0,-.01));leg=bpy.context.object;leg.name=f'Leg_{side}_{i}';leg.parent=arm
  post=cube('Foot post',(0,0,-.045),(.025,.025,.09),metal);post.parent=leg
  foot=cube('Foot pad',(0,0,-.09),(.065,.055,.012),mat);foot.parent=leg
  arm.location.x=side*.105;arm.keyframe_insert(data_path='location',frame=1);arm.location.x=side*.145;arm.keyframe_insert(data_path='location',frame=30)
  leg.location.z=-.01;leg.keyframe_insert(data_path='location',frame=1);leg.keyframe_insert(data_path='location',frame=30);leg.location.z=-.055;leg.keyframe_insert(data_path='location',frame=61)
# Pivot visible on both sides.
for x in (-.12,.12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.025,depth=.03,location=(x,.395,-.075),rotation=(0,math.pi/2,0));bpy.context.object.data.materials.append(metal)
sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=61
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE';sc.display.shading.show_cavity=True;sc.world.color=(.15,.15,.15);sc.render.resolution_x=900;sc.render.resolution_y=700
bpy.ops.object.camera_add(location=(1.4,-1.5,1.1));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.45;sc.camera=cam
for fr,name in [(1,'transport'),(61,'deployed')]:
 sc.frame_set(fr);sc.render.filepath=str(S/('draft_'+name+'.png'));bpy.ops.render.render(write_still=True)
for fr,name in [(1,'side_transport'),(61,'side_deployed')]:
 sc.frame_set(fr);cam.location=(2,0,0);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(S/('draft_'+name+'.png'));bpy.ops.render.render(write_still=True)
cam.location=(1.4,-1.5,1.1);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(S/'launcher_draft.blend'))
