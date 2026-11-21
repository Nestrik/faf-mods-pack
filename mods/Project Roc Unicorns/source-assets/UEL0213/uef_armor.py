"""Faceted armor castings, service hatches and vents for the Fourfold SCM."""
import math
import numpy as np
from PIL import Image, ImageDraw

def armor_detail(face, half_width, rear, front, top, wheel_index):
    def pad(origin, across, along, width, length, height, finish, bone, cut=.18):
        """An eight-sided casting with a recessed dark gasket and a bevel."""
        origin, across, along = map(np.array, (origin, across, along))
        normal = np.cross(across, along)
        outline = [(-1+cut,-1),(1-cut,-1),(1,-1+cut),(1,1-cut),
                   (1-cut,1),(-1+cut,1),(-1,1-cut),(-1,-1+cut)]
        def ring(factor, h):
            return [origin + across*(x*width*.5*factor) + along*(y*length*.5*factor)
                    + normal*h for x,y in outline]
        lower, waist, crown = ring(.96,0), ring(1,height*.32), ring(.88,height)
        for i in range(8):
            j=(i+1)%8
            outward = waist[i]+waist[j]-2*origin
            face([lower[i],lower[j],waist[j],waist[i]],outward,'dark',bone)
            face([waist[i],waist[j],crown[j],crown[i]],outward,'edge',bone)
        face(crown,normal,finish,bone)

    # Separate armor bays leave visible dark joints. Both broad faces read
    # from the RTS camera, one in transit and the other after deployment.
    for sign, surface in [(-1,rear),(1,front)]:
        for bay, y in enumerate((-.53,.30,1.14,2.00)):
            for side in (-1,1):
                pad((side*.315,y,surface),(sign,0,0),(0,1,0),
                    .49,.77,.049,'team' if bay in (1,3) else 'armor',1)
            pad((0,y,surface),(sign,0,0),(0,1,0),.14,.78,.072,'edge',1)
    for side in (-1,1):
        across=(0,0,-side)
        for bay,y in enumerate((-.51,.33,1.17,2.01)):
            center=(side*half_width,y,(rear+front)*.5)
            pad(center,across,(0,1,0),.99,.78,.044,'armor',1)
            pad((side*(half_width+.044),y,center[2]),across,(0,1,0),
                .68,.54,.023,'vent' if bay in (0,2) else 'team',1)
    # Metal ferrules catch the light around each open tube.
    for x in (-half_width/2,half_width/2):
        for z in (rear+half_width/2,rear+1.5*half_width):
            def ring(radius,h):
                return [(x+radius*math.cos(i*math.tau/24),top+h,
                         z+radius*math.sin(i*math.tau/24)) for i in range(24)]
            base,lip,inside=ring(.272,0),ring(.258,.027),ring(.235,.027)
            for i in range(24):
                j=(i+1)%24
                face([base[i],base[j],lip[j],lip[i]],(0,1,0),'edge',1)
                face([lip[i],lip[j],inside[j],inside[i]],(0,1,0),'armor',1)
                face([inside[i],inside[j],(inside[j][0],top,inside[j][2]),(inside[i][0],top,inside[i][2])],
                     (x-inside[i][0],0,z-inside[i][2]),'dark',1)
    for side in (-1,1):
        # Paired shoulder plates, armored fenders and the cabin air intakes.
        for z in (1.17,.55,-.62,-1.25):
            pad((side*.53,.64,z),(1,0,0),(0,0,-1),.27,.58,.10,'team',0)
        pad((side*.34,.99,1.22),(1,0,0),(0,0,-1),.30,.62,.105,'team',0)
        pad((side*.34,1.092,1.24),(1,0,0),(0,0,-1),.19,.35,.027,'vent',0)
        for i,z in enumerate((1.24,.70,-.60,-1.17)):
            pad((side*.82,.30,z),(0,0,-side),(0,1,0),.32,.32,.031,
                'armor',wheel_index(side,i),cut=.58)
    # Taper the cab brow down towards the bumper. The angled cheeks and
    # recessed optical strip are legible even when the vehicle is folded.
    for side in (-1,1):
        def mirrored(points):
            return [(side*x,y,z) for x,y,z in points]
        top_cheek=[(.02,1.045,1.53),(.40,1.015,1.49),(.49,.915,1.67),
                   (.38,.78,1.77),(.04,.78,1.81)]
        face(mirrored(top_cheek),(0,1,1),'team',0)
        face(mirrored([top_cheek[1],top_cheek[2],(.50,.58,1.68),(.47,.68,1.46)]),
             (side,0,0),'armor',0)
        face(mirrored([top_cheek[2],top_cheek[3],(.36,.60,1.8),(.50,.58,1.68)]),
             (side,0,1),'armor',0)
        face(mirrored([top_cheek[3],top_cheek[4],(.04,.61,1.84),(.36,.60,1.8)]),
             (0,0,1),'dark',0)
        face(mirrored([(.12,.731,1.825),(.33,.735,1.797),(.30,.70,1.806),(.12,.70,1.834)]),
             (0,0,1),'optic',0)
        face(mirrored([(.025,.61,1.85),(.385,.60,1.805),(.46,.53,1.775),
                       (.34,.455,1.83),(.025,.47,1.868)]),(0,0,1),'edge',0)
    pad((0,1.01,1.36),(1,0,0),(0,0,-1),.39,.55,.095,'armor',0)

def material_tiles(atlas,spec):
    # The procedural geometry uses the upper right atlas quadrant.
    rng=np.random.default_rng(213)
    for idx,(base,reflect,gloss,mask) in enumerate([
            ((65,77,94),68,72,0),((115,125,140),96,96,0),
            ((22,27,33),30,25,0),((56,68,89),86,88,120),
            ((25,31,40),46,60,0),((86,172,208),75,100,0)]):
        x=512+(idx%2)*256; y=(idx//2)*128
        noise=rng.normal(0,2,(128,256,1))
        tile=Image.fromarray(np.clip(np.array(base)+noise,0,255).astype('uint8'))
        draw=ImageDraw.Draw(tile)
        if idx==4:
            for row in range(8,120,16):
                draw.rectangle((10,row,246,row+10),fill=(13,18,24))
                draw.line((12,row+2,244,row+2),fill=(101,111,124),width=2)
        else:
            draw.line([(8,106),(29,116),(227,116),(248,105)], fill=tuple(v//2 for v in base),width=3)
            for px in (14,241):
                for py in (12,110):
                    draw.ellipse((px-3,py-3,px+3,py+3),fill=(27,32,39))
                    draw.line((px-1,py-1,px+1,py-1),fill=(126,133,142))
        atlas.paste(tile,(x,y))
        spec.paste((reflect,gloss,200 if idx==5 else 0,mask),(x,y,x+256,y+128))
