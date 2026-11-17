import bpy
from collections import defaultdict
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=r'D:\Games\FafModsCreate\mods\uef-extra-unit\source-assets\UEL0211\4_rocket_launcher.glb')
o=next(o for o in bpy.context.scene.objects if o.type=='MESH'); m=o.data
p=list(range(len(m.vertices)))
def root(x):
 while p[x]!=x:
  p[x]=p[p[x]];x=p[x]
 return x
for e in m.edges:
 a,b=map(root,e.vertices);p[a]=b
comp=defaultdict(list)
for v in m.vertices: comp[root(v.index)].append(v.co)
for co in sorted(comp.values(),key=len,reverse=True)[:35]:
 print('COMP',len(co),'min',tuple(round(min(v[i] for v in co),3) for i in range(3)),'max',tuple(round(max(v[i] for v in co),3) for i in range(3)))
print('TOTAL COMPONENTS',len(comp))
