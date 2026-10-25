"""Mesh primitives, polished Seraphim materials, and exported-SCM previews for GGA2401.

Y is up; +Z is the weapon's forward direction. All dimensions are source units.
This module builds real mesh geometry; preview images are renders of the SCM.
"""
from __future__ import annotations

import math
import struct
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
                normal = np.array(v[3:6])
                compatible = [original[j][3:6] for j in indices if np.dot(normal,original[j][3:6])>.82]
                normal = normalized(np.sum(compatible,axis=0))
                tangent = normalized(np.array(v[6:9])-normal*np.dot(v[6:9],normal))
                handedness = 1 if np.dot(np.cross(normal,tangent),v[9:12])>=0 else -1
                bitangent = np.cross(normal,tangent)*handedness
                self.vertices[i] = v[:3]+tuple(normal)+tuple(tangent)+tuple(bitangent)+v[12:]


def seraphim_inlays(u, v):
    """Fine paired contours and nested ovals, following stock Seraphim markings."""
    def stroke(distance, width):
        return np.clip((width+.004-distance)/.008,0,1)

    sweep=.055*np.sin(v*6.2+.3)+.015*np.sin(v*15)
    distance=np.minimum(abs(u-(.17+sweep)),abs(u-(.83-sweep)))
    paired=np.minimum(abs(u-(.212+sweep)),abs(u-(.788-sweep)))
    lines=np.maximum(stroke(distance,.007),stroke(paired,.0045))
    engraving=np.maximum(stroke(distance,.014),stroke(paired,.010))
    for cy,rx,ry in ((.18,.092,.048),(.39,.13,.065),(.63,.108,.056),(.82,.074,.040)):
        cx=.5+.065*math.sin(cy*8)
        metric=np.sqrt((u-cx)**2+((v-cy)*rx/ry)**2)
        outer=abs(metric-rx)
        inner=abs(metric-rx*.60)
        lines=np.maximum(lines,np.maximum(stroke(outer,.007),stroke(inner,.0045)))
        engraving=np.maximum(engraving,np.maximum(stroke(outer,.014),stroke(inner,.010)))
    fade=np.clip((v-.07)/.025,0,1)*np.clip((.94-v)/.025,0,1)
    return lines*fade,engraving*fade


def make_textures(asset_dir, unit_dir, save_dds):
    size=512
    albedo=np.zeros((size,size,4),dtype=np.uint8)
    specteam=np.zeros_like(albedo)
    normals=np.zeros_like(albedo)
    normals[:]=(128,128,255,255)
    # Every structural finish is silver metal. SpecTeam R/G carry the shine,
    # rather than gold paint or prepainted reflections in the diffuse map.
    palettes=((145,159,177),(84,100,120),(184,196,211),(108,127,149),
              (176,192,199),(156,188,198),(48,91,106),(58,72,91))
    finishes={"armor":(241,234),"dark":(224,220),"edge":(251,246),
              "steel":(235,232),"joint":(216,221)}
    u,v=np.meshgrid(np.linspace(0,1,128),np.linspace(0,1,256))
    brush=.65*np.sin(v*255*.83)+.5*np.sin(u*127*.53+v*255*.16)
    sheen=1.6*np.sin(math.pi*u)+1.2*np.cos(v*math.pi*2)
    lines,engraving=seraphim_inlays(u,v)
    for tile,name in enumerate(MATERIALS):
        ox,oy=(tile%4)*128,(tile//4)*256
        region=np.s_[oy:oy+256,ox:ox+128]
        value=np.array(palettes[tile],dtype=float)+brush[:,:,None]+sheen[:,:,None]
        packed=np.zeros((256,128,4),dtype=float)
        reflect,specular=finishes.get(name,(148,168))
        packed[:,:,0]=reflect; packed[:,:,1]=specular
        if name in ("armor","dark"):
            # Colored incised lines stay metallic and do not emit light.
            packed[:,:,3]=255*lines
            value*=1-.38*lines[:,:,None]-.10*engraving[:,:,None]
            packed[:,:,0]-=engraving*13
            packed[:,:,1]-=engraving*8
            gy,gx=np.gradient(-engraving)
            nx,ny=-gx*.22,-gy*.22
            nz=np.sqrt(np.maximum(0,1-nx*nx-ny*ny))
            normals[region][:,:,:3]=np.clip((np.stack((nx,ny,nz),axis=-1)*.5+.5)*255,0,255).astype(np.uint8)
        elif name in ("team","crystal","lens"):
            packed[:,:,3]=255
            packed[:,:,2]={"team":130,"crystal":128,"lens":190}[name]
            if name=="crystal":
                shard=12*np.sin(22*u+9*v)+8*np.sin(43*u-27*v)
                value+=(shard+20*np.maximum(0,1-abs(u-.5-v*.15)*4))[:,:,None]
                packed[:,:,0]=115; packed[:,:,1]=190
            elif name=="lens":
                value+=(25*np.sin(u*math.pi)*np.sin(v*math.pi))[:,:,None]
        albedo[region][:,:,:3]=np.clip(value,0,255).astype(np.uint8)
        albedo[region][:,:,3]=255
        specteam[region]=np.clip(packed,0,255).astype(np.uint8)
    for suffix,data in (("albedo",albedo),("specteam",specteam),("normalsTS",normals)):
        im=Image.fromarray(data)
        save_dds(im,unit_dir/f"GGA2401_{suffix}.dds")
        im.save(asset_dir/f"GGA2401_{suffix}_source.png")
    Image.fromarray(specteam[:,:,3]).save(asset_dir/"GGA2401_team_mask_preview.png")
    Image.fromarray(albedo).save(asset_dir/"GGA2401_albedo_preview.png")


def load_scm(path):
    data=Path(path).read_bytes()
    h=struct.unpack_from("<4s11I",data)
    vertices=np.array([struct.unpack_from("<16f4B",data,h[4]+i*68)[:17] for i in range(h[6])])
    faces=np.frombuffer(data,dtype="<u2",count=h[8],offset=h[7]).reshape(-1,3).copy()
    return vertices,faces


def export_obj(mesh, asset_dir, bones):
    # Full editable geometry and named bone groups for DCC import.
    out=["# GGA2401, Y up, +Z forward; source units (game scale 0.1)","mtllib GGA2401_source.mtl"]
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
            out.extend(("g "+bones[bone],"usemtl artillery_atlas"))
            last=bone
        out.append("f "+" ".join(f"{j+1}/{j+1}/{j+1}" for j in mesh.indices[i:i+3]))
    (asset_dir/"GGA2401_source.obj").write_text("\n".join(out)+"\n",encoding="utf-8")
    (asset_dir/"GGA2401_source.mtl").write_text("newmtl artillery_atlas\nKd 1 1 1\nKs 0.6 0.6 0.6\nNs 50\nmap_Kd GGA2401_albedo_source.png\n",encoding="utf-8")


def sample_map(texture,uv):
    """Bilinear sampling keeps fine incised lines smooth in the preview."""
    h,w=texture.shape[:2]
    x=np.clip(uv[:,0]*w-.5,0,w-1); y=np.clip(uv[:,1]*h-.5,0,h-1)
    x0=np.floor(x).astype(int); y0=np.floor(y).astype(int)
    x1=np.minimum(x0+1,w-1); y1=np.minimum(y0+1,h-1)
    fx=(x-x0)[:,None]; fy=(y-y0)[:,None]
    return ((texture[y0,x0]*(1-fx)+texture[y0,x1]*fx)*(1-fy)
            +(texture[y1,x0]*(1-fx)+texture[y1,x1]*fx)*fy)


def render_scm(scm, asset_dir, output, azimuth=35, elevation=19, player=(.12,.24,1.0), size=960):
    target_size=size
    size=math.ceil(size*1.5)
    vertices,faces=load_scm(scm)
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
    albedo=np.asarray(Image.open(asset_dir/"GGA2401_albedo_source.png"))[:,:,:3]/255
    spec=np.asarray(Image.open(asset_dir/"GGA2401_specteam_source.png"))/255
    normal_map=np.asarray(Image.open(asset_dir/"GGA2401_normalsTS_source.png"))[:,:,:3]/127.5-1
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
        normal=tangent*perturb[:,0:1]+bitangent*perturb[:,1:2]+normal*perturb[:,2:3]
        normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
        base=sample_map(albedo,uv); packed=sample_map(spec,uv)
        team=packed[:,3:4]
        tint=np.clip(np.array(player)*base*1.35,0,1)
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
        shine=(np.clip(normal@half,0,1)**65)[:,None]*packed[:,1:2]*.56
        color+=shine*(.85+.15*base)
        color+=base*packed[:,2:3]*.32
        patch=canvas[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        patch[mask]=np.clip(color,0,1)
        target[mask]=z[mask]
    result=Image.fromarray((np.clip(canvas,0,1)**.88*255).astype(np.uint8))
    result=result.resize((target_size,target_size),Image.Resampling.LANCZOS)
    result.save(output)
    return result


