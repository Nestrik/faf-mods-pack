local Projectile = import('/lua/sim/projectile.lua').Projectile
GGP0401CHARGE = ClassProjectile(Projectile) {
    OnCreate = function(self, inWater)
        Projectile.OnCreate(self, inWater)
        self:SetCollision(false)
        self:SetVelocity(0, 0, 0)
    end,
}
TypeClass = GGP0401CHARGE
