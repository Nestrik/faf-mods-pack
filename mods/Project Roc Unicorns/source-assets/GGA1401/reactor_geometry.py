"""Mesh primitives, aged Seraphim metal/crop-circle inlays and SCM previews.

Y is up; +Z is the weapon's forward direction. All dimensions are source units.
This module builds real mesh geometry; preview images are renders of the SCM.
"""
from __future__ import annotations

import math
import struct
from io import BytesIO
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


MATERIALS = ("armor", "dark", "edge", "steel", "team", "crystal", "lens", "joint")


def normalized(v):
    v = np.asarray(v, dtype=float)
    return v / max(1e-12, np.linalg.norm(v))


def atlas_uv(material, uv):
    tile = MATERIALS.index(material)
    # Generous gutters keep adjacent materials out of the first mip levels.
    return ((tile % 4 + .09 + .82 * uv[0]) / 4,
            (tile // 4 + .045 + .91 * uv[1]) / 2)


class Mesh:
    def __init__(self, detail):
        self.detail = detail
        self.vertices = []
        self.indices = []
        self.materials = []

    def face(self, points, bone=0, material="armor", outward=None, uvs=None):
        points = [np.asarray(p, dtype=float) for p in points]
        if uvs is None:
            uvs = [(0, 0), (1, 0), (1, 1), (0, 1)][:len(points)]
            if len(points) > 4:
                uvs = [(.5+.45*math.cos(i*2*math.pi/len(points)),
                        .5+.45*math.sin(i*2*math.pi/len(points))) for i in range(len(points))]
        n = np.cross(points[1]-points[0], points[2]-points[0])
        if outward is not None and np.dot(n, outward) < 0:
            points.reverse()
            uvs = list(reversed(uvs))
        for i in range(1, len(points)-1):
            ps = [points[j] for j in (0, i, i+1)]
            ts = [np.asarray(atlas_uv(material, uvs[j])) for j in (0, i, i+1)]
            normal = normalized(np.cross(ps[1]-ps[0], ps[2]-ps[0]))
            if np.linalg.norm(normal) < .5:
                continue
            e1, e2 = ps[1]-ps[0], ps[2]-ps[0]
            d1, d2 = ts[1]-ts[0], ts[2]-ts[0]
            det = d1[0]*d2[1]-d2[0]*d1[1]
            if abs(det) > 1e-10:
                tangent = normalized((e1*d2[1]-e2*d1[1])/det)
                bitangent = normalized((e2*d1[0]-e1*d2[0])/det)
            else:
                tangent = normalized(np.cross(normal, (0, 1, .01)))
                bitangent = normalized(np.cross(normal, tangent))
            for p, uv in zip(ps, ts):
                self.vertices.append(tuple(p)+tuple(normal)+tuple(tangent)+tuple(bitangent)+tuple(uv)+tuple(uv)+(bone,))
                self.indices.append(len(self.vertices)-1)
            self.materials.append(material)

    def loft(self, rings, centers, bone=0, material="dark", sides=None, loop=False):
        count = len(rings[0])
        length = len(rings) if loop else len(rings)-1
        for i in range(length):
            k = (i+1) % len(rings)
            center = (np.asarray(centers[i])+centers[k])/2
            for j in range(count):
                jj = (j+1) % count
                points = [rings[i][j], rings[k][j], rings[k][jj], rings[i][jj]]
                outward = np.mean(points, axis=0)-center
                finish=sides[j] if sides else material
                u0,u1=j/count,(j+1)/count
                self.face(points, bone, finish, outward,
                          [(u0,i/length),(u0,(i+1)/length),
                           (u1,(i+1)/length),(u1,i/length)])
        if not loop:
            self.face(rings[0], bone, material, np.asarray(centers[0])-centers[1])
            self.face(rings[-1], bone, material, np.asarray(centers[-1])-centers[-2])

    def column(self, profile, bone=0, material="dark", sides=None):
        sides = sides or self.detail
        rings = [[(r*math.cos(i*2*math.pi/sides), y, r*math.sin(i*2*math.pi/sides))
                  for i in range(sides)] for r, y in profile]
        self.loft(rings, [(0, y, 0) for _, y in profile], bone, material)

    def annulus(self, inner, outer, y0, y1, bone=0, material="edge"):
        b = min(.15, (outer-inner)/4, (y1-y0)/4)
        profile = [(inner+b,y0),(outer-b,y0),(outer,y0+b),(outer,y1-b),
                   (outer-b,y1),(inner+b,y1),(inner,y1-b),(inner,y0+b)]
        rings, centers = [], []
        for i in range(self.detail):
            a = i*2*math.pi/self.detail
            rings.append([(r*math.cos(a),y,r*math.sin(a)) for r,y in profile])
            centers.append(((inner+outer)/2*math.cos(a),(y0+y1)/2,(inner+outer)/2*math.sin(a)))
        self.loft(rings, centers, bone, material, loop=True)

    def nozzle(self, profile, bone=2, material="edge", y=22):
        rings = [[(r*math.cos(i*2*math.pi/self.detail),y+r*math.sin(i*2*math.pi/self.detail),z)
                  for i in range(self.detail)] for r,z in profile]
        self.loft(rings, [(0,y,z) for _,z in profile], bone, material)

    def blade(self, sections, angle, bone, material="edge", panels=True, depth=1.0):
        radial = np.array((math.cos(angle),0,math.sin(angle)))
        tangent = np.array((-math.sin(angle),0,math.cos(angle)))
        rings, centers = [], []
        for y, radius, width in sections:
            local_depth=min(depth,max(.07,width*.95)) if panels else depth
            bevel = min(.22, width*.32, local_depth*.4)
            cross = [(-width+bevel,-local_depth),(width-bevel,-local_depth),(width,-local_depth+bevel),
                     (width,local_depth-bevel),(width-bevel,local_depth),(-width+bevel,local_depth),
                     (-width,local_depth-bevel),(-width,-local_depth+bevel)]
            center = radial*radius+np.array((0,y,0))
            rings.append([tuple(center+radial*x+tangent*z) for x,z in cross])
            centers.append(center)
        finishes = ["armor","edge",material,"edge","armor","edge",material,"edge"] if panels else None
        self.loft(rings, centers, bone, material, finishes)

    def foot(self, sections, angle, material):
        radial = np.array((math.cos(angle),0,math.sin(angle)))
        tangent = np.array((-math.sin(angle),0,math.cos(angle)))
        rings, centers = [], []
        for radius, y, width, depth in sections:
            bevel = min(.3, depth*.4, width*.2)
            cross = [(-width+bevel,-depth),(width-bevel,-depth),(width,-depth+bevel),
                     (width,depth-bevel),(width-bevel,depth),(-width+bevel,depth),
                     (-width,depth-bevel),(-width,-depth+bevel)]
            center = radial*radius+np.array((0,y,0))
            rings.append([tuple(center+tangent*x+np.array((0,z,0))) for x,z in cross])
            centers.append(center)
        self.loft(rings, centers, 0, material)

    def smooth(self):
        groups = defaultdict(list)
        for i,v in enumerate(self.vertices):
            groups[(tuple(round(x,5) for x in v[:3]),v[16],self.materials[i//3])].append(i)
        original = self.vertices[:]
        for indices in groups.values():
            for i in indices:
                v = original[i]
                # The rebuilt surfaces have geometric rolled edges already.
                # One normal at every shared position prevents a highlight seam
                # where the old angle cutoff gave neighboring triangles different normals.
                normal = normalized(np.sum([original[j][3:6] for j in indices],axis=0))
                tangent = normalized(np.array(v[6:9])-normal*np.dot(v[6:9],normal))
                handedness = 1 if np.dot(np.cross(normal,tangent),v[9:12])>=0 else -1
                bitangent = np.cross(normal,tangent)*handedness
                self.vertices[i] = v[:3]+tuple(normal)+tuple(tangent)+tuple(bitangent)+v[12:]


def seraphim_inlays(u, v):
    """Linked concentric circles, orbital satellites and thin geometric pathways."""
    distance = np.full_like(u, 10.0)
    # UV ellipses compensate for the long armor panels to read as physical circles.
    for cx,cy,radii in ((.5,.29,(.25,.20,.115)),(.5,.69,(.17,.12)),
                       (.21,.51,(.075,.045)),(.79,.51,(.075,.045)),(.5,.9,(.055,))):
        metric=np.sqrt((u-cx)**2+((v-cy)*1.75)**2)
        for radius in radii:
            distance=np.minimum(distance,abs(metric-radius))
    def segment(ax,ay,bx,by):
        dx,dy=bx-ax,(by-ay)*1.75
        t=np.clip(((u-ax)*dx+(v-ay)*1.75*dy)/(dx*dx+dy*dy),0,1)
        return np.sqrt((u-ax-t*dx)**2+((v-ay)*1.75-t*dy)**2)
    # Connected motifs, with broad uncolored metal fields between narrow strokes.
    for points in ((.5,.43,.5,.59),(.5,.79,.5,.87),(.27,.51,.41,.40),
                   (.73,.51,.59,.40),(.27,.51,.41,.64),(.73,.51,.59,.64)):
        distance=np.minimum(distance,segment(*points))
    for side in (-1,1):
        sweep=.5+side*(.35-.045*np.sin(v*7))
        distance=np.minimum(distance,abs(u-sweep))
        distance=np.minimum(distance,abs(u-sweep-side*.033))
    lines=np.clip((.009-distance)/.004,0,1)
    engraving=np.clip((.017-distance)/.006,0,1)
    fade=np.clip((v-.07)/.025,0,1)*np.clip((.94-v)/.025,0,1)
    return lines*fade,engraving*fade


def make_textures(asset_dir, unit_dir, save_dds):
    size=1024
    albedo=np.zeros((size,size,4),dtype=np.uint8)
    specteam=np.zeros_like(albedo)
    normals=np.zeros_like(albedo)
    # Native ComputeNormal reads .ga, transformed by (binormal,tangent,normal).
    # A flat DXT5nm map has G=A=128, not an opaque RGB normal with alpha=255.
    normals[:]=(128,128,128,128)
    # Stock Seraphim uses restrained albedo plus strong reflected metal and gloss.
    palettes=((91,102,111),(49,58,65),(135,147,155),(80,92,101),
              (125,155,145),(76,113,106),(58,104,91),(21,29,32))
    finishes={"armor":(245,212),"dark":(205,180),"edge":(255,235),
              "steel":(235,208),"joint":(155,155)}
    w,h=size//4,size//2
    u,v=np.meshgrid(np.linspace(0,1,w),np.linspace(0,1,h))
    brush=.8*np.sin(v*h*.83)+.4*np.sin(u*w*.53+v*h*.16)
    weather=(np.sin(13*u+7*v)*np.sin(21*v-9*u)+.35*np.sin(51*u+37*v))
    patina=np.clip(weather-.1,0,1)
    sheen=1.2*np.sin(math.pi*u)+.8*np.cos(v*math.pi*2)
    lines,engraving=seraphim_inlays(u,v)
    for tile,name in enumerate(MATERIALS):
        ox,oy=(tile%4)*w,(tile//4)*h
        region=np.s_[oy:oy+h,ox:ox+w]
        value=np.array(palettes[tile],dtype=float)+brush[:,:,None]+sheen[:,:,None]+weather[:,:,None]*3
        value-=patina[:,:,None]*np.array((5,3,1))
        packed=np.zeros((h,w,4),dtype=float)
        reflect,specular=finishes.get(name,(148,168))
        packed[:,:,0]=reflect-patina*10; packed[:,:,1]=specular-patina*12
        if name in ("armor","steel"):
            # Bright narrow crop-circle channels cut into aged, uncolored armor.
            packed[:,:,3]=255*lines
            value=value*(1-.24*engraving[:,:,None])*(1-lines[:,:,None])+np.array((139,165,150))*lines[:,:,None]
            packed[:,:,2]=lines*18
            packed[:,:,0]-=engraving*13
            packed[:,:,1]-=engraving*8
            gy,gx=np.gradient(-engraving+weather*.03)
            nx,ny=-gx*.48,-gy*.48
            normals[region][:,:,1]=np.clip((ny*.5+.5)*255,0,255).astype(np.uint8)
            normals[region][:,:,3]=np.clip((nx*.5+.5)*255,0,255).astype(np.uint8)
        elif name in ("team","crystal","lens"):
            packed[:,:,3]=255
            packed[:,:,2]={"team":72,"crystal":78,"lens":160}[name]
            if name=="crystal":
                shard=12*np.sin(22*u+9*v)+8*np.sin(43*u-27*v)
                value+=(shard+20*np.maximum(0,1-abs(u-.5-v*.15)*4))[:,:,None]
                packed[:,:,0]=115; packed[:,:,1]=190
            elif name=="lens":
                value+=(25*np.sin(u*math.pi)*np.sin(v*math.pi))[:,:,None]
        # 2026-10-22: darker hull, retaining gloss and player-color inlays.
        value *= .76
        packed[:,:,0] *= .88
        packed[:,:,2] *= .85
        albedo[region][:,:,:3]=np.clip(value,0,255).astype(np.uint8)
        # Preserve the former SpecTeam-alpha line mask exactly, but put it in
        # Albedo.A as required by the stock Seraphim shader.
        albedo[region][:,:,3]=np.clip(packed[:,:,3],0,255).astype(np.uint8)
        packed[:,:,3]=0
        specteam[region]=np.clip(packed,0,255).astype(np.uint8)
    for suffix,data in (("albedo",albedo),("specteam",specteam),("normalsTS",normals)):
        im=Image.fromarray(data)
        save_dds(im,unit_dir/f"GGA1401_{suffix}.dds",independent_channels=True)
        im.save(asset_dir/f"GGA1401_{suffix}_source.png")
    Image.fromarray(albedo[:,:,3]).save(asset_dir/"GGA1401_team_mask_preview.png")
    Image.fromarray(albedo).save(asset_dir/"GGA1401_albedo_preview.png")


def quaternion_matrix(q):
    w,x,y,z=q
    return np.array(((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
                     (2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),
                     (2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y))))


def load_sca_pose(path, seconds):
    """Read a pose from the exported SCA, interpolating neighboring keyframes."""
    raw=Path(path).read_bytes()
    h=struct.unpack_from('<4siifiiiii',raw)
    names=raw[h[5]:].split(b'\0',h[4])[:h[4]]
    at=(seconds%h[3])/h[3]*(h[2]-1)
    i=int(at); blend=at-i
    pose={}
    for bone,name in enumerate(names):
        offset=h[7]+28+8+bone*28
        a=np.array(struct.unpack_from('<3f4f',raw,offset+i*h[8]))
        b=np.array(struct.unpack_from('<3f4f',raw,offset+min(i+1,h[2]-1)*h[8]))
        if np.dot(a[3:],b[3:])<0:b[3:]*=-1
        p=a*(1-blend)+b*blend
        p[3:]/=np.linalg.norm(p[3:])
        pose[name.decode('ascii')]=(p[:3],p[3:])
    return pose


def load_scm(path, pose=None):
    data=Path(path).read_bytes()
    h=struct.unpack_from("<4s11I",data)
    vertices=np.array([struct.unpack_from("<16f4B",data,h[4]+i*68)[:17] for i in range(h[6])])
    faces=np.frombuffer(data,dtype="<u2",count=h[8],offset=h[7]).reshape(-1,3).copy()
    if pose:
        bind_world=[]; world_positions=[]; world_rotations=[]
        for i in range(h[3]):
            bone=struct.unpack_from('<16f3f4f4i',data,h[2]+i*108)
            name=data[bone[23]:].split(b'\0')[0].decode('ascii')
            parent=bone[24]
            bind=np.array(bone[16:19])
            position,quaternion=pose.get(name,(bind,np.array(bone[19:23])))
            rotation=quaternion_matrix(quaternion)
            bind_world.append(bind+(bind_world[parent] if parent>=0 else 0))
            if parent>=0:
                position=world_positions[parent]+world_rotations[parent]@position
                rotation=world_rotations[parent]@rotation
            world_positions.append(position); world_rotations.append(rotation)
            mask=vertices[:,16]==i
            vertices[mask,:3]=(vertices[mask,:3]-bind_world[i])@rotation.T+position
            for start in (3,6,9):vertices[mask,start:start+3]=vertices[mask,start:start+3]@rotation.T
    return vertices,faces


def load_dds_mip(path,level=0):
    """Decode a real exported BC3 mip, including RGB under zero material alpha."""
    raw=Path(path).read_bytes()
    if raw[:4]!=b'DDS ' or raw[84:88]!=b'DXT5':
        raise ValueError('Expected a BC3/DXT5 DDS')
    h,w=struct.unpack_from('<II',raw,12)
    levels=max(1,struct.unpack_from('<I',raw,28)[0])
    if not 0<=level<levels:
        raise ValueError('DDS mip level outside its chain')
    offset=128
    for _ in range(level):
        offset+=((w+3)//4)*((h+3)//4)*16
        w,h=max(1,w//2),max(1,h//2)
    count=((w+3)//4)*((h+3)//4)*16
    if offset+count>len(raw):
        raise ValueError('Truncated DDS mip')
    header=bytearray(raw[:128])
    struct.pack_into('<II',header,12,h,w)
    struct.pack_into('<I',header,20,count)
    struct.pack_into('<I',header,28,1)
    return Image.open(BytesIO(bytes(header)+raw[offset:offset+count])).convert('RGBA')


def export_obj(mesh, asset_dir, bones):
    # Full editable geometry and named bone groups for DCC import.
    out=["# GGA1401, Y up, +Z forward; source units (game scale 0.1)","mtllib GGA1401_source.mtl"]
    for v in mesh.vertices:
        out.append("v %.6f %.6f %.6f"%v[:3])
    for v in mesh.vertices:
        out.append("vt %.7f %.7f"%(v[12],1-v[13]))
    for v in mesh.vertices:
        out.append("vn %.6f %.6f %.6f"%v[3:6])
    last=None
    for i in range(0,len(mesh.indices),3):
        bone=int(mesh.vertices[mesh.indices[i]][16])
        if bone!=last:
            out.extend(("g "+bones[bone],"usemtl reactor_atlas"))
            last=bone
        out.append("f "+" ".join(f"{j+1}/{j+1}/{j+1}" for j in mesh.indices[i:i+3]))
    (asset_dir/"GGA1401_source.obj").write_text("\n".join(out)+"\n",encoding="utf-8")
    (asset_dir/"GGA1401_source.mtl").write_text("newmtl reactor_atlas\nKd 1 1 1\nKs 0.6 0.6 0.6\nNs 50\nmap_Kd GGA1401_albedo_source.png\n",encoding="utf-8")


def sample_map(texture,uv):
    """Bilinear sampling keeps fine incised lines smooth in the preview."""
    h,w=texture.shape[:2]
    x=np.clip(uv[:,0]*w-.5,0,w-1); y=np.clip(uv[:,1]*h-.5,0,h-1)
    x0=np.floor(x).astype(int); y0=np.floor(y).astype(int)
    x1=np.minimum(x0+1,w-1); y1=np.minimum(y0+1,h-1)
    fx=(x-x0)[:,None]; fy=(y-y0)[:,None]
    return ((texture[y0,x0]*(1-fx)+texture[y0,x1]*fx)*(1-fy)
            +(texture[y1,x0]*(1-fx)+texture[y1,x1]*fx)*fy)


def render_scm(scm, asset_dir, output, azimuth=35, elevation=19, player=(.12,.24,1.0), size=960, bones=None, texture_mip=0, transparent=False, ground_tarmac=None, pose=None, fixed_bounds=None):
    target_size=size
    size=math.ceil(size*1.5)
    vertices,faces=load_scm(scm,pose)
    if bones is not None:
        faces=faces[np.all(np.isin(vertices[faces,16],bones),axis=1)]
        used,inverse=np.unique(faces,return_inverse=True)
        vertices=vertices[used]
        faces=inverse.reshape(-1,3)
    positions=vertices[:,:3]
    a,e=math.radians(azimuth),math.radians(elevation)
    view=normalized((math.sin(a)*math.cos(e),math.sin(e),math.cos(a)*math.cos(e)))
    right=normalized(np.cross((0,1,0),view)); up=np.cross(view,right)
    projected=np.stack((positions@right,-positions@up),axis=1)
    framing=projected
    if fixed_bounds is not None:
        framing=np.stack((fixed_bounds@right,-fixed_bounds@up),axis=1)
    if ground_tarmac is not None:
        gy,gx=np.where(np.asarray(ground_tarmac)[:,:,3]>24)
        stride=max(1,len(gx)//3000)
        ground_points=np.column_stack(((gx[::stride]/ground_tarmac.width-.5)*128,
                                       np.zeros_like(gx[::stride]),
                                       (gy[::stride]/ground_tarmac.height-.5)*128))
        framing=np.vstack((projected,np.stack((ground_points@right,-ground_points@up),axis=1)))
    center=(framing.min(axis=0)+framing.max(axis=0))/2
    span=np.ptp(framing,axis=0)
    scale=min(size*.82/span[0],size*.88/span[1])
    projected=(projected-center)*scale+(size/2,size*.49)
    depth=positions@view
    yy,xx=np.mgrid[:size,:size]
    bg=.085+.045*(1-yy/size)
    canvas=np.stack((bg*.91,bg*.97,bg*1.06),axis=-1)
    if ground_tarmac is not None:
        # Orthographic projection of the actual stock ground decal. Read only
        # from the user's env.scd for this preview, never redistributed as DDS.
        screen=np.stack(((xx-size/2)/scale+center[0],
                         (yy-size*.49)/scale+center[1]),axis=-1)
        plane=np.array(((right[0],right[2]),(-up[0],-up[2])))
        world=screen@np.linalg.inv(plane).T
        uv=world/128+.5
        inside=np.all((uv>=0)&(uv<=1),axis=-1)
        sample=sample_map(np.asarray(ground_tarmac)/255,uv.reshape(-1,2)).reshape(size,size,4)
        noise=(np.sin(world[:,:,0]*1.2)*np.sin(world[:,:,1]*1.7))*.012
        canvas[:]=np.array((.19,.205,.17))+noise[:,:,None]
        opacity=sample[:,:,3:4]*inside[:,:,None]
        canvas=canvas*(1-opacity)+(sample[:,:,:3]*.65+.045)*opacity
    # Contact shadow is a preview aid, never baked into the game's textures.
    ground_y=size*.49-center[1]*scale
    shadow=np.exp(-((xx-size*.5)/(size*.31))**2-((yy-ground_y)/(size*.07))**2)*.42
    canvas*=1-shadow[:,:,None]
    zbuffer=np.full((size,size),-np.inf)
    # Inspect the shipped data, rather than PNGs that cannot expose mip/export bugs.
    unit_dir=Path(scm).parent
    albedo=np.asarray(load_dds_mip(unit_dir/'GGA1401_albedo.dds',texture_mip))/255
    spec=np.asarray(load_dds_mip(unit_dir/'GGA1401_specteam.dds',texture_mip))/255
    normal_map=np.asarray(load_dds_mip(unit_dir/'GGA1401_normalsTS.dds',texture_mip))/127.5-1
    sun=normalized((-.45,.75,.65)); half=normalized(sun+view)
    for face in faces:
        geometric=np.cross(positions[face[1]]-positions[face[0]],positions[face[2]]-positions[face[0]])
        if np.dot(geometric,view)<=0: continue
        p=projected[face]
        lo=np.maximum(np.floor(p.min(axis=0)).astype(int),0)
        hi=np.minimum(np.ceil(p.max(axis=0)).astype(int),size-1)
        if np.any(lo>hi): continue
        x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
        denom=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
        if abs(denom)<1e-8: continue
        w0=((p[1,1]-p[2,1])*(x-p[2,0])+(p[2,0]-p[1,0])*(y-p[2,1]))/denom
        w1=((p[2,1]-p[0,1])*(x-p[2,0])+(p[0,0]-p[2,0])*(y-p[2,1]))/denom
        w2=1-w0-w1
        z=w0*depth[face[0]]+w1*depth[face[1]]+w2*depth[face[2]]
        target=zbuffer[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        mask=(w0>=0)&(w1>=0)&(w2>=0)&(z>target)
        if not mask.any(): continue
        weights=np.stack((w0[mask],w1[mask],w2[mask]),axis=1)
        normal=weights@vertices[face,3:6]
        normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
        uv=weights@vertices[face,12:14]
        tangent=weights@vertices[face,6:9]
        bitangent=weights@vertices[face,9:12]
        perturb=sample_map(normal_map,uv)
        nz=np.sqrt(np.maximum(0,1-perturb[:,1:2]**2-perturb[:,3:4]**2))
        normal=tangent*perturb[:,3:4]+bitangent*perturb[:,1:2]+normal*nz
        normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
        base=sample_map(albedo,uv); packed=sample_map(spec,uv)
        team=base[:,3:4]
        # Match the stock Seraphim color remap/team-mask convention. Lighting
        # remains an analytic preview, not the game's PBR environment cubemap.
        base=(base[:,[2,2,1]]+np.array((.4,.43,.47)))*.8
        ndotv=np.clip(normal@view,0,1)[:,None]
        tint=(2*ndotv**6-2*ndotv+1.5)*np.array(player)
        base=base*(1-team)+tint*team
        diffuse=np.clip(normal@sun,0,1)[:,None]
        sky=np.clip(normal[:,1:2]*.1+.10,.02,.20)
        # Analytic preview environment, not a replacement for the game's cubemap.
        reflection=2*(normal@view)[:,None]*normal-view
        sky_amount=np.clip(reflection[:,1:2]*.5+.5,0,1)**2
        environment=np.array((.035,.05,.075))+sky_amount*np.array((.40,.50,.66))
        band=np.exp(-((reflection[:,1:2]-.19)/.115)**2)*.46
        softbox=np.clip(reflection@normalized((-.55,.45,.7)),0,1)[:,None]**28*.85
        environment+=band+softbox
        metal=np.ones_like(packed[:,0:1])
        reflected_tint=(1-team)*(.35+.60*base)+team*(.05+.9*base)
        color=base*(.32+.46*diffuse+sky*.5)*(1-.55*metal)
        color+=environment*metal*reflected_tint
        gloss=packed[:,1:2]
        shine=np.clip(normal@half,0,1)[:,None]**(18+62*gloss)*gloss*.7
        color+=shine*(.85+.15*base)
        color+=base*packed[:,2:3]*.32
        patch=canvas[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        patch[mask]=np.clip(color,0,1)
        target[mask]=z[mask]
    result=Image.fromarray((np.clip(canvas,0,1)**.88*255).astype(np.uint8))
    if transparent:
        result.putalpha(Image.fromarray(np.where(np.isfinite(zbuffer),255,0).astype(np.uint8)))
    result=result.resize((target_size,target_size),Image.Resampling.LANCZOS)
    result.save(output)
    return result



