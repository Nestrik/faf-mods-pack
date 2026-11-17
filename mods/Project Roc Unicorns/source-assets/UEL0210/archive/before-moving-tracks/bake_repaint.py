import bpy,math
from pathlib import Path
from mathutils import Vector
S=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(S/'chassis_original.glb'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');bpy.context.view_layer.objects.active=o;o.select_set(True)
uv_original=o.data.uv_layers.active;uv_original.name='OriginalUV';project=o.data.uv_layers.new(name='Projection')
def material(name,img=None,color=(.055,.065,.08,1)):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');m.node_tree.links.new(em.outputs[0],out.inputs[0]);em.inputs['Color'].default_value=color
 if img:
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(S/img),check_existing=True);t.extension='EXTEND';u=n.new('ShaderNodeUVMap');u.uv_map='Projection';m.node_tree.links.new(u.outputs[0],t.inputs[0]);m.node_tree.links.new(t.outputs['Color'],em.inputs['Color'])
 return m
mats=[material('Hull projection','armor_projection.png'),material('Wheel projection','wheel_strip.png'),material('Dark track edge')];o.data.materials.clear()
for m in mats:o.data.materials.append(m)
counts=[0,0,0]
for p in o.data.polygons:
 c=p.center;n=p.normal
 side=abs(c.x)>.17 and c.z<.195 and abs(n.x)>.40
 edge=(c.z<.025 or (abs(c.y)>.45 and c.z<.20 and abs(n.y)>.60))
 k=1 if side else 2 if edge else 0;p.material_index=k;counts[k]+=1
 for li in p.loop_indices:
  v=o.data.vertices[o.data.loops[li].vertex_index].co
  project.data[li].uv=((v.y+.505)/1.01,(.5+(v.z-.11)/.32)) if side else ((v.x+.265)/.53,(v.y+.505)/1.01)
print('FACE GROUPS',counts,flush=True)
baked=bpy.data.images.new('Chassis_repaint_albedo',width=2048,height=2048,alpha=False)
for m in mats:
 n=m.node_tree.nodes;t=n.new('ShaderNodeTexImage');t.image=baked;n.active=t
 for node in n:node.select=node==t
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=1;sc.render.bake.margin=8;sc.render.bake.use_clear=True
o.data.uv_layers.active=uv_original;uv_original.active_render=True
bpy.ops.object.bake(type='EMIT',uv_layer='OriginalUV');baked.filepath_raw=str(S/'chassis_repaint_albedo.png');baked.file_format='PNG';baked.save()
# Preview only: use a conventional material with the newly baked texture.
m=bpy.data.materials.new('Repaint preview');m.use_nodes=True;nodes=m.node_tree.nodes;p=nodes.get('Principled BSDF');p.inputs['Metallic'].default_value=.25;p.inputs['Roughness'].default_value=.72;t=nodes.new('ShaderNodeTexImage');t.image=baked;u=nodes.new('ShaderNodeUVMap');u.uv_map='OriginalUV';m.node_tree.links.new(u.outputs[0],t.inputs[0]);m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color']);o.data.materials.clear();o.data.materials.append(m)
for poly in o.data.polygons:poly.material_index=0
bpy.ops.wm.save_as_mainfile(filepath=str(S/'chassis_repaint_work.blend'))
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE';sc.display.shading.show_cavity=False;sc.world.color=(.15,.15,.15);sc.render.resolution_x=1000;sc.render.resolution_y=760
for name,loc in [('perspective',(1.4,-1.5,1.1)),('side',(2,0,0)),('rear',(-1.4,1.5,1.1)),('top',(0,0,2))]:
 bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.13))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.4;sc.camera=cam;sc.render.filepath=str(S/('after_'+name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)

