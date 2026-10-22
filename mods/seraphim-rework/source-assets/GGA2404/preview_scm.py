"""Render exported SCM, not Blender authoring geometry. Adapted from GGA2404."""
from pathlib import Path
import math,struct
import numpy as np
from PIL import Image,ImageDraw
def normalized(v):
    a=np.array(v,dtype=float);return a/np.linalg.norm(a)

def load_scm(path):
    data=Path(path).read_bytes()
    h=struct.unpack_from("<4s11I",data)
    vertices=np.array([struct.unpack_from("<16f4B",data,h[4]+i*68)[:17] for i in range(h[6])])
    faces=np.frombuffer(data,dtype="<u2",count=h[8],offset=h[7]).reshape(-1,3).copy()
    return vertices,faces


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
    faces=faces[~np.isin(vertices[faces[:,0],16],[10,11])]
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
    albedo_rgba=np.asarray(Image.open(asset_dir/"GGA2404_albedo_source.png"))/255
    albedo=albedo_rgba[:,:,:3]
    spec=np.asarray(Image.open(asset_dir/"GGA2404_specteam_source.png"))/255
    normal_map=np.asarray(Image.open(asset_dir/"GGA2404_normalsTS_source.png"))/127.5-1
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
        packed_normal=sample_map(normal_map,uv)
        nx,ny=packed_normal[:,3],packed_normal[:,1]
        perturb=np.column_stack((nx,ny,np.sqrt(np.maximum(0,1-nx*nx-ny*ny))))
        normal=tangent*perturb[:,0:1]+bitangent*perturb[:,1:2]+normal*perturb[:,2:3]
        normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
        base=sample_map(albedo,uv); packed=sample_map(spec,uv)
        # Approximate the native Seraphim remap. This software lighting remains
        # a preview, not the engine PBR/falloff/cubemap implementation.
        team=sample_map(albedo_rgba,uv)[:,3:4]
        base=(base[:,[2,2,1]]+np.array((.4,.43,.47)))*.8
        tint=np.broadcast_to(np.array(player),base.shape)
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
        # Native Seraphim is fully metallic: no broad Lambert diffuse term.
        # The previous generic-Unit approximation made dark steel look silver.
        color=base*.035+environment*base*.78
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



if __name__=='__main__':
    here=Path(__file__).resolve().parent;unit=here.parents[1]/'units/GGA2404'
    for name,az,el,color in [('front',15,25,(.12,.24,1.)),('side',90,18,(.12,.24,1.)),('top',35,65,(.12,.24,1.)),('red',-40,26,(1.,.08,.05))]:
        render_scm(unit/'GGA2404_lod0.scm',here,here/f'GGA2404_{name}.png',az,el,color,700)
        print(name,flush=True)
