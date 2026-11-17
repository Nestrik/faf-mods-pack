local TLandUnit = import('/lua/terranunits.lua').TLandUnit
local TDFGaussCannonWeapon = import('/lua/terranweapons.lua').TDFGaussCannonWeapon

UEL0209 = ClassUnit(TLandUnit) {
    EnsureGunSlides = function(self)
        if self.GunSlides then return end
        self.GunSlides = {}
        self.GunRecoilEpoch = { Left = 0, Right = 0 }
        for _, side in { 'Left', 'Right' } do
            local slide = CreateSlider(self, 'Recoil_' .. side)
            slide:SetWorldUnits(false)
            self.Trash:Add(slide)
            self.GunSlides[side] = slide
        end
    end,

    AnimateGunRecoil = function(self, side, epoch)
        local slide = self.GunSlides[side]
        -- The projectile and native muzzle flash are created before this runs.
        slide:SetSpeed(-1)
        slide:SetGoal(0, 0, -0.22)
        WaitTicks(1)
        if self.Dead or self:BeenDestroyed() or self.GunRecoilEpoch[side] ~= epoch then return end
        slide:SetSpeed(0.55)
        slide:SetGoal(0, 0, 0)
    end,

    Weapons = {
        FrontTurret01 = ClassWeapon(TDFGaussCannonWeapon) {
            FxMuzzleFlashScale = 1.2,
            CreateProjectileAtMuzzle = function(self, muzzle)
                local projectile = TDFGaussCannonWeapon.CreateProjectileAtMuzzle(self, muzzle)
                if projectile and not projectile:BeenDestroyed() then
                    local unit = self.unit
                    unit:EnsureGunSlides()
                    local side = muzzle == 'Muzzle_Left' and 'Left' or 'Right'
                    unit.GunRecoilEpoch[side] = unit.GunRecoilEpoch[side] + 1
                    unit:ForkThread(unit.AnimateGunRecoil, side, unit.GunRecoilEpoch[side])
                end
                return projectile
            end,
        },
    },
}
TypeClass = UEL0209
