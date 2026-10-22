"""Layered, flowing Seraphim foundation; executed in builder namespace."""
lathe('Scalloped undercarriage',[(.03,.025),(.70,.025),(1.10,.07),(1.13,.12),(.90,.23),(.03,.25)],0,n=72,lobes=.16)
lathe('Recessed crown core',[(.03,.14),(.73,.18),(.65,.46),(.45,.85),(.39,1.04),(.03,1.04)],4,n=72,lobes=.13)
lathe('Tri-lobed polished crown',[(.42,.84),(.60,.91),(.59,1.015),(.49,1.08),(.40,1.045)],1,n=72,lobes=.14)
lathe('Crown silver lip',[(.40,1.035),(.48,1.065),(.49,1.083),(.41,1.068)],2,n=72,lobes=.14)
lathe('Crown energy well',[(.01,1.03),(.36,1.03),(.39,1.055),(.35,1.065),(.01,1.065)],4,n=60,lobes=.12)
lathe('Crown glow circuit',[(.365,1.05),(.38,1.056),(.38,1.064),(.365,1.068)],5,n=60,lobes=.10)
profile=[(.22,.91,.14),(.42,1.00,.26),(.65,.83,.41),(.91,.56,.55),(1.18,.31,.56),(1.49,.135,.38),(1.76,.055,.18),(1.94,.025,.004)]
cross=[(-1,-.04),(-.94,.035),(-.70,.13),(-.40,.17),(0,.22),(.40,.17),(.70,.13),(.94,.035),(1,-.04),(.50,-.13),(0,-.16),(-.50,-.13)]
def prof(t):
    # Catmull-Rom interpolation softens the shell without a melted outline.
    q=max(0,min(6.999999,t));j=int(q);u=q-j
    a=Vector(profile[max(0,j-1)]);b=Vector(profile[j]);c=Vector(profile[j+1]);d=Vector(profile[min(7,j+2)])
    v=.5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
    v.z=max(.004,v.z);return v
def rich_petal(index,angle,secondary=False):
    radial=Vector((cos(angle),sin(angle),0));side=Vector((-sin(angle),cos(angle),0))
    rs=.94 if secondary else 1.;zs=.79 if secondary else 1.;ws=.88 if secondary else 1.
    def surface(t,s,extra=0):
        r,z,w=prof(t);w*=ws
        z*=zs
        # Crown stays broad; the outer blade becomes thin and pointed.
        thick=(.48+.52*sin(pi*min(1,t/7)))*zs
        a=abs(s)
        if a<.4:dz=.22-.05*a/.4
        elif a<.7:dz=.17-.04*(a-.4)/.3
        else:dz=.13-.17*(a-.7)/.3
        return radial*(r*rs)+side*(s*w)+Vector((0,0,max(.026,z+dz*thick+extra)))
    vs=[];uv=[];n=22
    for j in range(n+1):
        t=7*j/n;r,z,w=prof(t);thick=(.48+.52*sin(pi*t/7))*zs
        for k,(s,dz) in enumerate(cross):
            vs.append(radial*(r*rs)+side*(s*w*ws)+Vector((0,0,max(.026,z*zs+dz*thick))))
            uv.append((j/n,k/11))
    fs=[(j*12+k,j*12+(k+1)%12,(j+1)*12+(k+1)%12,(j+1)*12+k) for j in range(n) for k in range(12)]
    fs += [tuple(reversed(range(12))),tuple(n*12+k for k in range(12))]
    ob=mesh(f'Rich layered foundation / petal {index}',vs,fs,7 if secondary else 1,smooth=True,uv=uv);ob['foundation_petal']=True;ob['secondary_petal']=secondary
    for s in [-.95,-.69,.69,.95]:
        pts=[surface(.30+6.5*j/16,s,.009) for j in range(17)]
        tube(f'Swept silver shoulder {index} / {s}',pts,.013 if abs(s)>.8 else .018,2)
    # Long black slits separate the overlapping armor lobes.
    for s in [-.81,.81]:
        pts=[surface(.75+4.8*j/14,s,.008) for j in range(15)]
        tube(f'Deep armor flute {index} / {s}',pts,.031,4)
    # A narrower bright split blade rises above each primary shoulder.
    if not secondary:
        vv=[]
        for j in range(17):
            t=.48+4.8*j/16;span=.13*sin(pi*j/16)**.5+.002
            for s in [-span,span]:vv.append(surface(t,s,.027))
        ff=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(16)]
        ff=[tuple(reversed(face)) for face in ff]
        mesh(f'Raised central crown blade {index}',vv,ff,2,smooth=True)
    # Linked nested ellipses, projected onto the actual curved petal skin.
    for q,t in enumerate([1.65,3.35,5.05]):
        for r in [1.,.68]:
            pts=[surface(t+.59*r*cos(2*pi*k/40),.37*r*sin(2*pi*k/40),.037) for k in range(41)]
            tube(f'Crop circle petal {index}/{q}/{r}',pts,.0075 if r==1 else .0045,3,sides=4)
        for flank in [-1,1]:
            pts=[surface(t+.15*cos(2*pi*k/20),flank*.50+.08*sin(2*pi*k/20),.025) for k in range(21)]
            tube(f'Orbital node petal {index}/{q}/{flank}',pts,.0045,3,sides=4)
        if q<2:
            tube(f'Petal circle link {index}/{q}',[surface(t+.59+.52*k/6,0,.037) for k in range(7)],.0055,3)
    for sign in [-1,1]:
        pts=[surface(.55+2.4*j/12,sign*.35,.023) for j in range(13)]
        tube(f'Living energy vein {index} / {sign}',pts,.010,5)
for i,a in enumerate([-150,-30,90]):rich_petal(i+1,math.radians(a))
for i,a in enumerate([-90,30,150]):rich_petal(i+4,math.radians(a),True)
# Six independent crown ribs flow from the top into the overlapping leaves.
for i in range(6):
    a=2*pi*i/6+pi/6;radial=Vector((cos(a),sin(a),0));side=Vector((-sin(a),cos(a),0))
    pts=[radial*r+Vector((0,0,z)) for r,z in [(.40,1.09),(.52,1.10),(.60,.98),(.67,.79),(.78,.58),(.90,.44)]]
    tube(f'Crown sculptural rib {i}',pts,.036,2,sides=6)
    p=radial*.535+Vector((0,0,1.05))
    tube(f'Team crown orbital seal {i}',[p+side*.045*cos(2*pi*k/24)+radial*.07*sin(2*pi*k/24)+Vector((0,0,.04)) for k in range(25)],.007,3,sides=4)
