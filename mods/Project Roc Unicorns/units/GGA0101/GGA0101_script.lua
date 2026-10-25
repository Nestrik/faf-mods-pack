local SLandUnit = import('/lua/seraphimunits.lua').SLandUnit
local SLaanseMissileWeapon = import('/lua/seraphimweapons.lua').SLaanseMissileWeapon

GGA0101 = ClassUnit(SLandUnit) {
    Weapons = {
        MissileRack = ClassWeapon(SLaanseMissileWeapon) {},
    },
}

TypeClass = GGA0101
