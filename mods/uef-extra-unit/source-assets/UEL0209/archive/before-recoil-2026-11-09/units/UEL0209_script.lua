local TLandUnit = import('/lua/terranunits.lua').TLandUnit
local TDFGaussCannonWeapon = import('/lua/terranweapons.lua').TDFGaussCannonWeapon
UEL0209 = ClassUnit(TLandUnit) {
    Weapons = { FrontTurret01 = ClassWeapon(TDFGaussCannonWeapon) {} },
}
TypeClass = UEL0209
