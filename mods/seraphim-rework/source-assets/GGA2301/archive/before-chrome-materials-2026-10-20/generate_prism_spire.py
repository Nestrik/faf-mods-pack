"""Rebuild GGA2301's reference-shaped mesh, rig, animations and material atlas.

Requires numpy and Pillow. Run this file with Python; outputs stay in this mod.
The previous working model is kept in archive/before-reference-rebuild-2026-10-20.
"""
from pathlib import Path
import math

from prism_reference_model import FIN_ANGLES, build_mesh, export_obj, make_previews, make_textures
from supcom_binary import save_dds_dxt5, write_sca, write_scm


ASSET_DIR=Path(__file__).resolve().parent
ROOT=ASSET_DIR.parents[1]
UNIT=ROOT/"units"/"GGA2301"
SCALE=.06
BONENAMES=["GGA2301","Turret","Turret_Barrel","Turret_Muzzle","Halo","FinLeft","FinRight","FinRear"]
PARENTS=[-1,0,1,2,0,0,0,0]
PIVOTS=[(0,0,0),(0,22,0),(0,0,0),(0,0,6.65),(0,21.5,0)] + [
    (7*math.cos(a),8,7*math.sin(a)) for a in FIN_ANGLES]


def quaternion(axis,angle):
    return (math.cos(angle/2),*(math.sin(angle/2)*c for c in axis))


def animations():
    # Only decorative bones are keyed. The engine owns yaw, pitch and muzzle.
    # This matches the exporter's support for exporting selected keyed bones.
    selected=(0,4,5,6,7)
    names=[BONENAMES[i] for i in selected]
    parents=[-1,0,0,0,0]
    activation=[]
    for frame in range(31):
        t=frame/30
        eased=t*t*(3-2*t)
        transforms=[]
        for bone in selected:
            position=PIVOTS[bone]
            rotation=(1,0,0,0)
            if bone>=5:
                a=FIN_ANGLES[bone-5]
                rotation=quaternion((-math.sin(a),0,math.cos(a)),math.radians(5)*(1-eased))
            transforms.append((position,rotation))
        activation.append(transforms)
    write_sca(UNIT/"GGA2301_activate.sca",names,parents,activation,1.0)
    idle=[]
    for frame in range(121):
        t=frame/120
        transforms=[]
        for bone in selected:
            position=PIVOTS[bone]
            rotation=(1,0,0,0)
            if bone==4:
                position=(position[0],position[1]+.12*math.sin(2*math.pi*t),position[2])
                rotation=quaternion((0,1,0),2*math.pi*t)
            transforms.append((position,rotation))
        idle.append(transforms)
    write_sca(UNIT/"GGA2301_idle.sca",names,parents,idle,12.0)


def main():
    UNIT.mkdir(parents=True,exist_ok=True)
    for lod,detail in ((0,32),(1,12)):
        mesh=build_mesh(detail)
        write_scm(mesh,UNIT/f"GGA2301_lod{lod}.scm",BONENAMES,PARENTS,PIVOTS)
        if lod==0: export_obj(mesh,ASSET_DIR)
        print(f"LOD{lod}: {len(mesh.indices)//3} triangles, {len(mesh.vertices)} vertices")
    animations()
    make_textures(ASSET_DIR,UNIT,save_dds_dxt5)
    make_previews(UNIT,ASSET_DIR)
    print("Reference rebuild exported to",UNIT)
    print("Muzzle at game height",PIVOTS[1][1]*SCALE,"and forward offset",PIVOTS[3][2]*SCALE)


if __name__=="__main__":
    main()
