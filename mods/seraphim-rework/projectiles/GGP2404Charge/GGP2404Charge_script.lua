local Projectile = import('/lua/sim/projectile.lua').Projectile
GGP2404CHARGE = ClassProjectile(Projectile) {
    OnCreate = function(self, inWater)
        Projectile.OnCreate(self, inWater)
        self:SetCollision(false)
        self:SetVelocity(0, 0, 0)
    end,
}
TypeClass = GGP2404CHARGE
