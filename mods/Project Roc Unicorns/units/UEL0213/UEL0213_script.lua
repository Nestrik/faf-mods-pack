local TLandUnit = import('/lua/terranunits.lua').TLandUnit
local TIFCruiseMissileLauncher = import('/lua/terranweapons.lua').TIFCruiseMissileLauncher

UEL0213 = ClassUnit(TLandUnit) {
    OnMotionHorzEventChange = function(self, new, old)
        TLandUnit.OnMotionHorzEventChange(self, new, old)
        if self.Dead then return end
        if new == 'Stopped' then
            if self.WheelAnimator then self.WheelAnimator:SetRate(0) end
        elseif old == 'Stopped' then
            if not self.WheelAnimator then
                self.WheelAnimator = self.Trash:Add(CreateAnimator(self, true))
                self.WheelAnimator:PlayAnim(self.Blueprint.Display.AnimationWalk, true)
                self.WheelAnimator:SetDirectionalAnim(true)
            end
            self.WheelAnimator:SetRate(self.Blueprint.Display.AnimationWalkRate or 1)
        end
    end,

    Weapons = {
        RocketRack = ClassWeapon(TIFCruiseMissileLauncher) {
            CreateProjectileAtMuzzle = function(self, muzzle)
                local projectile = TIFCruiseMissileLauncher.CreateProjectileAtMuzzle(self, muzzle)
                if projectile and not projectile:BeenDestroyed() then
                    -- Override engine aiming after projectile creation: clear the
                    -- vertical tube before the native tactical guidance turns it.
                    projectile:SetVelocity(0, 10, 0)
                    projectile:SetTurnRate(0)
                end
                return projectile
            end,
        },
    },
}
TypeClass = UEL0213
