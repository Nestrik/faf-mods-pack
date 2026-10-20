local SStructureUnit = import('/lua/seraphimunits.lua').SStructureUnit
local SIFZthuthaamArtilleryCannon = import('/lua/seraphimweapons.lua').SIFZthuthaamArtilleryCannon

GGA2401 = ClassUnit(SStructureUnit) {
    Weapons = {
        MainGun = ClassWeapon(SIFZthuthaamArtilleryCannon) {},
    },
}

TypeClass = GGA2401
