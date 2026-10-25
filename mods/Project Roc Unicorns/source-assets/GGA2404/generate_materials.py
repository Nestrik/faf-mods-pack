"""Author-owned unit maps and Othuy-style particles; no stock assets are copied."""
from pathlib import Path
import io,struct,json,math
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
MOD=HERE.parents[1]
UNIT=MOD/'units/GGA2404'

def save_dds(im,path):
    levels=[]
    while True:
        stream=io.BytesIO();im.save(stream,format='DDS',pixel_format='DXT5');levels.append(stream.getvalue())
        if im.size==(1,1):break
        size=(max(1,im.width//2),max(1,im.height//2))
        # These RGBA channels carry independent material data. Premultiplying
        # by the army mask would erase metal RGB where alpha is zero.
        im=Image.merge('RGBA',tuple(channel.resize(size,Image.Resampling.LANCZOS)
                                    for channel in im.split()))
    header=bytearray(levels[0][:128]);struct.pack_into('<I',header,8,struct.unpack_from('<I',header,8)[0]|0x20000)
    struct.pack_into('<I',header,28,len(levels));struct.pack_into('<I',header,108,0x401008)
    path.write_bytes(header+b''.join(x[128:] for x in levels))

def unit_maps():
    albedo=np.array(Image.open(HERE/'GGA2404_albedo_baseline.png').convert('RGBA'))
    spec=np.array(Image.open(HERE/'GGA2404_specteam_baseline.png').convert('RGBA'))
    normals=np.array(Image.open(HERE/'GGA2404_normalsTS_baseline.png').convert('RGBA'))
    for tile in range(8):
        y=(tile//4)*256;x=(tile%4)*256;s=np.s_[y:y+256,x:x+256]
        if tile in [3,5,6]:
            # Every inlay and luminous surface uses the complete army mask.
            # Seraphim takes army color from Albedo.A. Keep RGB below its
            # white-highlight threshold so colored lines do not bloom white.
            albedo[s]=[88]*3+[255]
            spec[s]=[70,115,0 if tile==3 else 210,255]
            normals[s]=[128,128,255,255]
            if tile==3:
                # The ribbon's V axis crosses the stroke. A shallow concave
                # profile produces incised edges instead of a raised wire.
                for row in range(256):
                    v=max(0,min(1,(row-20)/216))
                    # The exporter retains Blender's bitangent while flipping V
                    # to image coordinates, so the groove's green axis is inverted.
                    slope=-.65*math.sin(2*math.pi*v)
                    n=np.array([0,slope,1]);n/=np.linalg.norm(n)
                    normals[y+row,x:x+256,:3]=np.round((n*.5+.5)*255).astype(np.uint8)
                    value=round(88-15*math.sin(math.pi*v)**2)
                    albedo[y+row,x:x+256,:3]=value
        else:
            # Stock XSB0101/XSB0301/XSB1301 bare-metal RGB median is about 16.
            # Preserve authored surface variation, using dark steel throughout.
            grey=albedo[s][:,:,:3].mean(axis=2)
            target=[10,18,24,0,7,0,0,14][tile]
            grey=grey*target/max(1,float(np.median(grey)))
            albedo[s][:,:,:3]=np.clip(grey[:,:,None],0,64)
            albedo[s][:,:,3]=0
            spec[s][:,:,0]=255
            spec[s][:,:,1]=[160,180,188,0,150,0,0,175][tile]
            spec[s][:,:,2:]=0
    Image.fromarray(normals).save(HERE/'GGA2404_normalsTS_authoring.png')
    # mesh.fx ComputeNormal reads .ga, with G along binormal and A along
    # tangent. Opaque alpha=255 in the old RGB map produced invalid normals.
    normals[:,:,3]=normals[:,:,0]
    normals[:,:,0]=128
    normals[:,:,2]=255
    for kind,data in [('albedo',albedo),('specteam',spec),('normalsTS',normals)]:
        im=Image.fromarray(data);im.save(HERE/f'GGA2404_{kind}_source.png');save_dds(im,UNIT/f'GGA2404_{kind}.dds')

def curve(v,spread=0):return f'{{ XRange=1, Keys={{ {{ x=0, y={v}, z={spread} }} }} }}'

def effects():
    # Order from FAF GameColors.ArmyColors, checked against installed/upstream FAF.
    colors=['e80a0a','901427','FF873E','b76518','a79602','fafa00','9fd802','40bf40','2e8b57','2F4F4F','436eee','2929e1','5F01A7','9161ff','66ffcc','ffffff','616d7e','ff88ff','ff32ff']
    ramp=Image.new('RGBA',(64,256))
    for y in range(256):
        index=min(len(colors)-1,y*len(colors)//256)
        color=colors[index]
        rgb=tuple(int(color[i:i+2],16) for i in [0,2,4])
        for x in range(64):
            a=int(255*math.sin(math.pi*x/63)**.7)
            ramp.putpixel((x,y),(*rgb,a))
    # Power-of-two, uncompressed, no mip bleeding between the 19 army bands.
    ramp.save(MOD/'textures/particles/ball_army_ramp.dds')
    ramp.save(HERE/'ball_army_ramp_source.png')
    specs=[
        ('ball_othuy_arcs','electricity_08',4,38,.11,.87,.7,.18),
        ('ball_othuy_surface','electricity_09',2,26,.085,.72,.10,.13),
        ('ball_othuy_core','glow_02',1,16,.16,.54,0,.035),
        ('ball_othuy_haze','glow_02',1,8,.24,.88,.08,.15),
        ('ball_othuy_motes','electricity_08',4,20,.18,.17,.35,.28),
        ('ball_othuy_flash','electricity_08',4,12,.065,.64,0,.06),
        ('ball_impact','electricity_09',2,160,.13,.45,2,.1),
        ('ball_hit','electricity_09',2,90,.12,.24,.6,.08),
    ]
    for name,texture,strips,rate,life,size,speed,spread in specs:
        fields=dict(Lifetime='0.10' if name in ['ball_hit','ball_impact'] else '-1',Repeattime='1',
            Texture=repr('/textures/particles/'+texture+'.dds'),
            RampTexture=repr('/mods/Project Roc Unicorns/textures/particles/ball_army_ramp.dds'),
            Blendmode='3',TextureFramecount='1',TextureStripcount=str(strips),LODCutoff='350',
            LocalVelocity='false',LocalAcceleration='false',Gravity='false',Flat='false',
            AlignRotation='false',AlignToBone='false',InterpolateEmission='true',EmitIfVisible='true',CatchupEmit='false',
            EmitRateCurve=curve(rate),LifetimeCurve=curve(life,life*.15),VelocityCurve=curve(speed,speed*.3),
            SizeCurve=curve(0),StartSizeCurve=curve(size,size*.12),EndSizeCurve=curve(size*.2),
            InitialRotationCurve=curve(180,360),RotationRateCurve=curve(180,120),FrameRateCurve=curve(1),
            TextureSelectionCurve=curve(strips*.5,strips) if strips>1 else curve(0),
            RampSelectionCurve=curve((11-.5)/len(colors)),ResistanceCurve=curve(0))
        for axis in 'XYZ':
            fields[axis+'DirectionCurve']=curve(0,1)
            fields[axis+'PosCurve']=curve(0,spread)
            fields[axis+'AccelCurve']=curve(0)
        (MOD/f'effects/emitters/{name}_emit.bp').write_text('-- Othuy-style layers; stock textures referenced, not redistributed.\nEmitterBlueprint {\n'+''.join(f'    {k} = {v},\n' for k,v in fields.items())+'}\n')
    # Native Othuy beam texture, with per-army color set by the runtime helper.
    (MOD/'effects/emitters/ball_strike_beam_emit.bp').write_text('''BeamBlueprint {
    StartColor = { w=0, x=1, y=1, z=1 }, EndColor = { w=0, x=1, y=1, z=1 },
    LODCutoff = 400, Length = 1.5, Lifetime = 0.2, RepeatRate = 0.045,
    TextureName = '/textures/particles/electricity_beam_02.dds',
    Thickness = 0.55, UShift = 0, VShift = 0.4,
}
''')
    (HERE/'army_ramp_colors.json').write_text(json.dumps(colors,indent=2))

if __name__=='__main__':unit_maps();effects();print('GGA2404 materials and Othuy-style effects generated')
