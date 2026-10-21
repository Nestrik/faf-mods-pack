local SStructureUnit = import('/lua/seraphimunits.lua').SStructureUnit
local SIFZthuthaamArtilleryCannon = import('/lua/seraphimweapons.lua').SIFZthuthaamArtilleryCannon
local CreateSlaver = CreateSlaver

GGA2401 = ClassUnit(SStructureUnit) {
    OnCreate = function(self)
        SStructureUnit.OnCreate(self)
        -- As on stock UAL0205: copy the master barrel's rotation, while each
        -- slave retains its own hinge position and the islands remain level.
        self.Trash:Add(CreateSlaver(self, 'Barrel_01', 'Turret_Barrel'))
        self.Trash:Add(CreateSlaver(self, 'Barrel_02', 'Turret_Barrel'))
        self.Trash:Add(CreateSlaver(self, 'Barrel_04', 'Turret_Barrel'))
        self.Trash:Add(CreateSlaver(self, 'Barrel_05', 'Turret_Barrel'))
    end,

    Weapons = {
        MainGun = ClassWeapon(SIFZthuthaamArtilleryCannon) {},
    },
}

TypeClass = GGA2401
