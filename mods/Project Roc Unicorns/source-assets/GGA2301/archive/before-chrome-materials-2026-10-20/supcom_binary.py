"""SCM v5 / SCA v5 and DDS BC3 writers, following the SupCom exporter layout."""
import struct
from PIL import Image


def pad(size):
    value=32-size%32
    return value+32 if value<4 else value


def write_scm(mesh,path,names,parents,pivots):
    encoded=b"\0".join(n.encode("ascii") for n in names)+b"\0"
    name_offset=48+pad(48)
    bone_offset=name_offset+len(encoded)+pad(name_offset+len(encoded))
    vertex_offset=bone_offset+len(names)*108+pad(bone_offset+len(names)*108)
    index_offset=vertex_offset+len(mesh.vertices)*68
    index_offset+=pad(index_offset)
    if len(mesh.vertices)>65535:
        raise ValueError("SCM's 16-bit indices cannot address this vertex count")
    with path.open("wb") as f:
        f.write(struct.pack("<4s11I",b"MODL",5,bone_offset,len(names),vertex_offset,0,
                            len(mesh.vertices),index_offset,len(mesh.indices),0,0,len(names)))
        def section(tag):
            f.write(b"\xC5"*(pad(f.tell())-4)); f.write(tag)
        section(b"NAME"); f.write(encoded)
        section(b"SKEL")
        name_at=name_offset
        for i,(name,parent,pivot) in enumerate(zip(names,parents,pivots)):
            absolute=list(pivot)
            ancestor=parent
            while ancestor>=0:
                absolute=[absolute[j]+pivots[ancestor][j] for j in range(3)]
                ancestor=parents[ancestor]
            matrix=(1,0,0,0,0,1,0,0,0,0,1,0,-absolute[0],-absolute[1],-absolute[2],1)
            f.write(struct.pack("<16f3f4f4i",*matrix,*pivot,1,0,0,0,name_at,parent,0,0))
            name_at+=len(name)+1
        section(b"VTXL")
        for vertex in mesh.vertices:
            f.write(struct.pack("<16f4B",*vertex[:16],vertex[16],0,0,0))
        section(b"TRIS")
        f.write(struct.pack(f"<{len(mesh.indices)}H",*mesh.indices))


def write_sca(path,names,parents,frames,duration):
    encoded=b"\0".join(n.encode("ascii") for n in names)+b"\0"
    names_offset=40+pad(40)
    links_offset=names_offset+len(encoded)+pad(names_offset+len(encoded))
    data_offset=links_offset+4*len(names)+pad(links_offset+4*len(names))
    frame_size=8+28*len(names)
    with path.open("wb") as f:
        f.write(struct.pack("<4siifiiiii",b"ANIM",5,len(frames),duration,len(names),
                            names_offset,links_offset,data_offset,frame_size))
        f.write(b"\xC5"*(names_offset-f.tell()-4)); f.write(b"NAME"); f.write(encoded)
        f.write(b"\xC5"*(links_offset-f.tell()-4)); f.write(b"LINK")
        f.write(struct.pack(f"<{len(parents)}i",*parents))
        f.write(b"\xC5"*(data_offset-f.tell()-4)); f.write(b"DATA")
        f.write(struct.pack("<3f4f",0,0,0,1,0,0,0))
        for index,bones in enumerate(frames):
            f.write(struct.pack("<fi",duration*index/(len(frames)-1),0))
            for position,rotation in bones:
                f.write(struct.pack("<3f4f",*position,*rotation))


def rgb565(color):
    r,g,b=color
    return ((r*31+127)//255<<11)|((g*63+127)//255<<5)|((b*31+127)//255)


def decode565(value):
    return (((value>>11&31)*255+15)//31,((value>>5&63)*255+31)//63,((value&31)*255+15)//31)


def encode_dxt5_block(pixels):
    alphas=[p[3] for p in pixels]
    a0,a1=max(alphas),min(alphas)
    palette=[a0,a1]+[((7-i)*a0+i*a1+3)//7 for i in range(1,7)]
    alpha_bits=0
    for i,a in enumerate(alphas):
        alpha_bits|=min(range(8),key=lambda j:abs(a-palette[j]))<<(3*i)
    colors=[p[:3] for p in pixels]
    lo=min(colors,key=lambda c:.299*c[0]+.587*c[1]+.114*c[2])
    hi=max(colors,key=lambda c:.299*c[0]+.587*c[1]+.114*c[2])
    c0,c1=rgb565(hi),rgb565(lo)
    if c0<c1: c0,c1=c1,c0
    if c0==c1: c1=max(0,c0-1)
    p0,p1=decode565(c0),decode565(c1)
    palette=[p0,p1,tuple((2*p0[i]+p1[i]+1)//3 for i in range(3)),tuple((p0[i]+2*p1[i]+1)//3 for i in range(3))]
    color_bits=0
    for i,color in enumerate(colors):
        color_bits|=min(range(4),key=lambda j:sum((color[k]-palette[j][k])**2 for k in range(3)))<<(2*i)
    return bytes((a0,a1))+alpha_bits.to_bytes(6,"little")+struct.pack("<HHI",c0,c1,color_bits)


def save_dds_dxt5(image,path):
    levels=[]
    current=image.convert("RGBA")
    while True:
        levels.append(current)
        if current.size==(1,1): break
        current=current.resize((max(1,current.width//2),max(1,current.height//2)),Image.Resampling.LANCZOS)
    data=bytearray()
    for mip in levels:
        rgba=mip.load()
        for by in range((mip.height+3)//4):
            for bx in range((mip.width+3)//4):
                pixels=[rgba[min(mip.width-1,bx*4+x),min(mip.height-1,by*4+y)] for y in range(4) for x in range(4)]
                data.extend(encode_dxt5_block(pixels))
    w,h=image.size
    flags=0x1|0x2|0x4|0x1000|0x20000|0x80000
    linear=((w+3)//4)*((h+3)//4)*16
    header=[124,flags,h,w,linear,0,len(levels)]+[0]*11+[32,4,0x35545844,0,0,0,0,0]+[0x401008,0,0,0,0]
    path.write_bytes(b"DDS "+struct.pack("<31I",*header)+data)
