import bpy,bmesh,math
from mathutils import Vector
from pathlib import Path
S=Path(r'D:\Games\FafModsCreate\mods\uef-extra-unit\source-assets\UEL0210')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S/'sonic_current.glb'))
hull=next(o for o in bpy.context.scene.objects if o.type=='MESH');hull.name='Original_chassis'
# Replace only the fused upper weapon assembly. The original lower hull and tracks remain.
bm=bmesh.new();bm.from_mesh(hull.data)
for pt,no in [((0,0,-.095),(0,0,1)),((0,.0,0),(0,1,0)),((0,-.47,0),(0,1,0)),((-.245,0,0),(1,0,0)),((.245,0,0),(1,0,0))]:
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=pt,plane_no=no,clear_inner=False,clear_outer=False)
kill=[f for f in bm.faces if (lambda p:p.z>-.095 and -.47<p.y<0 and abs(p.x)<.245)(f.calc_center_median())]
bmesh.ops.delete(bm,geom=kill,context='FACES');loose=[v for v in bm.verts if not v.link_faces];bmesh.ops.delete(bm,geom=loose,context='VERTS');bm.to_mesh(hull.data);bm.free();hull.data.update()
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=.6;p.inputs['Roughness'].default_value=.45;return m
armor=mat('Dark UEF armor',(.12,.15,.19)); steel=mat('Machined steel',(.24,.27,.30));shadow=mat('Dish face',(.10,.12,.15));accent=mat('Emitter',(.21,.25,.29))
parts=[(hull,'UEL0210')]
def apply_obj(o,n,mat,bone):
 o.name=n;o.data.materials.append(mat);parts.append((o,bone));return o
def cube(n,loc,dims,material,bone,bevel=.008):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  b=o.modifiers.new('Bevel','BEVEL');b.width=bevel;b.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 return apply_obj(o,n,material,bone)
def cyl(n,loc,r,depth,material,bone,axis='Z',verts=32):
 rot=(0,0,0) if axis=='Z' else (0,math.pi/2,0) if axis=='X' else (math.pi/2,0,0)
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc,rotation=rot);return apply_obj(bpy.context.object,n,material,bone)
def rod(n,a,b,r,mat,bone):
 d=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))/2;bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=d.length,location=mid);o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return apply_obj(o,n,mat,bone)
# Original model proportions: large dish on a low circular deck, flanked by armored pivots.
cyl('Turntable bottom',(0,-.235,-.088),.216,.035,armor,'Turret')
cyl('Turntable upper',(0,-.235,-.063),.190,.022,steel,'Turret')
for side in (-1,1):
 x=side*.194
 cube('Antenna support',(x,-.215,.035),(.050,.085,.18),armor,'Turret',.012)
 cyl('Elevation hinge',(x,-.245,.13),.039,.062,steel,'Turret','X',24)
 cyl('Hinge center',(side*.229,-.245,.13),.018,.008,shadow,'Turret','X',20)
# Paraboloid is a proper surface with separate back skin. Center recessed from the forward rim.
N=40;R=10;radius=.177;cz=.13;yc=-.245
vertices=[]
for side in (0,1):
 for j in range(R+1):
  rr=radius*j/R
  for i in range(N):
   a=2*math.pi*i/N; x=rr*math.cos(a); z=cz+rr*math.sin(a); yy=yc-.048*(rr/radius)**2 + side*.010
   vertices.append((x,yy,z))
faces=[]
for side in (0,1):
 base=side*(R+1)*N
 for j in range(R):
  for i in range(N):
   a=base+j*N+i;b=base+j*N+(i+1)%N;c=b+N;d=a+N
   faces.append((a,b,c,d) if side==0 else (d,c,b,a))
for i in range(N):
 a=R*N+i;b=R*N+(i+1)%N;faces.append((a,b,b+(R+1)*N,a+(R+1)*N))
mesh=bpy.data.meshes.new('Parabolic dish');mesh.from_pydata(vertices,[],faces);mesh.update();dish=bpy.data.objects.new('Antenna dish',mesh);bpy.context.collection.objects.link(dish);apply_obj(dish,'Antenna dish',shadow,'Turret_Barrel')
for poly in mesh.polygons: poly.use_smooth=True
# Raised rim follows circular silhouette; the feed is connected to the dish.
bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=8,location=(0,yc-.048,cz),rotation=(math.pi/2,0,0),major_radius=radius,minor_radius=.006);apply_obj(bpy.context.object,'Dish rim',steel,'Turret_Barrel')
feed=(0,-.392,cz)
for a in (math.pi/2,math.pi/2+2*math.pi/3,math.pi/2+4*math.pi/3):
 rod('Feed support',(radius*.82*math.cos(a),-.284,cz+radius*.82*math.sin(a)),feed,.0045,steel,'Turret_Barrel')
cyl('Feed emitter',feed,.014,.045,accent,'Turret_Barrel','Y',20)
cyl('Emitter tip',(0,-.417,cz),.010,.008,steel,'Turret_Barrel','Y',20)
# Rigid weights; transform all meshes into common world coordinates first.
bpy.ops.object.select_all(action='DESELECT')
for o,b in parts:
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.select_set(False)
 vg=o.vertex_groups.new(name=b);vg.add(list(range(len(o.data.vertices))),1,'REPLACE')
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0));arm=bpy.context.object;arm.name='Sonic_Rig';bones=arm.data.edit_bones
root=bones[0];root.name='UEL0210';root.head=(0,0,0);root.tail=(0,0,.1)
yaw=bones.new('Turret');yaw.head=(0,-.235,-.095);yaw.tail=(0,-.235,.005);yaw.parent=root
pitch=bones.new('Turret_Barrel');pitch.head=(0,-.245,.13);pitch.tail=(0,-.245,.23);pitch.parent=yaw
m=bones.new('Turret_Muzzle');m.head=(0,-.422,.13);m.tail=(0,-.47,.13);m.parent=pitch
bpy.ops.object.mode_set(mode='OBJECT')
for o,b in parts:
 o.parent=arm;mod=o.modifiers.new('Armature','ARMATURE');mod.object=arm
sc=bpy.context.scene
for frame,y,p in [(1,0,0),(31,55,0),(61,0,0),(91,0,-25),(121,0,0)]:
 sc.frame_set(frame)
 for name,axis,angle in [('Turret',1,y),('Turret_Barrel',0,p)]:
  bone=arm.pose.bones[name];bone.rotation_mode='XYZ';bone.rotation_euler=(0,0,0);bone.rotation_euler[axis]=math.radians(angle);bone.keyframe_insert(data_path='rotation_euler',frame=frame,group=name)
sc.frame_start=1;sc.frame_end=121;sc.frame_set(1);arm.animation_data.action.name='Aim_demo'
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o,b in parts:o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.wm.save_as_mainfile(filepath=str(S/'sonic_rebuilt_rig.blend'))
bpy.ops.export_scene.gltf(filepath=str(S/'sonic_rebuilt_rig.glb'),export_format='GLB',use_selection=True,export_animations=True)
print('PARTS',len(parts),'FACES',sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o,b in parts),flush=True)
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE';sc.display.shading.show_cavity=True;sc.world.color=(.18,.18,.18);sc.render.resolution_x=900;sc.render.resolution_y=700
for name,loc,frame in [('neutral',(1.4,-1.5,1.1),1),('yaw',(1.4,-1.5,1.1),31),('pitch',(1.4,-1.5,1.1),91),('side',(2,0,0),1),('front',(0,-2,0),1),('top',(0,0,2),1)]:
 sc.frame_set(frame);bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.45;sc.camera=cam;sc.render.filepath=str(S/('rebuilt_'+name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
