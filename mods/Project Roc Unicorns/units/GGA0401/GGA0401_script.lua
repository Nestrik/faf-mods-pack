local HoverTank = import('/lua/seraphimunits.lua').SHoverLandUnit
local SeraphimWeapons = import('/lua/seraphimweapons.lua')
local PhasonCannon = SeraphimWeapons.SDFExperimentalPhasonProj
local AAGun = SeraphimWeapons.SAAOlarisCannonWeapon

GGA0401 = ClassUnit(HoverTank) {
    OnStopBeingBuilt = function(self, builder, layer)
        HoverTank.OnStopBeingBuilt(self, builder, layer)
        -- Separate hull islands drift very gently. AA aiming bones are children
        -- of their hull island, so the mount and its guns travel together.
        self.HullSliders = {}
        for _, spec in ipairs({
            { 'PortHull', 0, 0.30 }, { 'StarboardFore', 2.1, 0.22 },
            { 'StarboardAft', 4.2, 0.27 }, { 'AftShard', 1.3, 0.20 },
        }) do
            local slider = CreateSlider(self, spec[1])
            slider:SetSpeed(-1)
            self.Trash:Add(slider)
            table.insert(self.HullSliders, { slider, spec[2], spec[3] })
        end
        self:ForkThread(self.FloatHullThread)
        local visual = self:CreateProjectileAtBone(
            '/mods/Project Roc Unicorns/projectiles/GGP0401Charge/GGP0401Charge_proj.bp', 'MainMuzzle')
        if visual and not visual:BeenDestroyed() then
            self.ChargeVisual = visual
            visual:AttachBoneTo(-1, self, 'MainMuzzle')
            visual:SetDrawScale(0.000001)
            self.Trash:Add(visual)
        end
    end,

    FloatHullThread = function(self)
        local phase = 0
        while not self.Dead and not self:BeenDestroyed() do
            for _, spec in ipairs(self.HullSliders) do
                spec[1]:SetGoal(0, spec[3] * math.sin(phase + spec[2]), 0)
            end
            phase = phase + math.pi / 40
            WaitTicks(1)
        end
    end,

    ResetChargeVisual = function(self)
        self.ChargeEpoch = (self.ChargeEpoch or 0) + 1
        if self.ChargeVisual and not self.ChargeVisual:BeenDestroyed() then
            self.ChargeVisual:SetDrawScale(0.000001)
        end
    end,

    BeginChargeVisual = function(self, duration)
        self:ResetChargeVisual()
        local epoch = self.ChargeEpoch
        self:ForkThread(function(unit)
            local ticks = math.max(1, math.floor(duration * 10) - 1)
            for tick = 0, ticks do
                if unit.Dead or unit:BeenDestroyed() or unit.ChargeEpoch ~= epoch then return end
                local t = tick / ticks
                local scale = t * t * (3 - 2 * t)
                if unit.ChargeVisual and not unit.ChargeVisual:BeenDestroyed() then
                    unit.ChargeVisual:SetDrawScale(0.1 * (0.05 + 0.95 * scale))
                end
                if tick < ticks then WaitTicks(1) end
            end
        end)
    end,

    OnKilled = function(self, instigator, damageType, overkillRatio)
        self:ResetChargeVisual()
        HoverTank.OnKilled(self, instigator, damageType, overkillRatio)
    end,

    Weapons = {
        MainGun = ClassWeapon(PhasonCannon) {
            FxMuzzleFlashScale = 1.3,
            FxChargeMuzzleFlashScale = 1.3,
            PlayFxMuzzleChargeSequence = function(self, muzzle)
                self.unit:BeginChargeVisual(self.Blueprint.MuzzleChargeDelay)
                PhasonCannon.PlayFxMuzzleChargeSequence(self, muzzle)
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                self.unit:ResetChargeVisual()
                PhasonCannon.PlayFxMuzzleSequence(self, muzzle)
            end,
            OnLostTarget = function(self)
                self.unit:ResetChargeVisual()
                PhasonCannon.OnLostTarget(self)
            end,
            RackSalvoFiringState = State(PhasonCannon.RackSalvoFiringState) {
                OnHaltFire = function(self)
                    self.unit:ResetChargeVisual()
                    PhasonCannon.RackSalvoFiringState.OnHaltFire(self)
                end,
            },
        },
        AA1 = ClassWeapon(AAGun) { FxMuzzleFlashScale = 0.7 },
        AA2 = ClassWeapon(AAGun) { FxMuzzleFlashScale = 0.7 },
        AA3 = ClassWeapon(AAGun) { FxMuzzleFlashScale = 0.7 },
        AA4 = ClassWeapon(AAGun) { FxMuzzleFlashScale = 0.7 },
    },
}
TypeClass = GGA0401
