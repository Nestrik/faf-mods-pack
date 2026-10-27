"""Reference-shaped geometry, material atlas, and previews of the exported SCM.

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
FIN_ANGLES = (math.radians(150), math.radians(30), math.radians(270))


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
                u0,u1=(0,1) if finish=="armor" else (j/count,(j+1)/count)
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


def build_mesh(detail):
    m = Mesh(detail)
    # Six splayed, plated feet, rather than a single pyramidal plinth.
    m.column([(8.7,.15),(9.4,.75),(9.1,3.2),(7.5,6.1),(5.5,7.5)],material="dark")
    for i in range(6):
        a = math.radians(30+i*60)
        shape = [(6.3,3.0,3.1,2.6),(9.2,3.0,3.45,2.55),(12.6,2.05,3.1,1.8),
                 (16.3,.9,2.55,.74),(18.0,.62,2.0,.46)]
        if detail<24: shape=[shape[j] for j in (0,2,4)]
        m.foot(shape,a,"dark")
        rim = [(r,y+d+.05,w*.89,.24) for r,y,w,d in shape]
        m.foot(rim,a,"edge")
        plate = [(r,y+d+.34,w*.73,.12) for r,y,w,d in shape]
        m.foot(plate,a,"armor")
        # Long inset vent with a team-color light, aligned to the foot's slope.
        if detail>=24:
            m.foot([(12.5,4.25,.44,.10),(14.3,3.25,.37,.09),(16.2,2.04,.23,.08)],a,"joint")
            m.foot([(12.85,4.19,.11,.12),(14.3,3.39,.11,.11),(15.55,2.55,.09,.10)],a,"team")
        # Raised navy shoulders support the frames and fill the central plinth.
        m.foot([(3.8,7.35,1.7,.85),(6.4,6.45,2.35,1.3),(9.9,4.5,2.7,1.0)],a,"dark")
        m.blade([(5.7,6.9,.11),(8.1,6.25,.11)],a,0,"team",False,.14)
    m.annulus(4.4,6.2,6.4,7.2,material="edge")
    m.column([(5.3,7.0),(5.3,8.0),(4.6,8.5),(4.6,9.4)],material="dark")
    m.annulus(3.65,5.35,8.15,8.6,material="steel")
    m.annulus(3.9,4.85,9.3,9.75,material="edge")
    m.column([(3.35,9.4),(3.35,10.1),(2.6,10.7),(2.0,11.2)],material="steel")

    # Three open, curved frames. Two rails surround an actual empty window.
    samples = 14 if detail>=24 else 5
    for bone,(a,height) in enumerate(zip(FIN_ANGLES,(33.3,33.3,37.2)),5):
        def section(t):
            y = 8+(height-8)*t
            r = 7.0+3.15*math.sin(math.pi*t*.95)-.2*t
            width = (.75+2.1*math.sin(math.pi*t)**.65)*(1-.97*t**5)
            return y,r,width
        all_sections = [section(i/samples) for i in range(samples+1)]
        # Broad lower armor and pointed upper cap join the two rails.
        m.blade([section(i*.31/5) for i in range(6)],a,bone,depth=1.03)
        m.blade([section(.83+i*.17/4) for i in range(5)],a,bone,depth=.77)
        outer, inner = [], []
        for i in range(samples+1):
            t = .27+.60*i/samples
            y,r,w = section(t)
            outer.append((y,r+w*.69,w*.31))
            inner.append((y,r-w*.76,w*.24))
        m.blade(outer,a,bone,depth=.95)
        m.blade(inner,a,bone,depth=.63)
        # Recessed luminous spine inside each open frame.
        glow = []
        for i in range(7):
            t = .38+.36*i/6
            y,r,w = section(t)
            glow.append((y,r-w*.22,.115 if i not in (0,6) else .065))
        m.blade([(y,r,w+.15) for y,r,w in glow],a,bone,"steel",False,.23)
        m.blade(glow,a,bone,"team",False,.26)
        # The lower dark structural tendon remains visible beside the armor.
        tendon = [(y,r-1.7,w*.31) for y,r,w in all_sections[:max(3,samples//2)]]
        m.blade(tendon,a,bone,"dark",False,.64)

    # Small lower cradle, leaving a clear gap below the floating crystal tip.
    for a in FIN_ANGLES:
        m.blade([(10,3.4,.55),(11.3,4.5,.62),(13.4,4.8,.42),(15.7,4.25,.26)],
                a,0,"edge",True,.52)
    m.annulus(1.4,2.75,10.9,11.35,material="edge")

    # Suspended double-point crystal, not a solid column reaching the ground.
    crystal_sides = 8
    rings=[]; centers=[]
    for y,r,twist in ((13,.025,0),(17,1.82,.09),(21.5,3.25,0),(25.5,1.9,-.08),(29.1,.025,0)):
        rings.append([(r*math.cos(i*2*math.pi/crystal_sides+twist),y,
                       r*math.sin(i*2*math.pi/crystal_sides+twist)) for i in range(crystal_sides)])
        centers.append((0,y,0))
    m.loft(rings,centers,4,"crystal")

    # Armillary equator and short beam lens. Yaw and pitch keep their own bones.
    m.annulus(3.45,4.45,20.5,22.65,1,"dark")
    m.annulus(3.45,4.65,20.45,20.85,1,"edge")
    m.annulus(3.45,4.65,22.3,22.75,1,"edge")
    m.annulus(4.42,4.64,21.15,21.9,1,"armor")
    for i in range(6 if detail>=24 else 3):
        a = i*math.pi/3
        m.blade([(20.25,4.58,.28),(22.85,4.58,.28)],a,1,"edge",False,.28)
    m.nozzle([(1.25,3.5),(1.7,4.0),(1.82,4.7),(1.82,5.75),(1.62,6.3)],material="edge")
    m.nozzle([(1.34,5.83),(1.38,6.34),(1.16,6.5)],material="joint")
    m.nozzle([(1.00,6.50),(.96,6.53)],material="lens")
    m.nozzle([(.72,6.55),(.65,6.6)],material="team")
    m.smooth()
    return m


def make_textures(asset_dir, unit_dir, save_dds):
    size=512
    albedo=np.zeros((size,size,4),dtype=np.uint8)
    specteam=np.zeros_like(albedo)
    normals=np.zeros_like(albedo)
    normals[:]=(128,128,255,255)
    palettes=((198,200,193),(30,38,57),(173,151,111),(65,75,85),
              (176,192,199),(156,188,198),(48,91,106),(37,44,51))
    for tile,name in enumerate(MATERIALS):
        ox,oy=(tile%4)*128,(tile//4)*256
        for y in range(256):
            for x in range(128):
                u=x/127; v=y/255
                brush=1.2*math.sin(y*.83)+.8*math.sin(x*.53+y*.16)
                sheen=5*math.sin(math.pi*u)+3*math.cos(v*math.pi*2)
                value=np.array(palettes[tile],dtype=float)+brush+sheen
                mask=0; glow=0
                reflect,specular=(148,168)
                if name=="armor":
                    # Sparse paired organic lines; team hue comes from alpha.
                    curves=(.23+.055*math.sin(v*6.5),.76+.065*math.sin(v*7.0+1.8))
                    d=min(abs(u-c) for c in curves)
                    mask=int(160*max(0,1-d/.013)) if .10<v<.91 else 0
                    edge=min(u,1-u,v*.5,(1-v)*.5)
                    if .040<edge<.047:
                        value-=26
                elif name=="dark":
                    reflect,specular=83,110
                    if abs(u-.5-.08*math.sin(v*12))<.006:
                        value+=13
                elif name=="edge":
                    reflect,specular=183,202
                    value+=8*math.cos(u*math.pi*2)
                elif name in ("team","crystal","lens"):
                    mask=255
                    glow={"team":130,"crystal":128,"lens":190}[name]
                    if name=="crystal":
                        shard=12*math.sin(22*u+9*v)+8*math.sin(43*u-27*v)
                        value+=shard+20*max(0,1-abs(u-.5-v*.15)*4)
                        reflect,specular=115,190
                    elif name=="lens":
                        value+=25*math.sin(u*math.pi)*math.sin(v*math.pi)
                elif name=="joint":
                    reflect,specular=70,100
                albedo[oy+y,ox+x]=tuple(np.clip(value,0,255).astype(np.uint8))+(255,)
                specteam[oy+y,ox+x]=(reflect,specular,glow,mask)
    for suffix,data in (("albedo",albedo),("specteam",specteam),("normalsTS",normals)):
        im=Image.fromarray(data)
        save_dds(im,unit_dir/f"GGA2301_{suffix}.dds")
        im.save(asset_dir/f"GGA2301_{suffix}_source.png")
    Image.fromarray(specteam[:,:,3]).save(asset_dir/"GGA2301_team_mask_preview.png")
    Image.fromarray(albedo).save(asset_dir/"GGA2301_albedo_preview.png")


def load_scm(path):
    data=Path(path).read_bytes()
    h=struct.unpack_from("<4s11I",data)
    vertices=np.array([struct.unpack_from("<16f4B",data,h[4]+i*68)[:17] for i in range(h[6])])
    faces=np.frombuffer(data,dtype="<u2",count=h[8],offset=h[7]).reshape(-1,3).copy()
    return vertices,faces


def export_obj(mesh, asset_dir):
    # Full editable geometry and named bone groups for DCC import.
    out=["# GGA2301, Y up, +Z forward; source units (game scale 0.06)","mtllib GGA2301_source.mtl"]
    for v in mesh.vertices:
        out.append("v %.6f %.6f %.6f"%v[:3])
    for v in mesh.vertices:
        out.append("vt %.7f %.7f"%(v[12],1-v[13]))
    for v in mesh.vertices:
        out.append("vn %.6f %.6f %.6f"%v[3:6])
    bones=("GGA2301","Turret","Turret_Barrel","Turret_Muzzle","Halo","FinLeft","FinRight","FinRear")
    last=None
    for i in range(0,len(mesh.indices),3):
        bone=int(mesh.vertices[mesh.indices[i]][16])
        if bone!=last:
            out.extend(("g "+bones[bone],"usemtl prism_atlas"))
            last=bone
        out.append("f "+" ".join(f"{j+1}/{j+1}/{j+1}" for j in mesh.indices[i:i+3]))
    (asset_dir/"GGA2301_source.obj").write_text("\n".join(out)+"\n",encoding="utf-8")
    (asset_dir/"GGA2301_source.mtl").write_text("newmtl prism_atlas\nKd 1 1 1\nKs 0.6 0.6 0.6\nNs 50\nmap_Kd GGA2301_albedo_source.png\n",encoding="utf-8")


def render_scm(scm, asset_dir, output, azimuth=35, elevation=19, player=(.25,.88,1.0), size=960):
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
    albedo=np.asarray(Image.open(asset_dir/"GGA2301_albedo_source.png"))[:,:,:3]/255
    spec=np.asarray(Image.open(asset_dir/"GGA2301_specteam_source.png"))/255
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
        tx=np.clip((uv[:,0]*albedo.shape[1]).astype(int),0,albedo.shape[1]-1)
        ty=np.clip((uv[:,1]*albedo.shape[0]).astype(int),0,albedo.shape[0]-1)
        base=albedo[ty,tx]; packed=spec[ty,tx]
        team=packed[:,3:4]
        tint=np.clip(np.array(player)*base*1.35,0,1)
        base=base*(1-team)+tint*team
        diffuse=np.clip(normal@sun,0,1)[:,None]
        sky=np.clip(normal[:,1:2]*.1+.10,.02,.20)
        color=base*(.37+.56*diffuse+sky)
        shine=(np.clip(normal@half,0,1)**45)[:,None]*packed[:,1:2]*.44
        color+=shine*(.85+.15*base)
        color+=base*packed[:,2:3]*.32
        patch=canvas[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        patch[mask]=np.clip(color,0,1)
        target[mask]=z[mask]
    result=Image.fromarray((np.clip(canvas,0,1)**.88*255).astype(np.uint8))
    result.save(output)
    return result


def make_previews(unit_dir, asset_dir):
    scm=unit_dir/"GGA2301_lod0.scm"
    render_scm(scm,asset_dir,asset_dir/"GGA2301_prism_spire_preview.png")
    images=[]
    for name,a,e,color in (("Front",0,13,(.25,.88,1)),("Side",72,18,(.25,.88,1)),
                            ("Game view",35,43,(.96,.83,.13))):
        image=render_scm(scm,asset_dir,asset_dir/f"GGA2301_{name.replace(' ','_').lower()}.png",a,e,color,640)
        ImageDraw.Draw(image).text((24,24),name,fill=(210,219,226),font=ImageFont.load_default(size=19))
        images.append(image)
    sheet=Image.new("RGB",(1920,640))
    for i,im in enumerate(images): sheet.paste(im,(i*640,0))
    sheet.save(asset_dir/"GGA2301_reference_rebuild_views.png")
