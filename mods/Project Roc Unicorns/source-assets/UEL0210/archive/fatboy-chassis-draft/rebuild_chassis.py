import bpy, bmesh
from pathlib import Path
from mathutils import Vector
S=Path(r'D:\Games\FafModsCreate\mods\uef-extra-unit\source-assets\UEL0210')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(S/'sonic_1.glb'))
upper=next(o for o in bpy.context.scene.objects if o.type=='MESH');upper.name='Original_upper'
# Cut away the original lower chassis; preserve the original antenna and upper deck.
bm=bmesh.new();bm.from_mesh(upper.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=0.00001,plane_co=(0,0,-.105),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
bm.to_mesh(upper.data);bm.free();upper.data.update()
bpy.context.view_layer.objects.active=upper;upper.select_set(True)
mod=upper.modifiers.new('Simplify upper assembly','DECIMATE');mod.ratio=.18;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
print('UPPER',len(upper.data.polygons),flush=True)
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.63;return m
armor=mat('UEF armor',(.12,.15,.19)); track=mat('Track dark metal',(.055,.065,.075));steel=mat('Track link',(.18,.20,.22))
def cube(name,loc,scale,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new('Beveled edges','BEVEL');mod.width=bevel;mod.segments=1;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
cube('Lower hull',(0,0,-.215),(.38,.85,.22),armor,.025)
for sx in (-1,1):
 for cy in (-.245,.245):
  x=sx*.235
  cube('Track pod',(x,cy,-.24),(.105,.43,.17),track,.035)
  cube('Armored fender',(x,cy,-.143),(.11,.42,.035),armor,.009)
  # Segmented shoes across the exposed belt, keeping parts simple and readable.
  for j in range(8):
   y=cy-.17+j*.0485
   cube('Tread shoe',(x,y,-.329),(.10,.017,.012),steel,.002)
  for j in range(6):
   y=cy-.145+j*.058
   bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=.038,depth=.008,location=(sx*.292,y,-.245),rotation=(0,1.57079632679,0));bpy.context.object.name='Track roller';bpy.context.object.data.materials.append(steel)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];print('TOTAL',sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),flush=True)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(S/'sonic_fatboy_chassis_draft.glb'),export_format='GLB',use_selection=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE';sc.display.shading.show_cavity=True;sc.world.color=(.18,.18,.18);sc.render.resolution_x=1000;sc.render.resolution_y=760;sc.render.resolution_percentage=100
for name,loc in [('perspective',(1.4,-1.5,1.1)),('side',(2,0,0)),('front',(0,-2,0)),('top',(0,0,2))]:
 bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.45;sc.camera=cam;sc.render.filepath=str(S/('fatboy_chassis_'+name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
