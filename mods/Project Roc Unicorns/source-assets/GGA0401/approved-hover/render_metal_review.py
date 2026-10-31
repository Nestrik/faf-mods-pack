import bpy,struct,json,math
from pathlib import Path
from mathutils import Vector
SOURCE_DIR=Path(__file__).resolve().parent
MOD=SOURCE_DIR.parents[2]
ROOT=MOD.parents[1];OUT=ROOT/'outputs/Itha_Yen_Metal_v2'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1250;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Studio world');scene.world.color=(.18,.18,.18)
scene.view_settings.view_transform='AgX'
mat=bpy.data.materials.new('Decoded shipped Unit shader atlas');mat.use_nodes=True
nd=mat.node_tree.nodes;lk=mat.node_tree.links;nd.clear()
output=nd.new('ShaderNodeOutputMaterial');bs=nd.new('ShaderNodeBsdfPrincipled');lk.new(bs.outputs[0],output.inputs[0])
tex={}
for name in ['albedo','specteam']:
 t=nd.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(OUT/f'decoded_{name}.png'));t.image.colorspace_settings.name='Non-Color';t.image.pack();tex[name]=t
sep=nd.new('ShaderNodeSeparateColor');lk.new(tex['specteam'].outputs['Color'],sep.inputs[0])
army=nd.new('ShaderNodeRGB');army.name='ARMY_COLOR';army.outputs[0].default_value=(.24,.015,.75,1)
base=nd.new('ShaderNodeMixRGB');base.blend_type='MULTIPLY';base.inputs[0].default_value=1;base.inputs[2].default_value=(1.9,1.9,1.9,1);lk.new(tex['albedo'].outputs[0],base.inputs[1])
team=nd.new('ShaderNodeMixRGB');lk.new(tex['specteam'].outputs['Alpha'],team.inputs[0]);lk.new(base.outputs[0],team.inputs[1])
scale=nd.new('ShaderNodeMixRGB');scale.blend_type='MULTIPLY';scale.inputs[0].default_value=1;scale.inputs[2].default_value=(.6,.6,.6,1);lk.new(army.outputs[0],scale.inputs[1]);lk.new(scale.outputs[0],team.inputs[2]);lk.new(team.outputs[0],bs.inputs['Base Color']);lk.new(team.outputs[0],bs.inputs['Emission Color'])
em=nd.new('ShaderNodeMath');em.operation='MULTIPLY';em.inputs[1].default_value=.8;lk.new(sep.outputs['Blue'],em.inputs[0]);lk.new(em.outputs[0],bs.inputs['Emission Strength'])
metal=nd.new('ShaderNodeMath');metal.operation='SUBTRACT';metal.inputs[0].default_value=1;lk.new(tex['specteam'].outputs['Alpha'],metal.inputs[1]);lk.new(metal.outputs[0],bs.inputs['Metallic']);bs.inputs['Roughness'].default_value=.32

def load(lod):
 raw=(OUT/f'GGA0401/GGA0401_lod{lod}.scm').read_bytes();h=struct.unpack_from('<4s11I',raw)
 rows=[struct.unpack_from('<16f4B',raw,h[4]+i*68) for i in range(h[6])]
 faces=list(zip(*[iter(struct.unpack_from('<'+'H'*h[8],raw,h[7]))]*3))
 me=bpy.data.meshes.new(f'Native LOD{lod}');me.from_pydata([(r[0]/5,-r[2]/5,r[1]/5) for r in rows],[],faces);me.update()
 for p in me.polygons:p.use_smooth=True
 me.normals_split_custom_set_from_vertices([(r[3],-r[5],r[4]) for r in rows])
 uv=me.uv_layers.new(name='Native DDS UV')
 for p in me.polygons:
  for li,vi in zip(p.loop_indices,p.vertices):uv.data[li].uv=(rows[vi][12],1-rows[vi][13])
 ob=bpy.data.objects.new(f'GGA0401 exported LOD{lod}',me);scene.collection.objects.link(ob);me.materials.append(mat)
 return ob,rows,raw,h
ob,rows,raw,h=load(0)
# Native game rig, retained in editable exported model; vertices rigid-weighted.
rigdata=bpy.data.armatures.new('Native GGA0401 bones');rig=bpy.data.objects.new('GGA0401 game rig',rigdata);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
world=[]
for i in range(h[3]):
 b=struct.unpack_from('<16f3f4f4i',raw,h[2]+i*108);name=raw[b[23]:].split(b'\0')[0].decode();p=Vector(b[16:19]);parent=b[24];w=p+(world[parent] if parent>=0 else Vector((0,0,0)));world.append(w)
 bone=rigdata.edit_bones.new(name);bone.head=(w.x/5,-w.z/5,w.y/5);bone.tail=bone.head+Vector((0,-.12,0))
 if parent>=0:bone.parent=rigdata.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
for i,b in enumerate(rigdata.bones):
 vg=ob.vertex_groups.new(name=b.name);vi=[j for j,r in enumerate(rows) if r[16]==i]
 if vi:vg.add(vi,1,'REPLACE')
mod=ob.modifiers.new('Native rigid bone weights','ARMATURE');mod.object=rig
for lod in [1,2]:
 o,_,_,_=load(lod);o.hide_render=True;o.hide_set(True)
# Neutral studio, rebuilt after reading exported meshes.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.04));floor=bpy.context.object;floor.name='Studio floor';fm=bpy.data.materials.new('Floor');fm.diffuse_color=(.12,.13,.15,1);floor.data.materials.append(fm)
for loc,power,size in [((2,-6,10),1700,7),((-6,0,7),1800,6),((3,6,9),2300,5)]:
 data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.shape='DISK';data.size=size;light=bpy.data.objects.new(data.name,data);scene.collection.objects.link(light);light.location=loc;light.rotation_euler=(Vector((0,0,1.5))-light.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=11.7
# Simple bloom for emissive lining.
scene.use_nodes=True;cn=scene.node_tree.nodes;cn.clear();rl=cn.new('CompositorNodeRLayers');glare=cn.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.threshold=.7;co=cn.new('CompositorNodeComposite');scene.node_tree.links.new(rl.outputs['Image'],glare.inputs['Image']);scene.node_tree.links.new(glare.outputs['Image'],co.inputs[0])
def render(name,position,target=(0,0,1.6)):
 cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
render('game_model',(10,-13,10));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'GGA0401_game_ready.blend'))
army.outputs[0].default_value=(1,1,1,1);render('white_team_proof',(10,-13,10));army.outputs[0].default_value=(.24,.015,.75,1)
render('side',(13,0,3.3))
print('NATIVE_PREVIEWS_DONE',flush=True)
