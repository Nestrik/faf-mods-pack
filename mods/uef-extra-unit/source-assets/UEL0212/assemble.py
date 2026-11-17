import bpy,json,math
from pathlib import Path
from mathutils import Vector
s=Path(r'C:\Users\Nestr\OneDrive\Документы\tank_work')
files=[r'C:\Users\Nestr\Downloads\44e6f148-base-b236bd5a.glb',r'C:\Users\Nestr\Downloads\c5319545-tower-05e10b15.glb',r'C:\Users\Nestr\Downloads\75c0895b-canon-381f5861.glb']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
obs=[]
for i,f in enumerate(files):
 before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=f);o=next(x for x in set(bpy.context.scene.objects)-before if x.type=='MESH');o.name=['Hull','Turret','Guns'][i]
 if i==1:o.scale=(.52,)*3;o.location=(0,0,.235)
 if i==2:o.scale=(.52,)*3;o.location=(0,-.385,.235)
 obs.append(o)
 # Preserve embedded color texture for atlas.
 images=[n.image for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
 print('IMAGES',i,[(im.name,im.size[:]) for im in images],flush=True)
 if images: images[0].save_render(str(s/f'texture{i}.png'))
bpy.context.view_layer.update()
# Export triangulated loop data in game coordinates.
data=[]
for i,o in enumerate(obs):
 me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
 for tri in me.loop_triangles:
  for li in tri.loops:
   loop=me.loops[li];p=o.matrix_world@me.vertices[loop.vertex_index].co;n=(o.matrix_world.to_3x3()@loop.normal).normalized();t=uv[li].uv
   data.append([p.x*2.7,p.z*2.7,-p.y*2.7,n.x,n.z,-n.y,t.x,t.y,i])
(s/'mesh.json').write_text(json.dumps(data))
bpy.ops.wm.save_as_mainfile(filepath=str(s/'assembled.blend'))
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='TEXTURE';scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True;scene.world.color=(.22,.22,.22);scene.render.resolution_x=900;scene.render.resolution_y=700
for label,loc in [('front',(0,-4,1.4)),('side',(4,-.1,1.2)),('perspective',(2.8,-4,2.7)),('top',(0,-.01,5))]:
 bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.35))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.9;scene.camera=cam;scene.render.filepath=str(s/f'preview_{label}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
