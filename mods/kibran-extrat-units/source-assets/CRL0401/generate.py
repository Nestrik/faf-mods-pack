"""Original Cybran-inspired eight-wheel engineering platform; Y up, +Z forward."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
from model_geometry import Mesh, render_scm, load_scm, load_dds_mip
from supcom_binary import write_scm, write_sca, save_dds_dxt5

HERE = Path(__file__).resolve().parent
UNIT = HERE.parents[1] / 'units' / 'CRL0401'
LINKS = 24
HALF_LENGTH = .95
TRACK_RADIUS = .32
TRACK_Y = .36
TRACK_LENGTH = 4 * HALF_LENGTH + 2 * math.pi * TRACK_RADIUS
NAMES = (['CRL0401', 'BuildPoint'] +
         [f'Track_{side}_{i:02}' for side in ('L', 'R') for i in range(LINKS)] +
         [f'Roller_{side}_{i}' for side in ('L', 'R') for i in range(4)])
PARENTS = [-1] + [0] * (len(NAMES) - 1)

def path(distance):
    """Closed belt path; lower run moves backwards for forward travel."""
    d=distance % TRACK_LENGTH; a=2*HALF_LENGTH; r=TRACK_RADIUS
    if d < a:
        return (TRACK_Y-r, HALF_LENGTH-d, 0., -1.)
    d-=a
    if d < math.pi*r:
        t=d/r
        return (TRACK_Y-r*math.cos(t), -HALF_LENGTH-r*math.sin(t), math.sin(t), -math.cos(t))
    d-=math.pi*r
    if d < a:
        return (TRACK_Y+r, -HALF_LENGTH+d, 0., 1.)
    t=(d-a)/r
    return (TRACK_Y+r*math.cos(t), HALF_LENGTH+r*math.sin(t), -math.sin(t), math.cos(t))

def pivots():
    out=[(0,0,0),(0,2.72,0)]
    for side in (-1,1):
        for i in range(LINKS):
            y,z,_,_=path(i*TRACK_LENGTH/LINKS)
            out.append((side*1.19,y,z))
    for side in (-1,1):
        for z in (-.90,-.30,.30,.90): out.append((side*1.19,TRACK_Y,z))
    return out

def beam(m, start, end, width, height, mat='armor'):
    a,b=np.asarray(start,float),np.asarray(end,float)
    axis=b-a; axis/=np.linalg.norm(axis)
    ref=np.array((0.,1.,0.)) if abs(axis[1]) < .9 else np.array((0.,0.,1.))
    u=np.cross(axis,ref); u/=np.linalg.norm(u); v=np.cross(axis,u)
    rings=[[p+u*width*s+v*height*t for s,t in ((-1,-1),(1,-1),(1,1),(-1,1))] for p in (a,b)]
    m.loft(rings,[a,b],material=mat)

def block(m,x,y,z,sx,sy,sz,mat='armor'):
    rings=[[(x-sx/2,y-sy/2,z+q*sz/2),(x+sx/2,y-sy/2,z+q*sz/2),
            (x+sx/2,y+sy/2,z+q*sz/2),(x-sx/2,y+sy/2,z+q*sz/2)] for q in (-1,1)]
    m.loft(rings,[(x,y,z-sz/2),(x,y,z+sz/2)],material=mat)

def hull(m,sections,mat='armor'):
    # Each cross-section is an octagonal chamfered shell: z, half-width, bottom, top.
    rings=[]; centers=[]
    for z,w,lo,hi in sections:
        c=min(w*.23,(hi-lo)*.28)
        rings.append([(-w+c,lo,z),(w-c,lo,z),(w,lo+c,z),(w,hi-c,z),
                      (w-c,hi,z),(-w+c,hi,z),(-w,hi-c,z),(-w,lo+c,z)])
        centers.append((0,(lo+hi)/2,z))
    m.loft(rings,centers,material=mat)

def wheel(m,side,z,detail,bone):
    x=side*1.19; y=TRACK_Y; n=detail
    rings=[]; centers=[]
    for dx,r in [(-.15,.195),(-.12,.23),(.12,.23),(.15,.195)]:
        rings.append([(x+dx,y+r*math.cos(2*math.pi*i/n),z+r*math.sin(2*math.pi*i/n)) for i in range(n)])
        centers.append((x+dx,y,z))
    m.loft(rings,centers,bone=bone,material='joint')
    face=x+side*.155
    n2=max(8,detail//2)
    rings=[]; centers=[]
    for dx,r in [(0,.18),(side*.025,.18),(side*.03,.08)]:
        rings.append([(face+dx,y+r*math.cos(2*math.pi*i/n2),z+r*math.sin(2*math.pi*i/n2)) for i in range(n2)])
        centers.append((face+dx,y,z))
    m.loft(rings,centers,bone=bone,material='steel')
    for i in range(4):
        a=2*math.pi*i/4; b=a+.18
        pts=[(face+side*.034,y+r*math.cos(t),z+r*math.sin(t)) for r,t in ((.08,a),(.18,a),(.18,b),(.08,b))]
        m.face(pts,bone=bone,material='edge',outward=(side,0,0))

def track(m,side,detail):
    x=side*1.19
    # Solid continuous belt underneath the independently animated cleats.
    sections=[]; centers=[]
    count=40 if detail >= 16 else 24
    for i in range(count):
        y,z,dy,dz=path(i*TRACK_LENGTH/count)
        ny,nz=dz,-dy
        centers.append((x,y,z))
        sections.append([(x+sx*.21,y+ny*t,z+nz*t) for sx,t in ((-1,-.035),(1,-.035),(1,.035),(-1,.035))])
    m.loft(sections,centers,material='joint',loop=True)
    sideindex=0 if side < 0 else 1
    for i in range(LINKS):
        y,z,dy,dz=path(i*TRACK_LENGTH/LINKS); ny,nz=dz,-dy
        center=np.array((x,y,z)); tangent=np.array((0,dy,dz)); normal=np.array((0,ny,nz))
        # Center just outside the belt; each visible block has its own bone.
        center+=normal*.048
        rings=[]
        for sx in (-1,1):
            rings.append([center+np.array((sx*.218,0,0))+tangent*t+normal*n for t,n in
                          ((-.080,-.014),(.080,-.014),(.080,.014),(-.080,.014))])
        m.loft(rings,[center+(-.218,0,0),center+(.218,0,0)],bone=2+sideindex*LINKS+i,material='steel')

def tower(m,detail):
    # Squat base, then a tall swept, chamfered spire in the Hive's style.
    sections=[(.91,.68,.70,.03),(1.15,.64,.62,.00),(1.55,.52,.46,-.07),
              (2.08,.34,.31,-.20),(2.47,.13,.17,-.30),(2.57,.025,.055,-.32)]
    rings=[]; centers=[]
    for y,w,d,z in sections:
        c=min(w,d)*.22
        rings.append([(-w+c,y,z-d),(w-c,y,z-d),(w,y,z-d+c),(w,y,z+d-c),
                      (w-c,y,z+d),(-w+c,y,z+d),(-w,y,z+d-c),(-w,y,z-d+c)])
        centers.append((0,y,z))
    m.loft(rings,centers,material='dark')
    # Sloping front face with three raised triangular panels, separated by armour bands.
    # Front plane interpolates the front edge of the tower sections.
    points=[(1.17,.621),(1.55,.39),(2.08,.11),(2.46,-.13)]
    for i in range(3):
        y0,z0=points[i]; y1,z1=points[i+1]
        mid=y0+(y1-y0)*.13; top=y1-(y1-y0)*.12
        def front(y): return z0+(z1-z0)*(y-y0)/(y1-y0)+.012
        w=(.43,.32,.19)[i]
        # Each emblem sits on its own raised, dark trapezoidal armour cassette.
        lower=mid-.025; upper=top+.026
        panel=[(-w*1.16,lower,front(lower)-.005),(w*1.16,lower,front(lower)-.005),
               (w*.79,upper,front(upper)-.005),(-w*.79,upper,front(upper)-.005)]
        m.face(panel,material='dark',outward=(0,.3,1))
        for j in range(4): beam(m,panel[j],panel[(j+1)%4],.014,.010,'armor')
        vertices=[(-w,mid,front(mid)),(w,mid,front(mid)),(0,top,front(top))]
        m.face(vertices,material='steel',outward=(0,.3,1))
        inset=[(-w*.68,mid+.035,front(mid+.035)+.006),(w*.68,mid+.035,front(mid+.035)+.006),(0,top-.045,front(top-.045)+.006)]
        # This face uses a dedicated painted emblem tile. Only its fine rune
        # and frame are in the team mask, while the backing remains black metal.
        m.face(inset,material='crystal',outward=(0,.3,1),uvs=[(.05,.95),(.95,.95),(.5,.05)])
        for j in range(3): beam(m,vertices[j],vertices[(j+1)%3],.015,.012,'edge')
        if detail >= 16:
            # The inner frame and split prongs echo the inset details of Hive.
            # Stepped armor surrounding each emblem, inspired by the Hive's
            # layered chevrons rather than a bright, solid triangle.
            for scale in (1.09,1.19):
                yy=mid-.015*(scale-1)*5
                frame=[(-w*scale,yy,front(yy)-.006),(0,top+.025*scale,front(top+.025*scale)-.006),
                       (w*scale,yy,front(yy)-.006)]
                beam(m,frame[0],frame[1],.012,.009,'armor')
                beam(m,frame[1],frame[2],.012,.009,'armor')
    # Large triangular side buttresses and braces make the tower read as Hive.
    for side in (-1,1):
        outer=[(side*.70,1.04,-.53),(side*.70,1.04,.48),(side*.43,1.83,-.19)]
        m.face(outer,material='steel',outward=(side,0,0))
        inner=[(side*.711,1.12,-.39),(side*.711,1.12,.31),(side*.49,1.66,-.17)]
        m.face(inner,material='team',outward=(side,0,0))
        for j in range(3): beam(m,outer[j],outer[(j+1)%3],.03,.025,'edge')
        beam(m,(side*.56,1.18,.49),(side*.115,2.48,-.12),.035,.025,'edge')
        beam(m,(side*.61,1.12,-.5),(side*.13,2.42,-.43),.035,.025,'armor')
        if detail >= 16:
            for y in (1.28,1.42,1.56,1.70):
                z=.59-(y-1.17)*.6
                beam(m,(side*.38,y,z),(side*.47,y,z-.02),.01,.01,'crystal')
            for z in (-.34,-.22,-.10,.02,.14):
                beam(m,(side*.695,1.08,z),(side*.61,1.35,z-.04),.011,.01,'edge')
            # Recessed seams and narrow vent slits across the side armour.
            for y,z0,z1,x in [(1.34,-.43,.10,.63),(1.53,-.43,.02,.56),(1.76,-.45,-.05,.47)]:
                beam(m,(side*x,y,z0),(side*x,y,z1),.009,.007,'joint')
            for y in (1.14,1.18,1.22,1.26):
                beam(m,(side*.704,y,.30),(side*.68,y+.025,.36),.008,.006,'joint')
    # A narrow player-coloured tip, as on the fully upgraded Hive.
    y0,y1=2.465,2.565
    m.face([(-.08,y0,-.105),(.08,y0,-.105),(0,y1,-.235)],material='team',outward=(0,.3,1))

def model(detail):
    m=Mesh(detail)
    hull(m,[(-1.38,.61,.39,.71),(-1.15,.94,.35,.85),(.83,.94,.35,.83),(1.30,.66,.38,.67),(1.40,.36,.43,.59)],'dark')
    hull(m,[(-1.22,.75,.70,.89),(-.85,.83,.72,1.00),(.70,.81,.72,1.00),(1.18,.54,.68,.87)],'armor')
    for side in (-1,1):
        sideindex=0 if side < 0 else 1
        for i,z in enumerate((-.90,-.30,.30,.90)):
            wheel(m,side,z,detail,2+2*LINKS+sideindex*4+i)
        track(m,side,detail)
        beam(m,(side*.93,.71,-1.22),(side*.93,.71,1.18),.055,.035,'steel')
        beam(m,(side*.92,.87,-1.15),(side*.92,.87,1.10),.035,.02,'team')
        for z in (-.68,.68):
            beam(m,(side*.87,.62,z-.28),(side*1.02,.74,z+.24),.06,.04,'dark')
            block(m,side*.83,.91,z,.22,.07,.36,'edge')
            if detail >= 16:
                beam(m,(side*.90,.78,z-.25),(side*.98,.63,z+.22),.035,.035,'steel')
                beam(m,(side*.90,.78,z-.25),(side*.95,.67,z+.06),.017,.017,'edge')
        beam(m,(side*.66,.83,1.03),(side*.28,.65,1.36),.065,.05,'steel')
        beam(m,(side*.63,.86,-1.08),(side*.80,.99,-1.31),.06,.035,'edge')
        if detail >= 16:
            for z in (-.99,-.33,.33,.99):
                beam(m,(side*.98,.92,z-.24),(side*.98,.92,z+.24),.038,.025,'dark')
                beam(m,(side*.98,.96,z-.20),(side*.98,.96,z+.20),.012,.01,'steel')
            for x in (.26,.37,.48):
                beam(m,(side*x,.88,1.05),(side*(x-.08),.76,1.29),.014,.012,'edge')
            block(m,side*.54,.72,1.28,.15,.07,.05,'lens')
    block(m,0,.94,-1.04,1.05,.16,.38,'dark')
    for x in (-.32,-.16,0,.16,.32):
        block(m,x,1.035,-1.05,.045,.025,.28,'edge')
    tower_first=len(m.vertices)
    tower(m,detail)
    # Raise only the station, preserving the track skeleton and the 3x3 base.
    stretch=1.16
    for i in range(tower_first,len(m.vertices)):
        v=list(m.vertices[i]); v[1]=.91+(v[1]-.91)*stretch
        normal=np.array((v[3],v[4]/stretch,v[5])); normal/=np.linalg.norm(normal)
        tangent=np.array((v[6],v[7]*stretch,v[8])); tangent-=normal*np.dot(normal,tangent); tangent/=np.linalg.norm(tangent)
        bitangent=np.cross(normal,tangent)
        if np.dot(bitangent,np.array(v[9:12])) < 0: bitangent=-bitangent
        v[3:6]=normal; v[6:9]=tangent; v[9:12]=bitangent
        m.vertices[i]=tuple(v)
    return m

def animation():
    bind=pivots(); frames=[]; count=65
    duration=TRACK_LENGTH/2.0  # top speed 2 game units/s
    for frame in range(count):
        progress=frame/(count-1)
        poses=[(bind[0],(1,0,0,0)),(bind[1],(1,0,0,0))]
        for side in (-1,1):
            for i in range(LINKS):
                start=i*TRACK_LENGTH/LINKS
                y0,z0,dy0,dz0=path(start)
                y,z,dy,dz=path(start+progress*TRACK_LENGTH)
                angle=math.atan2(dz,dy)-math.atan2(dz0,dy0)
                poses.append(((side*1.19,y,z),(math.cos(angle/2),math.sin(angle/2),0,0)))
        # Rollers spin at belt speed; their vertices use their own bind pivots.
        angle=progress*TRACK_LENGTH/.23
        for j in range(8): poses.append((bind[2+2*LINKS+j],(math.cos(angle/2),math.sin(angle/2),0,0)))
        frames.append(poses)
    # The belt returns to its exact initial position. Rollers use a whole number
    # of turns so their last frame also joins the first without a visible jump.
    turns=round(TRACK_LENGTH/(2*math.pi*.23))
    for f,poses in enumerate(frames):
        angle=2*math.pi*turns*f/(count-1)
        for j in range(8): poses[2+2*LINKS+j]=(bind[2+2*LINKS+j],(math.cos(angle/2),math.sin(angle/2),0,0))
    # Keep adjacent quaternion representations on the same hemisphere.
    for bone in range(2,len(NAMES)):
        for frame in range(1,count):
            p,q=frames[frame][bone]; previous=frames[frame-1][bone][1]
            if sum(a*b for a,b in zip(q,previous)) < 0:
                frames[frame][bone]=(p,tuple(-a for a in q))
    # The construction effect point is deliberately excluded from this clip.
    write_sca(UNIT/'CRL0401_tracks.sca',[NAMES[0]]+NAMES[2:],[-1]+[0]*(len(NAMES)-2),
              [[poses[0]]+poses[2:] for poses in frames],duration)

def textures():
    colors=[(49,52,55),(19,21,24),(70,73,77),(57,60,63),
            (72,75,78),(19,21,24),(195,32,22),(25,27,29)]
    al=Image.new('RGBA',(512,256)); spec=Image.new('RGBA',al.size); normal=Image.new('RGBA',al.size,(128,128,255,128))
    da,ds=ImageDraw.Draw(al),ImageDraw.Draw(spec)
    for i,c in enumerate(colors):
        rect=((i%4)*128,(i//4)*128,(i%4+1)*128-1,(i//4+1)*128-1)
        da.rectangle(rect,fill=(*c,0))
        ds.rectangle(rect,fill=(45 if i!=7 else 20,78 if i!=7 else 42,55 if i==6 else 0,255 if i==4 else 0))
    # Emblem tile (material 'crystal'): mask is in SpecTeam.A for Unit shader.
    # Coordinates follow atlas_uv's inset so the image fits the triangular face.
    ox,oy=128,128
    def uv(x,y): return (round(ox+128*(.09+.82*x)),round(oy+128*(.045+.91*y)))
    def line(points,fill,width,drawer): drawer.line([uv(*p) for p in points],fill=fill,width=width,joint='curve')
    triangle=[(.08,.92),(.92,.92),(.5,.08),(.08,.92)]
    line(triangle,(60,63,67,0),4,da)
    line(triangle,(65,85,0,210),3,ds)
    # Angular Y/arrow emblem, negative space and small forked shoulders.
    emblem=[[(.50,.20),(.50,.46),(.30,.80)],[(.50,.46),(.70,.80)],[(.34,.80),(.66,.80)],
            [(.27,.68),(.34,.68),(.39,.57)],[(.73,.68),(.66,.68),(.61,.57)],
            [(.39,.54),(.33,.46),(.36,.40)],[(.61,.54),(.67,.46),(.64,.40)]]
    for stroke in emblem:
        line(stroke,(9,10,12,0),7,da); line(stroke,(55,78,0,235),4,ds)
    # Thin panel divisions and ventilation grooves on neutral steel tiles.
    for tile in (0,1,2,3,7):
        x0=(tile%4)*128; y0=(tile//4)*128
        for x in (18,22,105,109): da.line((x0+x,y0+17,x0+x,y0+111),fill=(27,29,31,0),width=1)
        for y in (18,22,105,109): da.line((x0+17,y0+y,x0+111,y0+y),fill=(30,32,34,0),width=1)
    # Small independent-channel surface variation survives mip generation and
    # avoids relying on alpha transparency for the material maps.
    pixels=np.asarray(al).copy(); rng=np.random.default_rng(304309)
    noise=rng.integers(-3,4,(256,512,1),dtype=np.int16)
    pixels[:,:,:3]=np.clip(pixels[:,:,:3].astype(np.int16)+noise,0,255).astype(np.uint8)
    al=Image.fromarray(pixels,'RGBA')
    for name,img in [('albedo',al),('specteam',spec),('normalsTS',normal)]:
        img.save(HERE / ('CRL0401_'+name+'.png'))
        save_dds_dxt5(img,UNIT/('CRL0401_'+name+'.dds'),independent_channels=True)

if __name__ == '__main__':
    UNIT.mkdir(parents=True,exist_ok=True)
    for lod,detail in [(0,24),(1,8)]:
        mesh=model(detail)
        write_scm(mesh,UNIT/f'CRL0401_lod{lod}.scm',NAMES,PARENTS,pivots())
        v,f=load_scm(UNIT/f'CRL0401_lod{lod}.scm')
        print('LOD',lod,'vertices',len(v),'triangles',len(f),'bounds',v[:,:3].min(axis=0),v[:,:3].max(axis=0))
    textures()
    animation()
    for name,a,e in [('front',0,12),('side',90,12),('top',0,85),('perspective',35,28)]:
        render_scm(UNIT/'CRL0401_lod0.scm',HERE,HERE/(name+'.png'),a,e,player=(.95,.06,.78),size=640)
    render_scm(UNIT/'CRL0401_lod1.scm',HERE,HERE/'lod1.png',35,28,player=(.05,.35,.95),size=480,texture_mip=2)
