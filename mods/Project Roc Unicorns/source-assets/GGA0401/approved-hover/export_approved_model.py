import bpy, math, struct, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
SOURCE_DIR=Path(__file__).resolve().parent
MOD=SOURCE_DIR.parents[2]
ROOT=MOD.parents[1]
SRC=MOD/'source-assets/GGA0401/approved-hover'
OUT=ROOT/'outputs/Itha_Yen_Approved_Integration'
OUT.mkdir(parents=True,exist_ok=True)
UNIT=OUT/'GGA0401';UNIT.mkdir(exist_ok=True)
SOURCE=SOURCE_DIR/'approved_hover_v23.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
CORR=Matrix(((1,0,0),(0,0,1),(0,-1,0)))
SCALE=5.0
# Native identity-oriented bones: +Y up, +Z forward, matching existing weapon scripts.
names=['GGA0401','MainYaw','MainPitch','MainMuzzle','ShieldCore','PortHull','StarboardFore','StarboardAft','AftShard']
parents=[-1,0,1,2,0,0,0,0,0]
world=[(0,0,0),(0,18.2,0),(0,18.2,0),(0,18.2,0),(0,6,0),(-12,5,0),(12,5,10),(12,5,-10),(0,5,-13)]
for i,(x,y,z) in enumerate([(-12,8,10),(12,8,10),(-12,8,-10),(12,8,-10)],1):
 b=len(names);names += [f'AA{i}Yaw',f'AA{i}Pitch',f'AA{i}Muzzle'];parents += [0,b,b+1];world += [(x,y,z),(x,y+.5,z),(x,y+.5,z+1)]
for name,x in [('GondolaLeft',-.925*SCALE),('GondolaRight',.925*SCALE)]:
 names.append(name);parents.append(2);world.append((x,18.2,0))
# Longitudinal electrode anchors inherit each moving gondola (not MainPitch alone).
for side,parent,x in [('L',21,-2.98),('R',22,2.98)]:
 for i,z in enumerate([16,8,0,-8,-16],1):
  names.append(f'Charge{side}{i}');parents.append(parent);world.append((x,18.2,z))
# Legacy floating-island bones deliberately have no geometry: v23 has a continuous hull.
# Existing unit Lua and all five weapons remain byte-for-byte unchanged.
objects=[o for o in scene.objects if o.type=='MESH' and o.name not in ['Plane','Charge presentation core'] and not o.name.startswith('Energy bridge')]
source_bounds=[(o.matrix_world@v.co) for o in objects for v in o.data.vertices]
print('SOURCE',len(objects),flush=True)

def category(mat):
 if mat.get('team_color_texture'):return 'gondola'
 if mat.get('fixed_ring_emission'):return 'violet'
 if mat.get('army_color_driven'):
  return 'glow' if 'underglow' in mat.name or 'inner-edge' in mat.name else 'team'
 return 'edge' if 'bevel' in mat.name else 'recess' if 'recess' in mat.name else 'steel' if 'steel' in mat.name else 'metal'
# Flat palette tiles occupy bottom half of 4096x2048 atlas. Projected gondola mask in top half.
tiles={'metal':(.0625,.75),'edge':(.1875,.75),'recess':(.3125,.75),'steel':(.4375,.75),'team':(.5625,.75),'glow':(.6875,.75),'violet':(.8125,.75)}

def make_lod(lod):
 rows=[];ids=[];lookup={};stats=[]
 for oi,ob in enumerate(objects):
  if ob.name=='Hybrid gondola LEFT':continue # mirror exported right exactly, including simplification
  tmp=ob.copy();tmp.data=ob.data.copy();scene.collection.objects.link(tmp)
  # v23 source meshes already contain the applied geometry. Preserve any authored modifiers.
  bpy.context.view_layer.objects.active=tmp
  for m in list(tmp.modifiers):
   if m.type=='ARMATURE':tmp.modifiers.remove(m)
  if ob.name.startswith('Hybrid gondola'):ratio=[.075,.037,.018][lod]
  elif 'Continuous armor' in ob.name:ratio=[.026,.012,.005][lod]
  elif 'Detailed mirrored' in ob.name:ratio=[.035,.018,.008][lod]
  elif 'recessed armor face' in ob.name:ratio=[.12,.06,.025][lod]
  elif 'sculpted perimeter' in ob.name:ratio=[.18,.10,.05][lod]
  else:ratio=[.105,.06,.035][lod]
  dec=tmp.modifiers.new('Game LOD reduction','DECIMATE');dec.ratio=ratio
  dep=bpy.context.evaluated_depsgraph_get();ev=tmp.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles()
  matcats=[category(m) if m else 'metal' for m in ob.data.materials]
  uv=me.uv_layers.get('GondolaSide')
  count=0
  # Duplicate right after simplifying, so geometry and vertex normals remain exactly symmetric.
  for mirror in ([1,-1] if ob.name=='Hybrid gondola RIGHT' else [1]):
   bi=names.index('GondolaRight' if mirror==1 else 'GondolaLeft') if ob.name.startswith('Hybrid gondola') else (2 if ob.name.startswith('Energy bridge') else 0)
   for tri in me.loop_triangles:
    inds=list(range(3)) if mirror==1 else [0,2,1]
    ps=[];ns=[];us=[]
    cat=matcats[me.polygons[tri.polygon_index].material_index]
    for j in inds:
     li=tri.loops[j];vi=tri.vertices[j]
     co=tmp.matrix_world@me.vertices[vi].co;co.x*=mirror
     no=tmp.matrix_world.to_3x3()@me.corner_normals[li].vector;no.x*=mirror;no.normalize()
     ps.append(CORR@co*SCALE);ns.append(CORR@no)
     if cat=='gondola' and uv:
      u,v=uv.data[li].uv;us.append(Vector((u,(1-v)*.5)))
     else:us.append(Vector(tiles[cat]))
    cross=(ps[1]-ps[0]).cross(ps[2]-ps[0])
    if cross.length<1e-7:continue
    d1=us[1]-us[0];d2=us[2]-us[0];det=d1.x*d2.y-d1.y*d2.x
    for p,n,u in zip(ps,ns,us):
     if n.length<.5:n=cross.normalized()
     if abs(det)>1e-12:
      tangent=((ps[1]-ps[0])*d2.y-(ps[2]-ps[0])*d1.y)/det
      tangent=tangent-n*tangent.dot(n)
      if tangent.length<1e-8:tangent=n.cross(Vector((0,1,0)))
      if tangent.length<1e-8:tangent=n.cross(Vector((1,0,0)))
      tangent.normalize()
      rawbit=((ps[2]-ps[0])*d1.x-(ps[1]-ps[0])*d2.x)/det
      bit=n.cross(tangent);bit*=1 if bit.dot(rawbit)>=0 else -1
     else:
      tangent=n.cross(Vector((0,1,0)))
      if tangent.length<1e-8:tangent=n.cross(Vector((1,0,0)))
      tangent.normalize();bit=n.cross(tangent)
     row=(*p,*n,*tangent,*bit,*u,*u,bi)
     # Constant palette UV has no meaningful tangent; sharing smooth vertices is safe.
     key=tuple(round(float(a),5) for a in row)
     if key not in lookup:lookup[key]=len(rows);rows.append(row)
     ids.append(lookup[key])
    count+=1
  stats.append({'name':ob.name,'triangles':count})
  ev.to_mesh_clear();bpy.data.objects.remove(tmp,do_unlink=True)
  if oi%100==0:print('LOD',lod,oi,'verts',len(rows),flush=True)
 print('LOD_DONE',lod,len(rows),len(ids)//3,flush=True)
 assert len(rows)<65536,('Vertex limit exceeded',lod,len(rows))
 path=UNIT/f'GGA0401_lod{lod}.scm'
 def section(f,tag):
  n=32-f.tell()%32
  if n<4:n+=32
  f.write(b'\xc5'*(n-4)+tag);return f.tell()
 with path.open('w+b') as f:
  f.write(bytes(48));section(f,b'NAME');offset=[]
  for name in names:offset.append(f.tell());f.write(name.encode()+b'\0')
  bo=section(f,b'SKEL')
  for i in range(len(names)):
   w=Matrix.Translation(world[i]);inv=w.inverted().transposed()
   p=Vector(world[i])-(Vector(world[parents[i]]) if parents[i]>=0 else Vector((0,0,0)))
   f.write(struct.pack('<16f3f4f4i',*[x for r in inv for x in r],*p,1,0,0,0,offset[i],parents[i],0,0))
  vo=section(f,b'VTXL')
  for row in rows:f.write(struct.pack('<16f4B',*row,0,0,0))
  io=section(f,b'TRIS');f.write(struct.pack('<'+'H'*len(ids),*ids))
  f.seek(0);f.write(struct.pack('<4s11I',b'MODL',5,bo,len(names),vo,0,len(rows),io,len(ids),0,0,len(names)))
 return {'vertices':len(rows),'triangles':len(ids)//3,'objects':stats}
report={'source':str(SOURCE),'scale':SCALE,'names':names,'parents':parents,'world_pivots':world,'lods':[make_lod(i) for i in range(3)]}
(OUT/'export_report.json').write_text(json.dumps(report,indent=2))
print('NATIVE_EXPORT_DONE',flush=True)
