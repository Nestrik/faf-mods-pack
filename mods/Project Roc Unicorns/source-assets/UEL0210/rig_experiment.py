import bpy,bmesh,math
from mathutils import Vector
from pathlib import Path
S=Path(r'D:\Games\FafModsCreate\mods\Project Roc Unicorns\source-assets\UEL0210')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(S/'sonic_current.glb'))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');ob.name='Sonic'
while len(ob.data.materials)<3: ob.data.materials.append(ob.data.materials[0])
bm=bmesh.new();bm.from_mesh(ob.data)
# Slice at the turntable, side edges and face of the dish, retaining both sides.
for pt,no in [((0,0,-.095),(0,0,1)),((0,-.08,0),(0,1,0)),((0,-.14,0),(0,1,0)),((0,0,-.065),(0,0,1)),((-.185,0,0),(1,0,0)),((.185,0,0),(1,0,0)),((-.24,0,0),(1,0,0)),((.24,0,0),(1,0,0))]:
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=0.0000001,plane_co=pt,plane_no=no,clear_inner=False,clear_outer=False)
def part(f):
 p=f.calc_center_median()
 if p.z>-.065 and p.y<-.14 and abs(p.x)<.185: return 2
 if p.z>-.095 and p.y<-.08 and abs(p.x)<.24: return 1
 return 0
edges=[e for e in bm.edges if len(e.link_faces)>1 and len({part(f) for f in e.link_faces})>1];bmesh.ops.split_edges(bm,edges=edges)
bm.verts.index_update();bm.verts.ensure_lookup_table(); groups=[set(),set(),set()]
for f in bm.faces:
 k=part(f);f.material_index=k
 for v in f.verts:groups[k].add(v.index)
bm.to_mesh(ob.data);bm.free();ob.data.update()
for name,ids in zip(['UEL0210','Turret','Turret_Barrel'],groups):
 vg=ob.vertex_groups.new(name=name)
 for i in range(0,len(ids),20000):vg.add(list(ids)[i:i+20000],1,'REPLACE')
print('GROUPS',[(name,len(ids)) for name,ids in zip(['hull','yaw','pitch'],groups)],'vertices',len(ob.data.vertices),'faces',len(ob.data.polygons),flush=True)
bpy.ops.object.armature_add(enter_editmode=True);arm=bpy.context.object;arm.name='Sonic_Rig';bones=arm.data.edit_bones
r=bones[0];r.name='UEL0210';r.head=(0,0,0);r.tail=(0,0,.10)
y=bones.new('Turret');y.head=(0,-.23,-.095);y.tail=(0,-.23,.025);y.parent=r
p=bones.new('Turret_Barrel');p.head=(0,-.245,.13);p.tail=(0,-.245,.23);p.parent=y
m=bones.new('Turret_Muzzle');m.head=(0,-.41,.13);m.tail=(0,-.46,.13);m.parent=p
bpy.ops.object.mode_set(mode='OBJECT');ob.parent=arm;mod=ob.modifiers.new('Rig','ARMATURE');mod.object=arm
# Export an explicitly provisional rig with a demonstration action; no engine animation is implied.
part_indices=[p.material_index for p in ob.data.polygons]
for poly in ob.data.polygons: poly.material_index=0
sc=bpy.context.scene
for frame,yaw,pitch in [(1,0,0),(31,45,0),(61,0,0),(91,0,-25),(121,0,0)]:
 sc.frame_set(frame)
 for name,axis,angle in [('Turret',1,yaw),('Turret_Barrel',0,pitch)]:
  bone=arm.pose.bones[name];bone.rotation_mode='XYZ';bone.rotation_euler=(0,0,0);bone.rotation_euler[axis]=math.radians(angle);bone.keyframe_insert(data_path='rotation_euler',frame=frame,group=name)
sc.frame_start=1;sc.frame_end=121;sc.frame_set(1)
if arm.animation_data and arm.animation_data.action:arm.animation_data.action.name='Demonstration_yaw_pitch'
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.wm.save_as_mainfile(filepath=str(S/'sonic_rig_experimental.blend'))
bpy.ops.export_scene.gltf(filepath=str(S/'sonic_rig_experimental.glb'),export_format='GLB',use_selection=True,export_animations=True)
for poly,idx in zip(ob.data.polygons,part_indices):poly.material_index=idx
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.world.color=(.16,.16,.16);sc.render.resolution_x=900;sc.render.resolution_y=700
# Diagnostic copy of material assignment is only for render, not saved or exported.
original=list(ob.data.materials); part_indices=[p.material_index for p in ob.data.polygons]
ob.data.materials.clear()
for name,col in [('Hull',(.5,.5,.5,1)),('Yaw',(.95,.35,.07,1)),('Pitch',(.05,.5,.95,1))]:
 mat=bpy.data.materials.new(name);mat.diffuse_color=col;ob.data.materials.append(mat)
for p,idx in zip(ob.data.polygons,part_indices): p.material_index=idx
bpy.ops.object.camera_add(location=(1.4,-1.5,1.1));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.45;sc.camera=cam
for name,ya,pi in [('rig_groups',0,0),('rig_yaw',45,0),('rig_pitch',0,25)]:
 arm.pose.bones['Turret'].rotation_mode='XYZ';arm.pose.bones['Turret'].rotation_euler[1]=math.radians(ya)
 arm.pose.bones['Turret_Barrel'].rotation_mode='XYZ';arm.pose.bones['Turret_Barrel'].rotation_euler[0]=math.radians(pi)
 bpy.context.view_layer.update();sc.render.filepath=str(S/(name+'.png'));bpy.ops.render.render(write_still=True)




