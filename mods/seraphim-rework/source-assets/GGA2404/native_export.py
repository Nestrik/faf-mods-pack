def pad(f,tag):
    n=32-f.tell()%32
    if n<4:n+=32
    f.write(b'\xc5'*(n-4)+tag)
    return f.tell()

CORR=Matrix(((1,0,0),(0,0,1),(0,-1,0))).to_4x4()
SCALE=20.0  # bp Display.UniformScale=.05 restores metre-like scene units.

def get_mesh_data(objects,decimate=False):
    verts=[];indices=[];lookup={}
    for ob in objects:
        tmp=ob.copy();tmp.data=ob.data.copy();scene.collection.objects.link(tmp)
        for m in list(tmp.modifiers):tmp.modifiers.remove(m)
        if decimate and len(tmp.data.polygons)>3 and not (ob.get('preserve_aperture') and ob.get('main_gondola')):
            m=tmp.modifiers.new('Distant mesh reduction','DECIMATE');m.ratio=.38
        tmp.modifiers.new('Native triangle topology','TRIANGULATE')
        dep=bpy.context.evaluated_depsgraph_get();evaluated=tmp.evaluated_get(dep);me=evaluated.to_mesh();me.calc_loop_triangles()
        if decimate:
            # Collapse interpolation can overshoot the small authored atlas tile.
            # Keep each material within its own padded tile before tangent generation.
            layer=me.uv_layers.active.data
            for polygon in me.polygons:
                mat=polygon.material_index
                tile=ob.data.materials[mat].get('atlas_tile',mat)
                xmin=(tile%4+20/256)/4;xmax=(tile%4+236/256)/4
                ymin=1-(tile//4+236/256)/2;ymax=1-(tile//4+20/256)/2
                for li in polygon.loop_indices:
                    u,v=layer[li].uv
                    layer[li].uv=(max(xmin,min(xmax,u)),max(ymin,min(ymax,v)))
        me.calc_tangents(uvmap=me.uv_layers.active.name)
        uvs=me.uv_layers.active.data
        bi=[b.name for b in rig.data.bones].index(ob['rig_bone'])
        for tri in me.loop_triangles:
            p=[CORR@me.vertices[k].co*SCALE for k in tri.vertices]
            uv=[Vector((uvs[li].uv.x,1-uvs[li].uv.y)) for li in tri.loops]
            dp1=p[1]-p[0];dp2=p[2]-p[0];du1=uv[1]-uv[0];du2=uv[2]-uv[0]
            det=du1.x*du2.y-du1.y*du2.x
            if abs(det)>1e-10:
                t=(dp1*du2.y-dp2*du1.y)/det;t.normalize()
                bt=(dp2*du1.x-dp1*du2.x)/det;bt.normalize()
            else:t=Vector((1,0,0));bt=Vector((0,0,1))
            for k,vi in enumerate(tri.vertices):
                t=CORR.to_3x3()@me.loops[tri.loops[k]].tangent
                bt=CORR.to_3x3()@me.loops[tri.loops[k]].bitangent
                norm=CORR.to_3x3()@(me.vertices[vi].normal if me.polygons[tri.polygon_index].use_smooth else tri.normal);norm.normalize()
                row=(*p[k],*norm,*t,*bt,*uv[k],*uv[k],bi,0,0,0)
                key=tuple(round(float(x),6) for x in row)
                if key not in lookup:lookup[key]=len(verts);verts.append(row)
                indices.append(lookup[key])
        evaluated.to_mesh_clear();bpy.data.objects.remove(tmp,do_unlink=True)
    return verts,indices

def write_scm(file,objects,decimate=False):
    vs,ix=get_mesh_data(objects,decimate);bs=list(rig.data.bones)
    assert len(vs)<65536,(len(vs),len(ix)//3)
    with open(file,'w+b') as f:
        f.write(b'\0'*48);pad(f,b'NAME');names=[]
        for b in bs:names.append(f.tell());f.write(b.name.encode()+b'\0')
        bo=pad(f,b'SKEL')
        for i,b in enumerate(bs):
            # Inverse bind pose, stored row-major transposed for the D3D matrix convention.
            world=CORR@b.matrix_local;world.translation*=SCALE
            inverse=world.inverted().transposed()
            parent=b.parent
            rel=(parent.matrix_local.inverted()@b.matrix_local) if parent else CORR@b.matrix_local
            pos=rel.to_translation()*SCALE;q=rel.to_quaternion().normalized()
            f.write(struct.pack('<16f3f4f4i',*[x for row in inverse for x in row],*pos,*q,names[i],bs.index(parent) if parent else -1,0,0))
        vo=pad(f,b'VRTX')
        for row in vs:f.write(struct.pack('<16f4B',*row))
        fo=pad(f,b'TRIS');f.write(struct.pack('<'+'H'*len(ix),*ix))
        f.seek(0);f.write(struct.pack('<4s11I',b'MODL',5,bo,len(bs),vo,0,len(vs),fo,len(ix),0,0,len(bs)))
    return {'vertices':len(vs),'triangles':len(ix)//3}
