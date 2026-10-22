"""Cut genuine holes and integrate coaxial, illuminated annuli into both nacelles.
Coordinates here are after the 90-degree inward roll and before global gun lift.
"""
import bmesh
RING_Y=-.16
RING_Z=1.80
RING_X=.80
HOLE_RADIUS=.385

# One cutter through both hulls ensures that the holes share a single axis.
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=HOLE_RADIUS,depth=4,
    location=(0,RING_Y,RING_Z),rotation=(0,pi/2,0))
cutter=bpy.context.object;cutter.name='BUILD ONLY / coaxial aperture cutter'
for m in materials:cutter.data.materials.append(m)
for poly in cutter.data.polygons:poly.material_index=1
for ob in list(parts):
    if ob['rig_bone'] not in ['GondolaL','GondolaR']:continue
    if ob.get('main_gondola'):
        bpy.context.view_layer.objects.active=ob
        mod=ob.modifiers.new('Genuine through-ring opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        ob['preserve_aperture']=True
    else:
        # Existing ornaments and open surface panels must not bridge the opening.
        # The wide new annulus conceals the trimmed boundary of these thin overlays.
        bm=bmesh.new();bm.from_mesh(ob.data)
        erase=[f for f in bm.faces if any((v.co.y-RING_Y)**2+(v.co.z-RING_Z)**2<.42**2 for v in f.verts)]
        bmesh.ops.delete(bm,geom=erase,context='FACES')
        loose=[v for v in bm.verts if not v.link_faces]
        if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
        bm.to_mesh(ob.data);bm.free();ob.data.update()
    if 'upper recessed panel' in ob.name:
        # Change both the material and atlas coordinates: game emission is data-map driven.
        for poly in ob.data.polygons:poly.material_index=5
        for loop in ob.data.uv_layers.active.data:loop.uv.x+=.25
        ob['illuminated_inner_surface']=True
bpy.data.objects.remove(cutter,do_unlink=True)

def ring_band(name,sign,profile,mat):
    n=64;vs=[];uv=[];bone='GondolaL' if sign<0 else 'GondolaR'
    for j,(r,axial) in enumerate(profile):
        for k in range(n+1):
            a=2*pi*k/n
            vs.append((sign*(RING_X+axial),RING_Y+r*cos(a),RING_Z+r*sin(a)))
            uv.append((k/n,j/max(1,len(profile)-1)))
    fs=[(j*(n+1)+k,j*(n+1)+k+1,(j+1)*(n+1)+k+1,(j+1)*(n+1)+k) for j in range(len(profile)-1) for k in range(n)]
    if mat==5 and sign>0:
        fs=[tuple(reversed(face)) for face in fs]
    ob=mesh(name,vs,fs,mat,bone,True,uv);ob['preserve_aperture']=True
    return ob

for sign in [-1,1]:
    bone='GondolaL' if sign<0 else 'GondolaR'
    # A light radial band, with slightly deeper axial metal section.
    profile=[(.385,-.05),(.393,-.085),(.545,-.09),(.57,-.07),(.575,0),
             (.57,.07),(.545,.09),(.393,.085),(.385,.05),(.385,-.05)]
    rim=ring_band(f'Through-ring metal shell {sign}',sign,profile,1)
    rim['through_ring']=True;rim['axis_center']=(sign*RING_X,RING_Y,RING_Z)
    rim['clear_radius']=.382;rim['radial_band_width']=.190;rim['axial_depth']=.18
    # Army-coloured lining follows only the inner cylindrical rim wall.
    # It never spans the aperture. Radius .383 leaves .766 clear diameter.
    lining=ring_band(f'Army-coloured luminous inner ring wall {sign}',sign,
        [(.383,-.050),(.383,.050)],5)
    lining['inner_ring_glow']=True
    for axial in [-.070,.070]:
        pts=[(sign*(RING_X+axial),RING_Y+.390*cos(2*pi*k/64),RING_Z+.390*sin(2*pi*k/64)) for k in range(65)]
        edge=tube(f'Thin ring light trace {sign} / {axial}',pts,.003,5,bone,4)
        edge['ring_edge_light']=True
    for axial,r in [(-.084,.550),(.084,.550)]:
        pts=[(sign*(RING_X+axial),RING_Y+r*cos(2*pi*k/64),RING_Z+r*sin(2*pi*k/64)) for k in range(65)]
        tube(f'Fine ring bevel {sign} / {axial}',pts,.004,2,bone,4)
    # Crop-circle seals on the outer face; paired curved tracks around the rim.
    for j in range(12):
        a=2*pi*j/12
        for r in [.039,.022]:
            pts=[]
            for k in range(25):
                u=2*pi*k/24;rr=.474+r*cos(u);aa=a+r/.474*sin(u)
                pts.append((sign*(RING_X+.098),RING_Y+rr*cos(aa),RING_Z+rr*sin(aa)))
            tube(f'Ring orbital seal {sign}/{j}/{r}',pts,.0035,3,bone,4)
    for rr in [.420,.529]:
        pts=[(sign*(RING_X+.098),RING_Y+rr*cos(2*pi*k/96),RING_Z+rr*sin(2*pi*k/96)) for k in range(97)]
        tube(f'Ring paired orbit {sign}/{rr}',pts,.0035,3,bone,4)
    for axial in [-.036,.036]:
        pts=[(sign*(RING_X+axial),RING_Y+.580*cos(2*pi*k/96),RING_Z+.580*sin(2*pi*k/96)) for k in range(97)]
        tube(f'Outer ring track {sign}/{axial}',pts,.0035,3,bone,4)
    # More engraving on the outward-facing hull keel, fore and aft of the ring.
    origin=Vector((sign*.64,0,1.8));rot=Matrix.Rotation(-sign*pi/2,3,'Y')
    def outer_point(t,s,lift=.012):
        y,w,z=hull_values(t);fade=.08+.92*sin(pi*t)**.5
        # Follow the original keel cross-section before applying the inward roll.
        depth=-.39+.04*abs(s)/.43
        return origin+rot@(Vector((sign*.64+s*w,y,z+depth*fade-lift))-origin)
    for j,t in enumerate([.135,.815]):
        for r in [1.,.66]:
            pts=[outer_point(t+.066*r*cos(2*pi*k/40),.31*r*sin(2*pi*k/40),.016) for k in range(41)]
            tube(f'Hull nested orbital seal {sign}/{j}/{r}',pts,.007 if r==1 else .004,3,bone,4)
        for direction in [-1,1]:
            tt=t+direction*.087
            pts=[outer_point(tt+.012*cos(2*pi*k/20),.09*sin(2*pi*k/20),.016) for k in range(21)]
            tube(f'Hull satellite {sign}/{j}/{direction}',pts,.004,3,bone,4)
    for start,span in [(.07,.11),(.72,.22)]:
        for side in [-1,1]:
            pts=[outer_point(start+span*k/16,side*.37,.011) for k in range(17)]
            tube(f'Team long hull circuit {sign} / {start} / {side}',pts,.007,3,bone,4)

# Empty overlay objects, if any, are removed before export and rig binding.
for ob in list(parts):
    if len(ob.data.polygons)==0:
        parts.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
