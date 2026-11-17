"""Render poses read from the exported SCM and SCA, not from source geometry."""
from pathlib import Path
import struct
import numpy as np
from PIL import Image, ImageDraw
import model_geometry as geom

HERE=Path(__file__).resolve().parent
UNIT=HERE.parents[1]/'units/CRL0401'
model=UNIT/'CRL0401_lod0.scm'
vertices,faces=geom.load_scm(model)
raw=model.read_bytes(); h=struct.unpack_from('<4s11I',raw)
bone_names=[]; positions=[]
for i in range(h[3]):
    item=struct.unpack_from('<16f3f4f4i',raw,h[2]+108*i)
    name_offset=item[23]
    bone_names.append(raw[name_offset:raw.index(b'\0',name_offset)].decode('ascii'))
    positions.append(np.array(item[16:19]))

data=(UNIT/'CRL0401_tracks.sca').read_bytes()
magic,version,count,duration,names_count,names_at,links_at,frames_at,frame_size=struct.unpack_from('<4siifiiiii',data)
assert magic==b'ANIM' and version==5
names=[]; offset=names_at
for _ in range(names_count):
    end=data.index(b'\0',offset); names.append(data[offset:end].decode('ascii')); offset=end+1
lookup={name:i for i,name in enumerate(names)}

def pose(frame):
    out=vertices.copy(); base=frames_at+28+frame*frame_size+8
    for bone,name in enumerate(bone_names):
        if name not in lookup: continue
        x,y,z,w,qx,qy,qz=struct.unpack_from('<3f4f',data,base+28*lookup[name])
        matrix=np.array([[1-2*(qy*qy+qz*qz),2*(qx*qy-qz*w),2*(qx*qz+qy*w)],
                         [2*(qx*qy+qz*w),1-2*(qx*qx+qz*qz),2*(qy*qz-qx*w)],
                         [2*(qx*qz-qy*w),2*(qy*qz+qx*w),1-2*(qx*qx+qy*qy)]])
        mask=vertices[:,16]==bone
        out[mask,:3]=(vertices[mask,:3]-positions[bone])@matrix.T+np.array((x,y,z))
        for k in (3,6,9): out[mask,k:k+3]=vertices[mask,k:k+3]@matrix.T
    return out,faces

images=[]
for f in range(16):
    geom.load_scm=lambda _,f=f: pose(f)
    output=HERE/f'track_frame_{f:02}.png'
    geom.render_scm(model,HERE,output,90,10,player=(.85,.08,.04),size=400)
    images.append(Image.open(output).convert('RGB'))
sheet=Image.new('RGB',(800,800))
for i,frame in enumerate((0,4,8,12)): sheet.paste(images[frame],((i%2)*400,(i//2)*400))
sheet.save(HERE/'tracks_four_poses.png')
images[0].save(HERE/'tracks_motion.gif',save_all=True,append_images=images[1:],duration=round(duration*1000/(count-1)),loop=0)
print('SCA:',count,'frames,',names_count,'bones, duration',duration,'seconds')
