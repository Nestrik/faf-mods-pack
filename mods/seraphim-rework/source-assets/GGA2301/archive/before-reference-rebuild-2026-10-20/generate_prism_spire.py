"""Build the Seraphim GGA2301 Prism Spire SCM, SCA and DDS assets.

The mesh uses authored coordinates at the game's stock-style 0.06 scale.
Only Python's standard library and Pillow are needed to regenerate it.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
UNIT = ROOT / "units" / "GGA2301"
ASSET_DIR = Path(__file__).resolve().parent
SCALE = 0.06
BONENAMES = ["GGA2301", "Turret", "Turret_Barrel", "Turret_Muzzle", "Halo", "FinLeft", "FinRight", "FinRear"]
PARENTS = [-1, 0, 1, 2, 0, 0, 0, 0]
PIVOTS = [(0, 0, 0), (0, 24, 0), (0, 0, 0), (0, 0, 15), (0, 10, 0), (-4, 7, 0), (4, 7, 0), (0, 7, -4)]


def pad(size: int) -> int:
    # SupCom's exporter aligns every section through a 32-byte pad helper.
    # The four-byte section tag is included in this amount.
    value = 32 - size % 32
    return value + 32 if value < 4 else value


def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(v):
    length = math.sqrt(sum(x * x for x in v))
    return tuple(x / length for x in v) if length > 1e-9 else (0.0, 1.0, 0.0)


def uv_basis(p0, p1, p2, uv0, uv1, uv2):
    e1, e2 = sub(p1, p0), sub(p2, p0)
    du1, dv1 = uv1[0] - uv0[0], uv1[1] - uv0[1]
    du2, dv2 = uv2[0] - uv0[0], uv2[1] - uv0[1]
    det = du1 * dv2 - du2 * dv1
    if abs(det) < 1e-8:
        return (1, 0, 0), (0, 1, 0)
    return norm(tuple((e1[i] * dv2 - e2[i] * dv1) / det for i in range(3))), norm(tuple((e2[i] * du1 - e1[i] * du2) / det for i in range(3)))


class Mesh:
    def __init__(self, segments: int):
        self.segments = segments
        self.vertices: list[tuple] = []
        self.indices: list[int] = []

    def tri(self, points, bone=0, team=False, uvs=None, finish="metal"):
        if uvs is None:
            if team:
                uvs = ((0.88, 0.12), (0.98, 0.12), (0.98, 0.88))
            else:
                bands = {"metal": (0.055, 0.555), "recess": (0.615, 0.685), "trim": (0.735, 0.815)}
                left, right = bands[finish]
                uvs = tuple((left + (right-left) * max(0, min(1, (p[0]+16)/40)),
                             0.07 + 0.86 * max(0, min(1, p[1]/42))) for p in points)
        normal = norm(cross(sub(points[1], points[0]), sub(points[2], points[0])))
        tangent, bitangent = uv_basis(*points, *uvs)
        for p, uv in zip(points, uvs):
            uv = (min(0.83, max(0.04, uv[0])), min(0.94, max(0.06, uv[1]))) if not team else uv
            self.vertices.append((*p, *normal, *tangent, *bitangent, *uv, *uv, bone))
            self.indices.append(len(self.vertices) - 1)

    def quad(self, a, b, c, d, bone=0, team=False, finish="metal"):
        self.tri((a, b, c), bone, team, finish=finish)
        self.tri((a, c, d), bone, team, finish=finish)

    def prism(self, radius, y0, y1, bone=0, sides=None, z_offset=0, finish="metal"):
        sides = sides or self.segments
        ring0, ring1 = [], []
        for i in range(sides):
            a = 2 * math.pi * i / sides + math.pi / sides
            ring0.append((radius * math.cos(a), y0, z_offset + radius * math.sin(a)))
            ring1.append((radius * math.cos(a), y1, z_offset + radius * math.sin(a)))
        center0, center1 = (0, y0, z_offset), (0, y1, z_offset)
        for i in range(sides):
            j = (i + 1) % sides
            # Face winding points outwards; FAF's unit shader back-face culls.
            self.quad(ring0[i], ring1[i], ring1[j], ring0[j], bone, finish=finish)
            self.tri((center0, ring0[i], ring0[j]), bone, finish=finish)
            self.tri((center1, ring1[j], ring1[i]), bone, finish=finish)

    def tapered_prism(self, radius0, y0, radius1, y1, bone=0, sides=None, z_offset=0, team_color=False, finish="metal"):
        sides = sides or self.segments
        lower, upper = [], []
        for i in range(sides):
            a = 2 * math.pi * i / sides + math.pi / sides
            lower.append((radius0 * math.cos(a), y0, z_offset + radius0 * math.sin(a)))
            upper.append((radius1 * math.cos(a), y1, z_offset + radius1 * math.sin(a)))
        tip = (0, y1 + radius1 * 1.45, z_offset)
        for i in range(sides):
            j = (i + 1) % sides
            self.quad(lower[i], upper[i], upper[j], lower[j], bone, team=team_color, finish=finish)
            self.tri((upper[i], tip, upper[j]), bone, team=team_color, finish=finish)
            self.tri(((0, y0, z_offset), lower[i], lower[j]), bone, finish=finish)

    def box(self, lo, hi, bone=0, team=False, finish="metal"):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
        for a,b,c,d in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)):
            self.quad(v[a],v[b],v[c],v[d],bone,team,finish)

    def barrel(self, radius, z0, z1, bone=2, sides=None, team=False, finish="metal"):
        sides = sides or self.segments
        low, high = [], []
        for i in range(sides):
            a = 2 * math.pi * i / sides
            low.append((radius * math.cos(a), 24 + radius * math.sin(a), z0))
            high.append((radius * math.cos(a), 24 + radius * math.sin(a), z1))
        for i in range(sides):
            j=(i+1)%sides
            self.quad(low[i],low[j],high[j],high[i],bone,team,finish)

    def ribbon(self, radius, y0, y1, turns, bone=0, strips=1):
        steps = 80 if self.segments >= 8 else 32
        width = 0.28
        for s in range(strips):
            phase = s * (2 * math.pi / strips)
            for i in range(steps):
                t0, t1 = i / steps, (i + 1) / steps
                def point(t, side):
                    a = 2 * math.pi * turns * t + phase
                    r = radius + side * width / 2
                    y = y0 + (y1 - y0) * t
                    return (r * math.cos(a), y, r * math.sin(a))
                self.quad(point(t0,-1),point(t1,-1),point(t1,1),point(t0,1),bone,True)

    def write(self, path: Path):
        names=b"\0".join(n.encode("ascii") for n in BONENAMES)+b"\0"
        name_offset=48+pad(48)
        bone_offset=name_offset+len(names)+pad(name_offset+len(names))
        vertex_offset=bone_offset+len(BONENAMES)*108+pad(bone_offset+len(BONENAMES)*108)
        index_offset=vertex_offset+len(self.vertices)*68
        index_offset+=pad(index_offset)
        header=(b"MODL",5,bone_offset,len(BONENAMES),vertex_offset,0,len(self.vertices),index_offset,len(self.indices),0,0,len(BONENAMES))
        with path.open("wb") as f:
            f.write(struct.pack("<4s11I",*header))
            def section(tag):
                f.write(b"\xC5"*(pad(f.tell())-4)); f.write(tag)
            section(b"NAME"); f.write(names)
            section(b"SKEL")
            name_at=name_offset
            for i,(name,parent,pivot) in enumerate(zip(BONENAMES,PARENTS,PIVOTS)):
                # Inverse absolute bind transform; root carries the standard SupCom axis conversion.
                if i==0:
                    # Vertices and skeleton are already authored in game axes.
                    matrix=(1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)
                    quat=(1,0,0,0)
                else:
                    absolute=list(pivot)
                    if parent>=0:
                        parent_index=parent
                        while parent_index>=0:
                            absolute=[absolute[j]+PIVOTS[parent_index][j] for j in range(3)]
                            parent_index=PARENTS[parent_index]
                    matrix=(1,0,0,0, 0,1,0,0, 0,0,1,0, -pivot[0],-pivot[1],-pivot[2],1)
                    quat=(1,0,0,0)
                    matrix=matrix[:12]+(-absolute[0],-absolute[1],-absolute[2],1)
                f.write(struct.pack("<16f3f4f4i",*matrix,*pivot,*quat,name_at,parent,0,0))
                name_at+=len(name)+1
            section(b"VTXL")
            for v in self.vertices:
                f.write(struct.pack("<16f4B",*v[:16],v[16],0,0,0))
            section(b"TRIS"); f.write(struct.pack(f"<{len(self.indices)}H",*self.indices))


def build_mesh(segments: int) -> Mesh:
    m=Mesh(segments)
    # Layered octagonal plinth: shaded seam, silver edge, then broad steel armor.
    m.prism(13,0,1.15,0,segments,finish="recess")
    m.prism(13.12,1.15,1.52,0,segments,finish="trim")
    m.prism(13,1.52,2,0,segments)
    m.tapered_prism(13,2,10.5,4.5,0,segments)
    m.prism(10.55,4.45,4.72,0,segments,finish="trim")
    m.prism(9.5,4.72,5.7,0,segments,finish="recess")
    m.prism(9.72,5.7,6,0,segments,finish="trim")
    m.tapered_prism(9.5,6,6.8,9,0,segments)
    m.prism(6.5,9,10.6,0,segments,finish="recess")
    m.prism(6.65,10.6,11,0,segments,finish="trim")
    # Side armor petals, metallic with team-color inlay lines.
    for i in range(4):
        a=math.pi/4+i*math.pi/2
        cx,cz=9*math.cos(a),9*math.sin(a)
        m.box((cx-1.7,1.4,cz-2.2),(cx+1.7,3.7,cz+2.2),0)
        m.box((cx-1.45,3.65,cz-1.65),(cx+1.45,3.77,cz+1.65),0,finish="trim")
        m.box((cx-.22,3.77,cz-1.35),(cx+.22,3.9,cz+1.35),0,True)
    # Central, faceted player-color prism inside a metal retaining cage.
    m.prism(5.5,10.5,12,0,segments)
    m.tapered_prism(4.3,12,3.5,27,0,segments,team_color=True)
    m.prism(4.12,17.3,17.65,0,segments,finish="trim")
    m.prism(3.8,23.4,23.72,0,segments,finish="trim")
    m.prism(5.2,14,14.55,4,segments)
    m.ribbon(3.65,12,27,2.4,4,3)
    # Three swept fins open on activation; each is its own rigged bone.
    for bone, sign in ((5,-1),(6,1)):
        x0=-4 if sign<0 else 4
        m.quad((x0,7,0),(x0+sign*4,7,0),(x0+sign*3.1,18,1.5),(x0+sign*.5,14,1.3),bone)
        m.quad((x0,7,0),(x0+sign*.5,14,1.3),(x0+sign*3.1,18,1.5),(x0+sign*3.4,8,1),bone,finish="recess")
        m.quad((x0+sign*.75,8.2,1.08),(x0+sign*1.15,8.2,1.08),(x0+sign*2.65,16.0,1.54),(x0+sign*2.25,16.0,1.54),bone,True)
        m.quad((x0+sign*3.15,8.1,1.12),(x0+sign*3.3,8.1,1.12),(x0+sign*3.0,17.0,1.58),(x0+sign*2.85,17.0,1.58),bone,finish="trim")
    m.quad((-1,7,-4),(1,7,-4),(1,18,-7.5),(-1,15,-6.8),7)
    m.quad((-1,7,-4),(-1,15,-6.8),(1,18,-7.5),(1,8,-4.8),7,finish="recess")
    m.quad((-.2,8,-4.6),(.18,8,-4.6),(.18,16.9,-7.25),(-.2,15.0,-6.8),7,True)
    # Yaw and pitch gimbal plus forward-facing XSB2301 beam emitter.
    m.prism(3.4,21,27,1,segments,finish="recess")
    m.prism(3.55,26.3,26.7,1,segments,finish="trim")
    m.barrel(2.0,0,9.3,2,segments)
    m.barrel(2.75,9.3,10.25,2,segments,finish="recess")
    m.barrel(2.82,10.25,10.55,2,segments,finish="trim")
    m.barrel(1.6,10.55,14.0,2,segments)
    m.barrel(2.4,13.8,15.2,2,segments,finish="recess")
    m.barrel(2.46,14.82,15.2,2,segments,finish="trim")
    m.prism(2.1,10,13,4,segments)  # hidden local-axis hub for the rotating halo
    # Fine metal ring ribs on the upper emitter.
    for z in (3.2,6.6,9.2):
        m.barrel(2.08,z,z+.18,2,segments,finish="trim")
    return m


def rotation_y(angle):
    return (math.cos(angle/2),0,math.sin(angle/2),0)


def make_activation(path: Path):
    names=b"\0".join(n.encode("ascii") for n in BONENAMES)+b"\0"
    names_offset=40+pad(40)
    links_end=names_offset+len(names)
    links_offset=links_end+pad(links_end)
    data_end=links_offset+4*len(BONENAMES)
    data_offset=data_end+pad(data_end)
    frame_size=8+28*len(BONENAMES)
    num_frames=31
    duration=1.0
    with path.open("wb") as f:
        f.write(struct.pack("<4siifiiiii",b"ANIM",5,num_frames,duration,len(BONENAMES),names_offset,links_offset,data_offset,frame_size))
        f.write(b"\xC5"*(names_offset-f.tell()-4)); f.write(b"NAME"); f.write(names)
        f.write(b"\xC5"*(links_offset-f.tell()-4)); f.write(b"LINK"); f.write(struct.pack("<8i",*PARENTS))
        f.write(b"\xC5"*(data_offset-f.tell()-4)); f.write(b"DATA")
        f.write(struct.pack("<3f4f",0,0,0,1,0,0,0))
        for frame in range(num_frames):
            t=frame/(num_frames-1)
            eased=t*t*(3-2*t)
            f.write(struct.pack("<fi",duration*t,0))
            for bone in range(len(BONENAMES)):
                angle=0
                if bone==5: angle=-math.radians(28)*eased
                elif bone==6: angle=math.radians(28)*eased
                elif bone==7: angle=math.radians(24)*eased
                f.write(struct.pack("<3f4f",*PIVOTS[bone],*rotation_y(angle)))


def make_idle(path: Path):
    # A 2-second cyclic sweep of the Halo bone; the animation loops seamlessly.
    names=b"\0".join(n.encode("ascii") for n in BONENAMES)+b"\0"
    names_offset=40+pad(40)
    links_end=names_offset+len(names)
    links_offset=links_end+pad(links_end)
    data_end=links_offset+4*len(BONENAMES)
    data_offset=data_end+pad(data_end)
    num_frames=61; duration=12.0; frame_size=8+28*len(BONENAMES)
    with path.open("wb") as f:
        f.write(struct.pack("<4siifiiiii",b"ANIM",5,num_frames,duration,len(BONENAMES),names_offset,links_offset,data_offset,frame_size))
        f.write(b"\xC5"*(names_offset-f.tell()-4)); f.write(b"NAME"); f.write(names)
        f.write(b"\xC5"*(links_offset-f.tell()-4)); f.write(b"LINK"); f.write(struct.pack("<8i",*PARENTS))
        f.write(b"\xC5"*(data_offset-f.tell()-4)); f.write(b"DATA"); f.write(struct.pack("<3f4f",0,0,0,1,0,0,0))
        for frame in range(num_frames):
            t=frame/(num_frames-1)
            f.write(struct.pack("<fi",duration*t,0))
            for bone in range(len(BONENAMES)):
                q=rotation_y(2*math.pi*t) if bone==4 else (1,0,0,0)
                f.write(struct.pack("<3f4f",*PIVOTS[bone],*q))


def make_textures():
    size=256
    albedo=Image.new("RGBA",(size,size),(125,145,158,255))
    spec=Image.new("RGBA",(size,size),(134,150,0,0))
    px=albedo.load(); sp=spec.load()
    # Four UV finishes: blue-silver armor, dark joints, polished edges, team inlays.
    for y in range(size):
        for x in range(size):
            u=(x+.5)/size; v=(y+.5)/size
            if u<.59:
                across=(u-.055)/.5
                brush=2.3*math.sin(y*.49)+1.5*math.sin(x*.18+y*.065)
                sheen=7*math.cos((across-.42)*math.pi*1.6)
                tone=brush+sheen
                mask=0
                if .08<v<.9:
                    # Paired flowing Seraphim lines, stored in the shader's team mask.
                    paths=(.20+.036*math.sin(8*v+.35),
                           .49+.053*math.sin(6.5*v+2.1),
                           .78+.031*math.sin(9*v+4.0))
                    distance=min(abs(across-path) for path in paths)
                    mask=int(180*max(0,1-distance/.020)**1.5)
                shine=mask/30
                px[x,y]=(int(128+tone+shine),int(148+tone+shine),int(162+tone+shine),255)
                sp[x,y]=(146,166,0,mask)
            elif u<.71:
                tone=3*math.sin(y*.13)+2*math.cos(x*.27)
                px[x,y]=(int(48+tone),int(65+tone),int(79+tone),255)
                sp[x,y]=(88,104,0,0)
            elif u<.85:
                tone=5*math.cos((u-.78)*25)+3*math.sin(y*.2)
                px[x,y]=(int(174+tone),int(190+tone),int(201+tone),255)
                sp[x,y]=(190,208,0,0)
            else:
                # The actual color is supplied by FAF from the player's palette.
                px[x,y]=(188,199,205,255)
                sp[x,y]=(142,156,255,255)
    save_dds_dxt5(albedo,UNIT/"GGA2301_albedo.dds")
    save_dds_dxt5(spec,UNIT/"GGA2301_specteam.dds")
    normals=Image.new("RGBA",(size,size),(128,128,255,255))
    save_dds_dxt5(normals,UNIT/"GGA2301_normalsTS.dds")
    albedo.save(ASSET_DIR/"GGA2301_albedo_preview.png")
    spec.getchannel("A").save(ASSET_DIR/"GGA2301_team_mask_preview.png")


def rgb565(color):
    r,g,b=color
    return ((r*31+127)//255<<11)|((g*63+127)//255<<5)|((b*31+127)//255)


def decode565(value):
    r=(value>>11)&31; g=(value>>5)&63; b=value&31
    return ((r*255+15)//31,(g*255+31)//63,(b*255+15)//31)


def encode_dxt5_block(pixels):
    alphas=[p[3] for p in pixels]
    a0,a1=max(alphas),min(alphas)
    palette=[a0,a1]+[( (7-i)*a0+i*a1+3)//7 for i in range(1,7)]
    alpha_bits=0
    for i,a in enumerate(alphas):
        idx=min(range(8),key=lambda j:abs(a-palette[j]))
        alpha_bits|=idx<<(3*i)
    opaque=[p[:3] for p in pixels]
    lo=min(opaque,key=lambda c:0.299*c[0]+0.587*c[1]+0.114*c[2])
    hi=max(opaque,key=lambda c:0.299*c[0]+0.587*c[1]+0.114*c[2])
    c0,c1=rgb565(hi),rgb565(lo)
    if c0<c1: c0,c1=c1,c0
    if c0==c1: c1=max(0,c0-1)
    p0,p1=decode565(c0),decode565(c1)
    colors=[p0,p1,tuple((2*p0[i]+p1[i]+1)//3 for i in range(3)),tuple((p0[i]+2*p1[i]+1)//3 for i in range(3))]
    color_bits=0
    for i,color in enumerate(opaque):
        idx=min(range(4),key=lambda j:sum((color[k]-colors[j][k])**2 for k in range(3)))
        color_bits|=idx<<(2*i)
    return bytes((a0,a1))+alpha_bits.to_bytes(6,"little")+struct.pack("<HHI",c0,c1,color_bits)


def save_dds_dxt5(image: Image.Image, path: Path):
    levels=[]
    current=image.convert("RGBA")
    while True:
        levels.append(current)
        if current.width==1 and current.height==1: break
        current=current.resize((max(1,current.width//2),max(1,current.height//2)),Image.Resampling.LANCZOS)
    data=bytearray()
    for mip in levels:
        rgba=mip.load()
        for by in range((mip.height+3)//4):
            for bx in range((mip.width+3)//4):
                block=[]
                for y in range(4):
                    for x in range(4):
                        block.append(rgba[min(mip.width-1,bx*4+x),min(mip.height-1,by*4+y)])
                data.extend(encode_dxt5_block(block))
    w,h=image.size
    flags=0x1|0x2|0x4|0x1000|0x20000|0x80000
    linear=((w+3)//4)*((h+3)//4)*16
    caps=0x1000 | (0x8|0x400000 if len(levels)>1 else 0)
    header=[124,flags,h,w,linear,0,len(levels)]+[0]*11+[32,4,0x35545844,0,0,0,0,0]+[caps,0,0,0,0]
    path.write_bytes(b"DDS "+struct.pack("<31I",*header)+data)


def make_preview(path: Path):
    mesh=build_mesh(8)
    image=Image.new("RGBA",(512,512),(19,25,31,255))
    draw=ImageDraw.Draw(image)
    albedo=Image.open(ASSET_DIR/"GGA2301_albedo_preview.png").convert("RGBA")
    team_mask=Image.open(ASSET_DIR/"GGA2301_team_mask_preview.png").convert("L")
    right=(0.82,0,-0.57); up=(-0.31,0.93,-0.22); depth=(0.48,0.37,0.79)
    projected=[]
    for i in range(0,len(mesh.vertices),3):
        verts=mesh.vertices[i:i+3]
        if len(verts)<3: continue
        pts=[]; ds=[]
        for v in verts:
            x,y,z=v[:3]
            pts.append((x*right[0]+y*right[1]+z*right[2],x*up[0]+y*up[1]+z*up[2]))
            ds.append(x*depth[0]+y*depth[1]+z*depth[2])
        u=sum(v[12] for v in verts)/3; v=sum(v[13] for v in verts)/3
        tx=min(albedo.width-1,int(u*albedo.width)); ty=min(albedo.height-1,int(v*albedo.height))
        base=albedo.getpixel((tx,ty))
        mask=team_mask.getpixel((tx,ty))/255
        normal=norm(verts[0][3:6]); light=max(0.28,0.55+0.45*(normal[0]*-.4+normal[1]*.65+normal[2]*.64))
        color=tuple(int(((1-mask)*base[c]+mask*(241,208,35)[c])*light) for c in range(3))+(255,)
        projected.append((sum(ds)/3,pts,color))
    projected.sort(key=lambda row:row[0])
    coords=[p for _,pts,_ in projected for p in pts]
    minx,maxx=min(p[0] for p in coords),max(p[0] for p in coords)
    miny,maxy=min(p[1] for p in coords),max(p[1] for p in coords)
    scale=min(390/(maxx-minx),420/(maxy-miny))
    centerx=(minx+maxx)/2; centery=(miny+maxy)/2
    for _,pts,color in projected:
        screen=[(int(256+(x-centerx)*scale),int(272-(y-centery)*scale)) for x,y in pts]
        draw.polygon(screen,fill=color)
    image.save(path)


def main():
    UNIT.mkdir(parents=True,exist_ok=True)
    for filename,segments in (("GGA2301_lod0.scm",8),("GGA2301_lod1.scm",6)):
        build_mesh(segments).write(UNIT/filename)
    make_activation(UNIT/"GGA2301_activate.sca")
    make_idle(UNIT/"GGA2301_idle.sca")
    make_textures()
    make_preview(ASSET_DIR/"GGA2301_prism_spire_preview.png")
    print("Generated Prism Spire meshes, animations and DDS textures in",UNIT)


if __name__=="__main__":
    main()
