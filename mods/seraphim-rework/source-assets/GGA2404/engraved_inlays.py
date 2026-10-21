"""Flush projected inlays; concavity is supplied by the tangent-space normal map.
Executed in the model builder before the common gun lift and rig binding.
"""
from mathutils.bvhtree import BVHTree
import bmesh

# Earlier raised wires hid inverted faces on the foundation and mirrored ring.
# Flush inlays require the actual receiving skin to face outwards.
for ob in parts:
    if ob.get('foundation_petal') or ob.get('through_ring'):
        ob.data.calc_loop_triangles()
        volume=sum(ob.data.vertices[t.vertices[0]].co.dot(
            ob.data.vertices[t.vertices[1]].co.cross(ob.data.vertices[t.vertices[2]].co))/6
            for t in ob.data.loop_triangles)
        if volume<0:
            bm=bmesh.new();bm.from_mesh(ob.data)
            bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
            bm.to_mesh(ob.data);bm.free();ob.data.update()

receivers=[ob for ob in parts if ob.get('foundation_petal') or ob.get('main_gondola')
           or ob.get('through_ring') or ob.name.startswith(('Tri-lobed polished crown','Crown sculptural rib'))]
trees={ob:BVHTree.FromPolygons([v.co for v in ob.data.vertices],
       [list(p.vertices) for p in ob.data.polygons]) for ob in receivers}
count=0
for old in list(parts):
    if not old.get('decorative_pattern'):continue
    # Each original four-sided tube ring has four vertices about its centerline.
    centers=[sum((old.data.vertices[j+k].co for k in range(4)),Vector())/4
             for j in range(0,len(old.data.vertices),4)]
    if len(centers)<2:continue
    radius=sum((old.data.vertices[k].co-centers[0]).length for k in range(4))/4
    candidates=[ob for ob in receivers if ob['rig_bone']==old['rig_bone']]
    if not candidates:raise RuntimeError('No engraving receiver: '+old.name)
    if old.name.startswith(('Ring orbital','Ring paired','Outer ring')):
        candidates=[ob for ob in candidates if ob.get('through_ring')]
    elif old['rig_bone'] in ['GondolaL','GondolaR']:
        candidates=[ob for ob in candidates if ob.get('main_gondola')]
    receiver=min(candidates,key=lambda ob:sum(trees[ob].find_nearest(p)[3] for p in centers))
    tree=trees[receiver];vs=[];uv=[];closed=(centers[0]-centers[-1]).length<1e-5
    for j,center in enumerate(centers):
        point,normal,_,_=tree.find_nearest(center)
        before=centers[j-1] if j else centers[-2] if closed else centers[0]
        after=centers[j+1] if j+1<len(centers) else centers[1] if closed else centers[-1]
        tangent=(after-before).normalized();side=normal.cross(tangent).normalized()
        for sign in [-1,1]:
            edge,edge_normal,_,_=tree.find_nearest(point+side*radius*1.50*sign)
            vs.append(edge+edge_normal*.0015)
            uv.append((j/(len(centers)-1),(sign+1)/2))
    faces=[(2*j,2*j+2,2*j+3,2*j+1) for j in range(len(centers)-1)]
    name=old.name;bone=old['rig_bone'];parts.remove(old);bpy.data.objects.remove(old,do_unlink=True)
    ob=mesh(name+' / flush engraving',vs,faces,3,bone,True,uv)
    ob['decorative_pattern']=True;ob['engraved_inlay']=True
    ob['engraving_method']='flush surface ribbon + concave normal map'
    count+=1
print('ENGRAVED_INLAYS',count,flush=True)
