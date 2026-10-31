"""Visual study using exported SCM geometry; electrical curves approximate engine beams."""
import bpy,struct,math,json,random
from pathlib import Path
from mathutils import Vector
SOURCE_DIR=Path(__file__).resolve().parent
MOD=SOURCE_DIR.parents[2]
ROOT=MOD.parents[1];OUT=ROOT/'outputs/Dush_Nai_Charge_v2'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/Itha_Yen_Metal_v2/GGA0401_game_ready.blend'))
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT'
s.render.resolution_x=640;s.render.resolution_y=512;s.render.resolution_percentage=100
if hasattr(s,'eevee') and hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=8
frames=OUT/'charge_frames';frames.mkdir(exist_ok=True)
rig=bpy.data.objects['GGA0401 game rig']
# Original projectile's actual SCM, UVs and decoded material atlas.
p=MOD/'projectiles/GGP0401/GGP0401_lod0.scm';raw=p.read_bytes();h=struct.unpack_from('<4s11I',raw)
rows=[struct.unpack_from('<16f4B',raw,h[4]+i*68) for i in range(h[6])];ix=struct.unpack_from('<'+'H'*h[8],raw,h[7]);faces=[ix[i:i+3] for i in range(0,len(ix),3)]
me=bpy.data.meshes.new('Original GGP0401 projectile');me.from_pydata([(v[0],-v[2],v[1]) for v in rows],[],faces);me.update();uv=me.uv_layers.new()
for f in me.polygons:
 f.use_smooth=True
 for li,vi in zip(f.loop_indices,f.vertices):uv.data[li].uv=(rows[vi][12],1-rows[vi][13])
orb=bpy.data.objects.new('Original phason sphere charging',me);s.collection.objects.link(orb)
m=bpy.data.materials.new('Old projectile atlas — Seraphim approximate preview');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(OUT/'old_projectile_albedo.png'));t.image.colorspace_settings.name='Non-Color'
sep=n.new('ShaderNodeSeparateColor');l.new(t.outputs[0],sep.inputs[0]);comb=n.new('ShaderNodeCombineColor');l.new(sep.outputs['Blue'],comb.inputs['Red']);l.new(sep.outputs['Blue'],comb.inputs['Green']);l.new(sep.outputs['Green'],comb.inputs['Blue'])
add=n.new('ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=1;add.inputs[2].default_value=(.4,.43,.47,1);l.new(comb.outputs[0],add.inputs[1]);l.new(add.outputs[0],bs.inputs['Base Color']);l.new(add.outputs[0],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1.2;bs.inputs['Metallic'].default_value=.3;bs.inputs['Roughness'].default_value=.24
me.materials.append(m)
boltmat=bpy.data.materials.new('Violet electrical field preview');boltmat.use_nodes=True;bs=boltmat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.36,.09,1,1);bs.inputs['Emission Color'].default_value=(.42,.15,1,1);bs.inputs['Emission Strength'].default_value=10
bolts=[]
for i in range(4):
 c=bpy.data.curves.new('Rapid electrical link','CURVE');c.dimensions='3D';c.bevel_depth=.015;c.bevel_resolution=1;sp=c.splines.new('POLY');sp.points.add(8);o=bpy.data.objects.new(c.name,c);s.collection.objects.link(o);c.materials.append(boltmat);bolts.append(o)
# Pose uses exactly the native .65-unit inward travel, at original model scale 5.
def smooth(t):return t*t*(3-2*t)
def pose(openness):
 for name,sign in [('GondolaLeft',1),('GondolaRight',-1)]:
  pb=rig.pose.bones[name];delta=Vector((sign*.43*(1-openness),0,0));pb.location=pb.bone.matrix_local.to_3x3().inverted()@delta
fps=6;timeline=[]
for frame in range(97):
 time=frame/fps
 if time<3:
  progress=min(1,time/3);openness=smooth(progress);stage='charging';visible=True
 elif time<4:
  progress=1;openness=1;stage='ready';visible=True
 elif time<4.2:
  progress=0;openness=1;stage='shot';visible=False
 elif time<4.8:
  progress=0;openness=1-smooth((time-4.2)/.6);stage='closing';visible=False
 elif time<14:
  progress=min(1,(time-4.8)/9.2);openness=smooth(progress);stage='charging';visible=True
 elif time<15:
  progress=1;openness=1;stage='ready';visible=True
 elif time<15.2:
  progress=0;openness=1;stage='shot';visible=False
 else:
  progress=0;openness=max(0,1-smooth(min(1,(time-15.2)/.6)));stage='closing';visible=False

 pose(openness)
 orbprog=max(.04,progress)
 orb.hide_render=not visible or orbprog<=0;orb.location=(0,0,3.64);orb.scale=(.096*orbprog,)*3;orb.rotation_euler.z=time*.8
 # A flying copy stays the original projectile's full size and travels forward.
 if stage=='shot':
  orb.hide_render=False;since=time-(4 if time<10 else 15);orb.scale=(.2,)*3;orb.location=(0,-since*70,3.64)
 rng=random.Random(frame*311)
 active=stage in ('charging','ready')
 for i,o in enumerate(bolts):
  o.hide_render=not active
  left=(frame+i*2)%5;right=(frame*3+i)%5
  gap=.596-.43*(1-openness);a=Vector((-gap,-[3.2,1.6,0,-1.6,-3.2][left],3.64));b=Vector((gap,-[3.2,1.6,0,-1.6,-3.2][right],3.64))
  for j,point in enumerate(o.data.splines[0].points):
   t=j/8;co=a.lerp(b,t)
   if j not in (0,8):co+=Vector((rng.uniform(-.09,.09),rng.uniform(-.12,.12),rng.uniform(-.13,.13)))*(0.4+progress)
   point.co=(*co,1)
  o.data.bevel_depth=.018+.026*progress
 s.render.filepath=str(frames/f'{frame:03}.png');bpy.ops.render.render(write_still=True)
 timeline.append({'time':time,'stage':stage,'progress':progress,'openness':openness})
 if frame%12==0:print('ANIMATION_FRAME',frame,flush=True)
(OUT/'charge_preview_timeline.json').write_text(json.dumps(timeline,indent=2))
print('CHARGE_PREVIEW_DONE',flush=True)
