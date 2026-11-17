local TLandUnit = import('/lua/terranunits.lua').TLandUnit
local TDFGaussCannonWeapon = import('/lua/terranweapons.lua').TDFGaussCannonWeapon

UEL0212 = ClassUnit(TLandUnit) {
    OnCreate = function(self)
        TLandUnit.OnCreate(self)
        -- Each lower barrel pitches about its own mounting point.
        self.Trash:Add(CreateSlaver(self, 'Barrel_Left', 'Turret_Barrel'))
        self.Trash:Add(CreateSlaver(self, 'Barrel_Right', 'Turret_Barrel'))
    end,

    EnsureGunSlides = function(self)
        if self.GunSlides then return end
        self.GunSlides = {}
        self.GunRecoilEpoch = { Top = 0, Left = 0, Right = 0 }
        for _, side in { 'Top', 'Left', 'Right' } do
            local slide = CreateSlider(self, 'Recoil_' .. side)
            slide:SetWorldUnits(false)
            self.Trash:Add(slide)
            self.GunSlides[side] = slide
        end
    end,

    AnimateGunRecoil = function(self, side, epoch)
        local slide = self.GunSlides[side]
        slide:SetSpeed(-1)
        slide:SetGoal(0, 0, -0.22)
        WaitTicks(1)
        if self.Dead or self:BeenDestroyed() or self.GunRecoilEpoch[side] ~= epoch then return end
        slide:SetSpeed(0.55)
        slide:SetGoal(0, 0, 0)
    end,

    Weapons = {
        FrontTurret01 = ClassWeapon(TDFGaussCannonWeapon) {
            FxMuzzleFlashScale = 1,
            CreateProjectileAtMuzzle = function(self, muzzle)
                local projectile = TDFGaussCannonWeapon.CreateProjectileAtMuzzle(self, muzzle)
                if projectile and not projectile:BeenDestroyed() then
                    local unit = self.unit
                    local side = ({ Muzzle_Top = 'Top', Muzzle_Left = 'Left', Muzzle_Right = 'Right' })[muzzle]
                    if side then
                        unit:EnsureGunSlides()
                        unit.GunRecoilEpoch[side] = unit.GunRecoilEpoch[side] + 1
                        unit:ForkThread(unit.AnimateGunRecoil, side, unit.GunRecoilEpoch[side])
                    end
                end
                return projectile
            end,
        },
    },
}
TypeClass = UEL0212
