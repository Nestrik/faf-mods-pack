local CLandUnit = import('/lua/cybranunits.lua').CLandUnit
local CybranWeapons = import('/lua/cybranweapons.lua')

-- The stock Monkeylord spins a bone named Center_Turret_Barrel on beam start.
-- Raider has fixed emitters on two independent pitch manipulators.
local DefaultBeamWeapon = import('/lua/sim/defaultweapons.lua').DefaultBeamWeapon
local RaiderBeam = ClassWeapon(CybranWeapons.CDFHeavyMicrowaveLaserGenerator) {
    PlayFxBeamStart = DefaultBeamWeapon.PlayFxBeamStart,
    PlayFxBeamEnd = DefaultBeamWeapon.PlayFxBeamEnd,
}

CRL0402 = ClassUnit(CLandUnit) {
    Weapons = {
        LeftBeam = ClassWeapon(RaiderBeam) {},
        RightBeam = ClassWeapon(RaiderBeam) {},
        Missile01 = ClassWeapon(CybranWeapons.CAAMissileNaniteWeapon) {},
    },

    OnMotionHorzEventChange = function(self, new, old)
        CLandUnit.OnMotionHorzEventChange(self, new, old)
        if self.Dead then return end
        if new == 'Stopped' then
            if self.DriveAnimator then self.DriveAnimator:SetRate(0) end
        elseif old == 'Stopped' then
            if not self.DriveAnimator then
                self.DriveAnimator = self.Trash:Add(CreateAnimator(self, true))
                self.DriveAnimator:PlayAnim(self.Blueprint.Display.AnimationWalk, true)
                self.DriveAnimator:SetDirectionalAnim(true)
            end
            self.DriveAnimator:SetRate(1)
        end
    end,
}

TypeClass = CRL0402
