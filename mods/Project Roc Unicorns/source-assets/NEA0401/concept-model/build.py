from pathlib import Path
import sys, math, json, copy, struct
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(1,str(HERE.parent))
from geometry import Mesh, load_scm, render_scm
from primitives import ellipsoid, ring, tube, curve
from supcom_binary import write_scm, write_sca, save_dds_dxt5

HATCH_RADIUS=5.95
HINGE_RADIUS=5.8

def build():
    m=Mesh(24); n=48; hz=-12; hr=HATCH_RADIUS
    # Restore the cambered streamlined shell with one open aft launch aperture.
    inner=[]; outer=[]
    for a in np.linspace(0,2*math.pi,n,endpoint=False):
        dx,dz=math.cos(a),math.sin(a)
        A=(dx/7.6)**2+(dz/26)**2; B=2*hz*dz/26**2; C=(hz/26)**2-1
        t=(-B+math.sqrt(B*B-4*A*C))/(2*A)
        inner.append((hr*dx,14,hz+hr*dz)); outer.append((t*dx,13.6,hz+t*dz))
    for i in range(n):
        j=(i+1)%n; a,b=inner[i],inner[j]; c,d=outer[j],outer[i]
        m.face([a,b,c,d],0,'armor',(0,1,0))
        m.face([d,c,(c[0],8,c[2]),(d[0],8,d[2])],0,'armor',(d[0],0,d[2]))
        m.face([(a[0],9,a[2]),(b[0],9,b[2]),b,a],0,'dark',(-a[0],0,hz-a[2]))
        m.face([(0,8,0),(d[0],8,d[2]),(c[0],8,c[2])],0,'dark',(0,-1,0))
    # Concentric rims and recessed bands leave the launch opening unobstructed.
    ring(m,0,14.12,hz,6.10,0,'edge',.17)
    ring(m,0,13.75,hz,5.85,0,'team',.11)
    ring(m,0,12.3,hz,5.85,0,'edge',.11)
    ring(m,0,10.5,hz,5.85,0,'team',.10)
    # Layered armor outlines and luminous keel inlays.
    for s in (-1,1):
        tube(m,[(0,14.0,24),(s*2.7,14.05,19),(s*4.8,14.04,9),(s*5.7,14.04,0),(s*5.3,14.04,-8)],.10,0,'edge',6)
        tube(m,[(0,14.10,21),(s*1.8,14.1,14),(s*2.8,14.1,7),(s*3.5,14.1,1)],.12,0,'team',6)
        # Long nested, tapered Aeon filigree, following the top deck.
        for points, width, mat in [
            ([(0,23),(s*1.0,21),(s*2.9,16),(s*4.2,9),(s*4.7,3),(s*4.1,-2)],.085,'edge'),
            ([(0,20),(s*.8,18),(s*2.0,14),(s*2.8,9),(s*3.1,5),(s*2.8,2)],.10,'team'),
            ([(s*5.8,10),(s*6.3,6),(s*6.6,1),(s*6.3,-4),(s*5.7,-8)],.09,'edge')]:
            pts=curve([(x,14.17,z) for x,z in points],3)
            tube(m,pts,width,0,mat,5)
    # The middle pair sits slightly farther out to follow the hull's outline.
    pods=[(s*(14.3 if z==0 else 13),z) for s in (-1,1) for z in (-14,0,14)]
    for x,z in pods:
        ellipsoid(m,(x,6,z),(5.8,5.0,5.8),0,'dark')
        ellipsoid(m,(x,6.8,z),(5.75,4.6,5.75),0,'armor')
        ring(m,x,6.55,z,5.72,0,'team',.14)
        ring(m,x,7.0,z,5.72,0,'edge',.12)
        ring(m,x,10.55,z,2.65,0,'edge',.09)
        ellipsoid(m,(x,11.15,z),(1.0,.22,1.0),0,'lens')
        # Gold sweeping petals wrap the curved upper shell. A diamond frames
        # the luminous crown; each path conforms to the ellipsoid surface.
        def dome(u,v):
            r2=(u/5.75)**2+(v/5.75)**2
            return (x+u,6.8+4.6*math.sqrt(max(0,1-r2))+.10,z+v)
        diamond=[(0,1.35),(.9,0),(0,-1.35),(-.9,0),(0,1.35)]
        tube(m,[dome(u,v) for u,v in diamond],.10,0,'edge',6)
        for side in (-1,1):
            # Mirrored leaf-shaped curves converge at the front and back.
            for path in [ [(0,1.1),(side*1.7,2.0),(side*3.7,2.5),(side*5.0,1.6),(side*5.45,0)],
                          [(0,-1.1),(side*1.7,-2.0),(side*3.7,-2.5),(side*5.0,-1.6),(side*5.45,0)] ]:
                points=curve([(u,0,v) for u,v in path],3)
                tube(m,[dome(p[0],p[2]) for p in points],.09,0,'edge',5)
    # Concentric projector rings under the floating crystal.
    ring(m,0,14.30,3,3.8,0,'edge',.18)
    ring(m,0,14.35,3,2.8,0,'team',.10)
    ring(m,0,14.43,3,2.15,0,'lens',.10)
    # Floating double-pointed crystal and four independent tilted rings.
    eq=[(2.65*math.cos(a),24,3+2.65*math.sin(a)) for a in np.linspace(0,2*math.pi,8,endpoint=False)]
    for i in range(8):
        a,b=eq[i],eq[(i+1)%8]; out=(a[0]+b[0],1,a[2]+b[2]-6)
        m.face([(0,30,3),a,b],1,'crystal',out)
        m.face([(0,19,3),b,a],1,'crystal',(out[0],-1,out[2]))
    # Faceted, luminous seams and a pale inner shaft evoke the concept's
    # crystal while retaining an opaque, engine-friendly material setup.
    for i in range(8):
        a=2*math.pi*i/8
        ridge=(2.68*math.cos(a),24,3+2.68*math.sin(a))
        tube(m,[(0,30.02,3),ridge,(0,18.98,3)],.045,1,'lens',5)
    tube(m,[(0,19.0,3),(0,30.0,3)],.10,1,'lens',6)
    for idx,(y,rad,tilt) in enumerate([(20,4.62,.151),(23,5.50,-.120),(26.5,5.06,.232),(30.5,4.07,.070)]):
        pts=[(rad*math.cos(a),y+tilt*rad*math.cos(a),3+rad*math.sin(a)) for a in np.linspace(0,2*math.pi,33)]
        tube(m,pts,.10,8+idx,'edge',5)
        ellipsoid(m,(rad,y+tilt*rad,3),(.28,.22,.28),8+idx,'lens')
    m.smooth()
    lookup={}; verts=[]; inds=[]
    for i in m.indices:
        v=m.vertices[i]; key=tuple(round(float(x),6) for x in v)
        if key not in lookup: lookup[key]=len(verts); verts.append(v)
        inds.append(lookup[key])
    m.vertices,m.indices=verts,inds
    return m

def main():
    m=build(); assert len(m.vertices)<65536
    hz=-12
    pal=[(240,235,220),(46,75,70),(205,161,75),(170,174,155),(35,198,149),(8,155,110),(45,235,177),(9,62,57)]
    al=np.zeros((256,512,4),np.uint8); sp=np.zeros_like(al); no=np.full_like(al,128)
    for i,c in enumerate(pal):
        y=i//4*128;x=i%4*128; al[y:y+128,x:x+128,:]=[*c,255]; sp[y:y+128,x:x+128,:]=[120,120,200 if i in (4,5,6) else 0,255 if i in (2,4) else 0]
    for suffix,data in [('albedo',al),('specteam',sp),('normalsTS',no)]:
        im=Image.fromarray(data); im.save(HERE/f'NEA0401_{suffix}_source.png'); save_dds_dxt5(im,HERE/f'NEA0401_{suffix}.dds',independent_channels=True)
    scm=HERE/'NEA0401_concept_lod0.scm'
    bone_names=['NEA0401','Crystal']+[f'Hatch{i+1}' for i in range(6)]+[f'Ring{i+1}' for i in range(4)]+['Launch']
    bone_parents=[-1]+[0]*12
    hinges=[(HINGE_RADIUS*math.cos((k+.5)*math.pi/3),14.25,hz+HINGE_RADIUS*math.sin((k+.5)*math.pi/3)) for k in range(6)]
    bone_pivots=[(0,0,0),(0,24,3)]+hinges+[(0,y,3) for y in (20,23,26.5,30.5)]+[(0,14.25,hz)]
    write_scm(m,scm,bone_names,bone_parents,bone_pivots)
    ring_frames=[]
    for frame in range(121):
        t=frame/120
        poses=[((0,0,0),(1,0,0,0))]
        for k in range(4):
            angle=2*math.pi*t*(1 if k%2==0 else -1)
            poses.append((bone_pivots[8+k],(math.cos(angle/2),0,math.sin(angle/2),0)))
        ring_frames.append(poses)
    write_sca(HERE/'NEA0401_rings_idle.sca',[bone_names[0]]+bone_names[8:12],[-1]+[0]*4,ring_frames,8.0)
    rh=struct.unpack_from('<4siifiiiii',(HERE/'NEA0401_rings_idle.sca').read_bytes())
    assert rh[0]==b'ANIM' and rh[2]==121 and rh[4]==5 and rh[8]==148
    v,f=load_scm(scm); assert np.isfinite(v).all() and f.max()<len(v)
    lines=['# NEA0401 concept, Y up, +Z forward','mtllib NEA0401_concept.mtl']
    for p in m.vertices: lines.append('v %.6f %.6f %.6f'%p[:3])
    for p in m.vertices: lines.append('vt %.7f %.7f'%(p[12],1-p[13]))
    for p in m.vertices: lines.append('vn %.6f %.6f %.6f'%p[3:6])
    names=['armor','dark','edge','steel','team','crystal','lens','joint']
    last=None; lastmat=None
    for i in range(0,len(m.indices),3):
        b=int(m.vertices[m.indices[i]][16])
        if b!=last: lines.append('g '+('Hull' if b==0 else bone_names[b])); last=b
        mat=m.materials[i//3]
        if mat!=lastmat: lines.append('usemtl '+mat); lastmat=mat
        lines.append('f '+' '.join(f'{j+1}/{j+1}/{j+1}' for j in m.indices[i:i+3]))
    (HERE/'NEA0401_concept.obj').write_text('\n'.join(lines)+'\n')
    materials=[]
    for name,c in zip(names,pal):
        rgb=tuple(v/255 for v in c)
        materials.extend([f'newmtl {name}','Kd %.4f %.4f %.4f'%rgb,
                          'Ks '+('0.8 0.7 0.4' if name=='edge' else '0.35 0.35 0.35'),
                          'Ns '+('110' if name=='edge' else '60')])
        if name in ('crystal','lens','team'): materials.append('Ke %.4f %.4f %.4f'%tuple(v*.35 for v in rgb))
        if name=='crystal': materials.extend(['d 0.58','Ni 1.35','illum 4'])
        materials.append('')
    (HERE/'NEA0401_concept.mtl').write_text('\n'.join(materials)+'\n')
    print(json.dumps({'vertices':len(v),'triangles':len(f)},indent=2),flush=True)
    # The preview renderer reads team color from albedo alpha; Aeon stores it
    # in SpecTeam alpha. Substitute that channel for preview only.
    import geometry
    original=geometry.load_dds_mip
    def loader(path,level=0):
        im=original(path,level)
        if 'albedo' in Path(path).name:
            data=np.asarray(im).copy()
            spec=original(Path(path).with_name(Path(path).name.replace('albedo','specteam')),level)
            data[:,:,3]=np.asarray(spec)[:,:,3]
            return Image.fromarray(data)
        return im
    geometry.load_dds_mip=loader
    ims=[]
    for name,az,el in [('perspective',35,40),('top',180,88),('front',0,12),('side',90,12)]:
        path=HERE/f'NEA0401_{name}.png'; render_scm(scm,HERE,path,azimuth=az,elevation=el,size=600,texture_mip=1); ims.append(Image.open(path))
    sheet=Image.new('RGB',(1200,1200))
    for i,im in enumerate(ims): sheet.paste(im,((i%2)*600,(i//2)*600))
    sheet.save(HERE/'NEA0401_views.png')
    # Render the rotating-ring clip against the exported model.
    previews=[]; temp=HERE/'_hatch_preview.scm'
    for frame in range(0,120,15):
        posed=copy.copy(m); posed.vertices=[]
        for vertex in m.vertices:
            b=int(vertex[16]); pos=list(vertex)
            if b>=8:
                pivot,quat=ring_frames[frame][b-7]
                w,x,y,z=quat; axis=np.array([x,y,z]); point=np.array(pos[:3])-pivot
                pos[:3]=point+2*w*np.cross(axis,point)+2*np.cross(axis,np.cross(axis,point))+np.array(pivot)
                for start in (3,6,9):
                    vec=np.array(pos[start:start+3])
                    pos[start:start+3]=vec+2*w*np.cross(axis,vec)+2*np.cross(axis,np.cross(axis,vec))
            posed.vertices.append(tuple(pos))
        write_scm(posed,temp,bone_names,bone_parents,bone_pivots)
        img=render_scm(temp,HERE,HERE/'_hatch_frame.png',azimuth=35,elevation=35,size=420,texture_mip=1)
        previews.append(img.convert('P',palette=Image.Palette.ADAPTIVE))
    previews[0].save(HERE/'NEA0401_rings_idle.gif',save_all=True,append_images=previews[1:],duration=1000,loop=0,disposal=2)
    temp.unlink(); (HERE/'_hatch_frame.png').unlink()
if __name__=='__main__': main()
