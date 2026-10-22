"""Original Seraphim twin-gondola artillery. Blender 4.5 background build."""
import bpy, math, struct, json, sys
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from math import sin, cos, pi

HERE=Path(__file__).resolve(); SRC=HERE.parent; UNIT=SRC.parents[1]/'units/GGA2404'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True;scene.render.fps=30
scene.world.color=(.25,.25,.25);scene.view_settings.view_transform='AgX'
materials=[]
for i,name in enumerate(['Graphite metal','Polished silver','Bright bevel','Team geometric inlay','Recess','Energy rail','Ball lightning','Brushed steel']):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(SRC/'GGA2404_albedo_source.png'),check_existing=True);t.image.alpha_mode='CHANNEL_PACKED'
    l.new(t.outputs['Color'],p.inputs['Base Color']);p.inputs['Metallic'].default_value=.95 if i in (0,1,2,7) else .25
    p.inputs['Roughness'].default_value=[.28,.16,.12,.36,.72,.3,.25,.24][i]
    if i==4:p.inputs['Metallic'].default_value=.85
    if i==3:
        image_node=n.new('ShaderNodeTexImage');image_node.image=bpy.data.images.load(str(SRC/'GGA2404_normalsTS_source.png'),check_existing=True)
        image_node.image.colorspace_settings.name='Non-Color'
        normal_node=n.new('ShaderNodeNormalMap');l.new(image_node.outputs['Color'],normal_node.inputs['Color']);l.new(normal_node.outputs['Normal'],p.inputs['Normal'])
    if i in (3,5,6):
        tint=n.new('ShaderNodeRGB');tint.name='TEAM_COLOR_PREVIEW';tint.outputs[0].default_value=(.025,.22,.9,1)
        l.new(tint.outputs[0],p.inputs['Base Color'])
        if i in (5,6):l.new(tint.outputs[0],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=2.5 if i==5 else 5
    materials.append(m)
# Separate preview materials reuse the same authored game atlas tiles.
for name,tile,power in [('Permanent lightning field',5,1.2),('Charge field boost',6,6.0)]:
    m=materials[tile].copy();m.name=name;m['atlas_tile']=tile
    m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=power
    materials.append(m)
parts=[]
def mesh(name,verts,faces,mat=0,bone='GGA2404',smooth=False,uv=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob)
    for m in materials:me.materials.append(m)
    for p in me.polygons:p.material_index=mat;p.use_smooth=smooth
    layer=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        for j,li in enumerate(p.loop_indices):
            vi=me.loops[li].vertex_index;u,v=uv[vi] if uv else [(0,0),(1,0),(1,1),(0,1)][j%4]
            tile=materials[mat].get('atlas_tile',mat)
            layer.data[li].uv=((tile%4+(20+u*216)/256)/4,1-(tile//4+(20+v*216)/256)/2)
    ob['rig_bone']=bone;ob['asset_part']=True;parts.append(ob);return ob
def tube(name,points,r,mat,bone='GGA2404',sides=4):
    points=[Vector(v) for v in points];verts=[]
    for j,p in enumerate(points):
        d=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized();a=d.cross(Vector((0,0,1)))
        if a.length<.01:a=d.cross(Vector((0,1,0)))
        a.normalize();b=d.cross(a).normalized()
        for k in range(sides):verts.append(p+r*(cos(2*pi*k/sides)*a+sin(2*pi*k/sides)*b))
    faces=[(j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k) for j in range(len(points)-1) for k in range(sides)]
    faces += [tuple(reversed(range(sides))),tuple((len(points)-1)*sides+k for k in range(sides))]
    uv=[(j/(len(points)-1),k/sides) for j in range(len(points)) for k in range(sides)]
    ob=mesh(name,verts,faces,mat,bone,True,uv);ob['decorative_pattern']=(mat==3);return ob
def lathe(name,profile,mat=0,bone='GGA2404',n=72,lobes=0):
    vs=[];uv=[]
    for j,(r,z) in enumerate(profile):
        for k in range(n+1):
            a=2*pi*k/n;rr=r*(1+lobes*cos(3*a));vs.append((rr*cos(a),rr*sin(a),z));uv.append((k/n,j/(len(profile)-1)))
    fs=[(j*(n+1)+k,j*(n+1)+k+1,(j+1)*(n+1)+k+1,(j+1)*(n+1)+k) for j in range(len(profile)-1) for k in range(n)]
    return mesh(name,vs,fs,mat,bone,True,uv)
def sphere(name,center,r,mat=6,bone='Charge',n=24,rings=12):
    vs=[];uv=[]
    for j in range(rings+1):
        a=pi*(.001+.998*j/rings)
        for k in range(n+1):
            b=2*pi*k/n;vs.append(Vector(center)+Vector((r*sin(a)*cos(b),r*sin(a)*sin(b),r*cos(a))));uv.append((k/n,j/rings))
    fs=[(j*(n+1)+k,j*(n+1)+k+1,(j+1)*(n+1)+k+1,(j+1)*(n+1)+k) for j in range(rings) for k in range(n)]
    return mesh(name,vs,fs,mat,bone,True,uv)

exec(compile((HERE.parent/'rich_base.py').read_text(),str(HERE.parent/'rich_base.py'),'exec'),globals())

# Exactly two gondolas, each a pointed hull with inset top panel, rim and inner rail.
def hull_values(t):
    y=-1.56+2.80*t
    width=.003+.345*sin(pi*t)**.72
    # Keep the inward-facing longitudinal spine straight. The previous end rise
    # became an inward hook after the 90-degree hull roll.
    top=1.79875
    return y,width,top
def gondola(sign):
    center=sign*.64;bone='GondolaL' if sign<0 else 'GondolaR';vs=[];uv=[]
    # Cross section gives a broad hard shoulder, curved hull belly and pointed keel.
    cross=[(0,.025),(.64,.015),(1,-.075),(.86,-.25),(.43,-.35),(0,-.39),(-.43,-.35),(-.86,-.25),(-1,-.075),(-.64,.015)]
    n=28
    for j in range(n+1):
        t=j/n;y,w,z=hull_values(t);end=.08+.92*sin(pi*t)**.5
        for k,(x,dz) in enumerate(cross):vs.append((center+x*w,y,z+dz*end));uv.append((j/n,k/9))
    fs=[(j*10+k,j*10+(k+1)%10,(j+1)*10+(k+1)%10,(j+1)*10+k) for j in range(n) for k in range(10)]
    fs += [tuple(reversed(range(10))),tuple(n*10+k for k in range(10))]
    ob=mesh(f'Floating boat hull {sign}',vs,fs,1,bone,True,uv);ob['main_gondola']=True
    # Dark inset top, framed by a silver lip, makes the hull read like a boat instead of a tube.
    vs=[]
    for j in range(25):
        t=.08+.84*j/24;y,w,z=hull_values(t)
        for x in (-.55,0,.55):vs.append((center+x*w,y,z+.030 if x else z+.034))
    fs=[(j*3+k,(j+1)*3+k,(j+1)*3+k+1,j*3+k+1) for j in range(24) for k in range(2)]
    # The top becomes the inward-facing light panel after the roll. Its front
    # face must point out of the hull; the old winding pointed into the metal.
    fs=[tuple(reversed(face)) for face in fs]
    mesh(f'Gondola {sign} upper recessed panel',vs,fs,4,bone,True)
    for s in (-1,1):
        pts=[]
        for j in range(29):
            t=.025+.95*j/28;y,w,z=hull_values(t);pts.append((center+s*.67*w,y,z+.035))
        tube(f'Gondola {sign} coaming {s}',pts,.014,2,bone)
    # A continuous organic outer armor stripe and a brighter inner energy conductor.
    pts=[];inner=[]
    for j in range(23):
        t=.11+.78*j/22;y,w,z=hull_values(t)
        pts.append((center+sign*.96*w,y,z-.10))
        inner.append((center-sign*.87*w,y,z-.065))
    tube(f'Gondola {sign} long inset',pts,.030,0,bone)
    tube(f'Gondola {sign} electric inner lip',inner,.015,5,bone)
    # Raised, pointed silver islands divide the recessed top into Seraphim leaf motifs.
    for q,t in enumerate((.25,.60,.82)):
        vv=[]
        for dt,s in [(-.105,0),(-.02,-.38),(.11,0),(.015,.38)]:
            y,w,z=hull_values(t+dt);vv.append((center+w*s,y,z+.052))
        mesh(f'Gondola {sign} floating silver inlay {q}',vv,[(0,1,2,3)],2,bone)
        # No angular chevron overlay: crop-circle motifs are added after the roll.
gondola(-1);gondola(1)

# Roll each hull 90 degrees about its own longitudinal axis, top faces inward.
for ob in parts:
    if ob['rig_bone'] in ['GondolaL','GondolaR']:
        sign=-1 if ob['rig_bone']=='GondolaL' else 1
        origin=Vector((sign*.64,0,1.80));rot=Matrix.Rotation(-sign*pi/2,3,'Y')
        for v in ob.data.vertices:v.co=origin+rot@(v.co-origin)
        ob['inward_roll_degrees']=-sign*90
exec(compile((HERE.parent/'ring_gondolas.py').read_text(),str(HERE.parent/'ring_gondolas.py'),'exec'),globals())
exec(compile((HERE.parent/'engraved_inlays.py').read_text(),str(HERE.parent/'engraved_inlays.py'),'exec'),globals())
# Move complete gondolas without narrowing their shells or changing the ring bore.
# Ring-center separation: 1.60 -> 1.36, exactly 15 percent closer.
GONDOLA_INSET=.12
for ob in parts:
    if ob['rig_bone'] in ['GondolaL','GondolaR']:
        sign=-1 if ob['rig_bone']=='GondolaL' else 1
        for v in ob.data.vertices:v.co.x-=sign*GONDOLA_INSET
        if 'axis_center' in ob:
            center=list(ob['axis_center']);center[0]-=sign*GONDOLA_INSET;ob['axis_center']=center
charge_center=Vector((0,-.16,1.80))
sphere('Growing ball lightning',charge_center,.34,6,'Charge',32,16)
for j in range(0):  # v8: no permanent meridian filaments
    a=2*pi*j/9;pts=[]
    for k in range(15):
        t=pi*k/14;r=.346+.008*sin(k*2.1+j)
        pts.append(charge_center+Vector((r*sin(t)*cos(a+.10*sin(k*2)),r*sin(t)*sin(a+.10*sin(k*2)),r*cos(t))))
    tube(f'Growing sphere filament {j}',pts,.0055,9,'Charge',5)
# Historical sphere is excluded from SCM; the runtime orb is entirely particles.
for ob in parts:
    if ob['rig_bone']=='Charge':
        for v in ob.data.vertices:v.co=charge_center+(v.co-charge_center)*.97
# There is always a branching electric field, even while the gun is idle.
for bone,count,radius,material in [('Field',5,.004,8),('FieldBoost',5,.006,9),('FieldPeak',4,.009,9)]:
    for j in range(count):
        pts=[]
        for k in range(17):
            t=k/16;y=-1.25+2.05*t;phase=j*1.7
            x=.22*sin(phase+t*5)+.06*sin(k*2.1+j)
            z=1.80+.12*cos(phase+t*6)+.035*sin(k*2.8+j)
            pts.append((x,y,z))
        ob=tube(f'Lightning web {bone} / {j}',pts,radius,material,bone,5);ob['permanent_field']=(bone=='Field')
    # Crosswise streamers tie the two inward-facing emitter plates together.
    for j in range(3):
        y=-.90+j*.63
        pts=[(-.48+.96*k/12,y+.03*sin(k*2+j),1.80+.06*sin(k*2.7+j)) for k in range(13)]
        tube(f'Cross-gap arc {bone} / {j}',pts,radius,material,bone,5)

# Raise the floating assembly another 0.20 game units for the high-arc mortar.
# Keep the rings, charge, muzzle and pitch axis together; only the height changes.
GUN_LIFT=1.10
for ob in parts:
    if ob['rig_bone']!='GGA2404':
        for v in ob.data.vertices:v.co.z+=GUN_LIFT
        if 'axis_center' in ob:
            center=list(ob['axis_center']);center[2]+=GUN_LIFT;ob['axis_center']=center
charge_center.z=1.8+GUN_LIFT

# Rigid native hierarchy: yaw + hover + pitch + recoil; two separate hull bones.
BNAMES=['GGA2404','TurretYaw','Hover','TurretPitch','Recoil','GondolaL','GondolaR','Charge','Muzzle','Field','FieldBoost','FieldPeak']
pivot=(0,-.16,1.8+GUN_LIFT)
defs=[('GGA2404',(0,0,0),None),('TurretYaw',pivot,'GGA2404'),('Hover',pivot,'TurretYaw'),('TurretPitch',pivot,'Hover'),('Recoil',pivot,'TurretPitch'),('GondolaL',(-.64,-.16,1.8+GUN_LIFT),'Recoil'),('GondolaR',(.64,-.16,1.8+GUN_LIFT),'Recoil'),('Charge',tuple(charge_center),'Recoil'),('Muzzle',tuple(charge_center),'Recoil'),('Field',(0,-.3,1.80+GUN_LIFT),'Recoil'),('FieldBoost',(0,-.3,1.80+GUN_LIFT),'Recoil'),('FieldPeak',(0,-.3,1.80+GUN_LIFT),'Recoil')]
bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name='GGA2404';eb=rig.data.edit_bones;eb.remove(eb[0]);bones={}
for name,head,parent in defs:
    if name in ['GondolaL','GondolaR']:
        head=(head[0]-(-1 if name=='GondolaL' else 1)*GONDOLA_INSET,head[1],head[2])
    b=eb.new(name);b.head=head;b.tail=Vector(head)+Vector((0,0,.13));bones[name]=b
    if parent:b.parent=bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for ob in parts:
    ob.parent=rig;g=ob.vertex_groups.new(name=ob['rig_bone']);g.add(list(range(len(ob.data.vertices))),1,'REPLACE')
    mod=ob.modifiers.new('Rigid skeletal deformation','ARMATURE');mod.object=rig


exec(compile((SRC/'native_export.py').read_text(),str(SRC/'native_export.py'),'exec'),globals())
native_parts=[ob for ob in parts if ob['rig_bone']!='Charge']
stats={name:write_scm(UNIT/f'GGA2404_{name}.scm',native_parts,name=='lod1') for name in ['lod0','lod1']}
for ob in list(parts):
 if ob['rig_bone']=='Charge':
  parts.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'GGA2404_source.blend'))
(SRC/'geometry_validation.json').write_text(json.dumps(stats,indent=2))
print('GGA2404_BUILD_COMPLETE',stats,flush=True)
