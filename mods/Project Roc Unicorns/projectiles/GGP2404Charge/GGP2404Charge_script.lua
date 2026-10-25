local Projectile = import('/lua/sim/projectile.lua').Projectile
local Visuals = import('/mods/Project Roc Unicorns/lua/vael_itha_effects.lua')
GGP2404CHARGE = ClassProjectile(Projectile) {
    OnCreate = function(self, inWater)
        Projectile.OnCreate(self, inWater)
        self:SetCollision(false)
        self:SetVelocity(0, 0, 0)
    end,
    SetChargeProgress = function(self, progress)
        if progress <= 0 then
            if self.OrbEffects then Visuals.DestroyOrb(self.OrbEffects); self.OrbEffects = nil end
        elseif self.OrbEffects then
            Visuals.UpdateOrb(self.OrbEffects, progress)
        else
            self.OrbEffects = Visuals.CreateOrb(self, progress)
        end
    end,
}
TypeClass = GGP2404CHARGE
