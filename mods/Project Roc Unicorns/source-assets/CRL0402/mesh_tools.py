from __future__ import annotations

import math
import struct
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image


MATERIALS = ("armor", "dark", "edge", "steel", "team", "crystal", "lens", "joint")


def normalized(v):
    v = np.asarray(v, dtype=float)
    return v / max(1e-12, np.linalg.norm(v))


def atlas_uv(material, uv):
    if material == "hazard":
        return ((244+3*uv[0])/512,(244+3*uv[1])/256)
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

def load_scm(path):
    data=Path(path).read_bytes()
    h=struct.unpack_from("<4s11I",data)
    vertices=np.array([struct.unpack_from("<16f4B",data,h[4]+i*68)[:17] for i in range(h[6])])
    faces=np.frombuffer(data,dtype="<u2",count=h[8],offset=h[7]).reshape(-1,3).copy()
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


def sample_map(texture,uv):
    """Bilinear sampling keeps fine incised lines smooth in the preview."""
    h,w=texture.shape[:2]
    x=np.clip(uv[:,0]*w-.5,0,w-1); y=np.clip(uv[:,1]*h-.5,0,h-1)
    x0=np.floor(x).astype(int); y0=np.floor(y).astype(int)
    x1=np.minimum(x0+1,w-1); y1=np.minimum(y0+1,h-1)
    fx=(x-x0)[:,None]; fy=(y-y0)[:,None]
    return ((texture[y0,x0]*(1-fx)+texture[y0,x1]*fx)*(1-fy)
            +(texture[y1,x0]*(1-fx)+texture[y1,x1]*fx)*fy)


def render_scm(scm, asset_dir, output, azimuth=35, elevation=19, player=(.12,.24,1.0), size=960, bones=None, texture_mip=0, wreck=False, transparent=False, texture_prefix='CRL0402'):
    target_size=size
    size=math.ceil(size*1.5)
    vertices,faces=load_scm(scm)
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
    span=np.ptp(projected,axis=0)
    scale=min(size*.82/span[0],size*.88/span[1])
    projected=(projected-(projected.min(axis=0)+projected.max(axis=0))/2)*scale+(size/2,size*.49)
    depth=positions@view
    yy,xx=np.mgrid[:size,:size]
    bg=.085+.045*(1-yy/size)
    canvas=np.stack((bg*.91,bg*.97,bg*1.06),axis=-1)
    # Contact shadow is a preview aid, never baked into the game's textures.
    ground_y=(np.array((0,0,0))@up*-scale + (size*.49+(positions@up).max()*scale/2+(positions@up).min()*scale/2))
    shadow=np.exp(-((xx-size*.5)/(size*.31))**2-((yy-ground_y)/(size*.07))**2)*.42
    canvas*=1-shadow[:,:,None]
    zbuffer=np.full((size,size),-np.inf)
    # Inspect the shipped data, rather than PNGs that cannot expose mip/export bugs.
    unit_dir=Path(scm).parent
    maps=unit_dir.parents[1]/'units/GGA0101' if wreck else unit_dir
    albedo=np.asarray(load_dds_mip(unit_dir/('GGA0101_wreck_albedo.dds' if wreck else f'{texture_prefix}_albedo.dds'),texture_mip))/255
    spec=np.asarray(load_dds_mip(maps/f'{texture_prefix}_specteam.dds',texture_mip))/255
    normal_map=np.asarray(load_dds_mip(maps/f'{texture_prefix}_normalsTS.dds',texture_mip))/127.5-1
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
        team=packed[:,3:4]
        # Match the stock Seraphim color remap/team-mask convention. Lighting
        # remains an analytic preview, not the game's PBR environment cubemap.
        base=base[:,:3]
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
        metal=packed[:,0:1]
        reflected_tint=(1-team)*(.35+.60*base)+team*(.05+.9*base)
        color=base*(.32+.46*diffuse+sky*.5)*(1-.55*metal)
        color+=environment*metal*reflected_tint
        gloss=packed[:,1:2]
        shine=np.clip(normal@half,0,1)[:,None]**(18+62*gloss)*gloss*(.08 if wreck else .7)
        color+=shine*(.85+.15*base)
        if not wreck:
            color+=base*packed[:,2:3]*.32
        patch=canvas[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        patch[mask]=np.clip(color,0,1)
        target[mask]=z[mask]
    result=Image.fromarray((np.clip(canvas,0,1)**.88*255).astype(np.uint8))
    if transparent:
        result=result.convert('RGBA')
        result.putalpha(Image.fromarray((np.isfinite(zbuffer)*255).astype(np.uint8)))
    result=result.resize((target_size,target_size),Image.Resampling.LANCZOS)
    result.save(output)
    return result


