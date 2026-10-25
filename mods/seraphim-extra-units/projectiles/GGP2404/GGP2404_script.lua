local PhasonProjectile = import('/lua/seraphimprojectiles.lua').SDFExperimentalPhasonProjectile
local Entity = import('/lua/sim/entity.lua').Entity
local Visuals = import('/mods/seraphim-extra-units/lua/vael_itha_effects.lua')
local FX = '/mods/seraphim-extra-units/effects/emitters/'
local Sin, Cos, Pi = math.sin, math.cos, math.pi

GGP2404 = ClassProjectile(PhasonProjectile) {
    -- Othuy-style energy: no visible smooth sphere or fixed violet sprites.
    -- Only StrikeNearbyUnits applies damage.
    FxTrails = {},
    FxImpactUnit = {},
    FxImpactProp = {},
    FxImpactLand = {},
    FxImpactWater = {},
    FxImpactShield = {},

    OnCreate = function(self, inWater)
        PhasonProjectile.OnCreate(self, inWater)
        self.Config = self.Blueprint.Lightning
        self.SpinTick = 0
        self:SetVelocityAlign(false)
        self.OrbEffects = Visuals.CreateOrb(self, 1)
        self.Trash:Add(ForkThread(self.FlightVisualThread, self))
    end,

    UpdateOrbVisual = function(self, fade)
        local c = self.Config
        self.SpinTick = self.SpinTick + 1
        local angle = self.SpinTick * c.SpinDegreesPerSecond * Pi / 1800
        self:SetOrientation({ 0, Sin(angle / 2), 0, Cos(angle / 2) }, true)
        local pulse = 1 + c.PulseAmplitude * Sin(self.SpinTick * 2 * Pi / c.PulsePeriodTicks)
        self:SetDrawScale(self.Blueprint.Display.UniformScale * pulse * (fade or 1))
        Visuals.UpdateOrb(self.OrbEffects, pulse * (fade or 1))
    end,

    FlightVisualThread = function(self)
        while not self:BeenDestroyed() and not self.Grounded do
            self:UpdateOrbVisual()
            WaitTicks(1)
        end
    end,

    OnImpact = function(self, targetType, targetEntity)
        if self.Grounded or self:BeenDestroyed() then return end
        if targetEntity and targetEntity.DisallowCollisions then return end
        local p = self:GetPosition()
        -- Shields intercept normally; no hazard teleports underneath a shield.
        -- Air and underwater contacts retain the ordinary phason impact.
        local land = targetType == 'Terrain' or targetType == 'Unit' or targetType == 'Prop'
        if not land or GetSurfaceHeight(p[1], p[3]) > GetTerrainHeight(p[1], p[3]) + 0.05 then
            Visuals.CreateBurst(self, 'ball_impact')
            PhasonProjectile.OnImpact(self, targetType, targetEntity)
            return
        end
        self.Grounded = true
        self:SetCollision(false)
        self:SetVelocity(0, 0, 0)
        self:SetBallisticAcceleration(0)
        local c = self.Config
        self:SetLifetime((c.SinkTicks + c.ActiveTicks + c.FadeTicks) / 10 + 1)
        self.GroundPosition = { p[1], GetTerrainHeight(p[1], p[3]), p[3] }
        Visuals.CreateBurst(self, 'ball_impact')
        local sound = self.Blueprint.Audio.Impact
        if sound then self:PlaySound(sound) end
        self.Trash:Add(ForkThread(self.GroundThread, self))
    end,

    GroundThread = function(self)
        local c, p = self.Config, self.GroundPosition
        for i = 1, c.SinkTicks do
            if self:BeenDestroyed() then return end
            local u = i / c.SinkTicks
            u = u * u * (3 - 2 * u)
            Warp(self, { p[1], p[2] + c.OrbRadius * (1 - u), p[3] })
            self:UpdateOrbVisual()
            WaitTicks(1)
        end
        -- Bolts emerge above ground; the sphere centre remains on the surface.
        self.BoltOrigin = Entity()
        self.Trash:Add(self.BoltOrigin)
        Warp(self.BoltOrigin, { p[1], p[2] + c.OrbRadius * 0.65, p[3] })
        for tick = 0, c.ActiveTicks - 1 do
            if self:BeenDestroyed() then return end
            self:UpdateOrbVisual()
            if math.mod(tick, c.StrikeIntervalTicks) == 0 then self:StrikeNearbyUnits() end
            WaitTicks(1)
        end
        for tick = 1, c.FadeTicks do
            if self:BeenDestroyed() then return end
            self:UpdateOrbVisual(1 - tick / (c.FadeTicks + 1))
            WaitTicks(1)
        end
        self:Destroy()
    end,

    StrikeNearbyUnits = function(self)
        local c, p = self.Config, self.GroundPosition
        local r = c.Radius
        local units = GetUnitsInRect(p[1] - r, p[3] - r, p[1] + r, p[3] + r)
        if not units then return end
        for _, unit in ipairs(units) do
            if not unit.Dead and not unit:BeenDestroyed()
                and not EntityCategoryContains(categories.AIR + categories.SUBMERSIBLE, unit)
                and (c.AffectFriendly or not IsAlly(self.Army, unit:GetArmy())) then
                local q = unit:GetPosition()
                local dx, dy, dz = q[1] - p[1], q[2] - p[2], q[3] - p[3]
                if dx * dx + dy * dy + dz * dz <= r * r then
                    local beam = AttachBeamEntityToEntity(self.BoltOrigin, -1, unit, 0,
                        self.Army, FX .. 'ball_strike_beam_emit.bp')
                    Visuals.TintBeam(beam, self.Army)
                    self.Trash:Add(beam)
                    self.Trash:Add(ForkThread(function()
                        WaitTicks(c.BeamTicks)
                        beam:Destroy()
                    end))
                    -- Color belongs to the projectile, even when striking an enemy.
                    local hit = CreateEmitterAtEntity(unit, self.Army, FX .. 'ball_hit_emit.bp')
                    Visuals.TintEmitter(hit, self.Army)
                    self.Trash:Add(hit)
                    local instigator = self
                    if self.Launcher and not self.Launcher:BeenDestroyed() then instigator = self.Launcher end
                    Damage(instigator, q, unit, c.DamagePerStrike, c.DamageType)
                end
            end
        end
    end,
}
TypeClass = GGP2404
