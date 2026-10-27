local HoverTank = import('/lua/seraphimunits.lua').SHoverLandUnit
local Weapons = import('/lua/seraphimweapons.lua')
local PhasonCannon = Weapons.SDFExperimentalPhasonProj
local AAGun = Weapons.SAAOlarisCannonWeapon

GGA0402 = ClassUnit(HoverTank) {
    OnCreate = function(self)
        HoverTank.OnCreate(self)
        -- One weapon controls the pair. The rear assembly keeps its own hinge
        -- and position while copying the front assembly's yaw and pitch.
        self.Trash:Add(CreateSlaver(self, 'MainAftYaw', 'MainForeYaw'))
        self.Trash:Add(CreateSlaver(self, 'MainAftPitch', 'MainForePitch'))
    end,

    OnStopBeingBuilt = function(self, builder, layer)
        HoverTank.OnStopBeingBuilt(self, builder, layer)
        self.HullSliders = {}
        for _, spec in ipairs({
            { 'ForeLeftShard', 0, .22 }, { 'PortIsland', 2.1, .25 },
            { 'PortAftIsland', 4.2, .22 }, { 'StarboardTip', 1.3, .18 },
        }) do
            local slider = CreateSlider(self, spec[1])
            slider:SetSpeed(-1)
            self.Trash:Add(slider)
            table.insert(self.HullSliders, { slider, spec[2], spec[3] })
        end
        self:ForkThread(self.FloatHullThread)
        self.ChargeVisuals = {}
        for _, muzzle in ipairs({ 'MainForeMuzzle', 'MainAftMuzzle' }) do
            local visual = self:CreateProjectileAtBone(
                '/mods/seraphim-extra-units/projectiles/GGP0402Charge/GGP0402Charge_proj.bp', muzzle)
            if visual and not visual:BeenDestroyed() then
                self.ChargeVisuals[muzzle] = visual
                visual:AttachBoneTo(-1, self, muzzle)
                visual:SetDrawScale(.000001)
                self.Trash:Add(visual)
            end
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

    ResetChargeVisual = function(self, muzzle)
        if muzzle then
            -- The second pod remains charged between the two shots.
            local visual = self.ChargeVisuals and self.ChargeVisuals[muzzle]
            if visual and not visual:BeenDestroyed() then visual:SetDrawScale(.000001) end
            return
        end
        self.ChargeEpoch = (self.ChargeEpoch or 0) + 1
        for _, visual in pairs(self.ChargeVisuals or {}) do
            if not visual:BeenDestroyed() then visual:SetDrawScale(.000001) end
        end
    end,

    BeginChargeVisual = function(self, seconds)
        self:ResetChargeVisual()
        local epoch = self.ChargeEpoch
        self:ForkThread(function(unit)
            local ticks = math.max(1, math.floor(seconds * 10) - 1)
            for tick = 0, ticks do
                if unit.Dead or unit:BeenDestroyed() or unit.ChargeEpoch ~= epoch then return end
                local t = tick / ticks
                local scale = .1 * (.05 + .95 * t * t * (3 - 2 * t))
                for _, visual in pairs(unit.ChargeVisuals or {}) do
                    if not visual:BeenDestroyed() then visual:SetDrawScale(scale) end
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
            FxMuzzleFlashScale = 1.1,
            FxRackChargeMuzzleFlash = PhasonCannon.FxChargeMuzzleFlash,
            FxRackChargeMuzzleFlashScale = 1.1,
            PlayFxRackSalvoChargeSequence = function(self)
                self.unit:BeginChargeVisual(self.Blueprint.RackSalvoChargeTime)
                PhasonCannon.PlayFxRackSalvoChargeSequence(self)
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                self.unit:ResetChargeVisual(muzzle)
                PhasonCannon.PlayFxMuzzleSequence(self, muzzle)
            end,
            OnLostTarget = function(self)
                self.unit:ResetChargeVisual()
                PhasonCannon.OnLostTarget(self)
            end,
            RackSalvoChargeState = State(PhasonCannon.RackSalvoChargeState) {
                OnHaltFire = function(self)
                    self.unit:ResetChargeVisual()
                    ChangeState(self, self.IdleState)
                end,
            },
            RackSalvoFiringState = State(PhasonCannon.RackSalvoFiringState) {
                OnHaltFire = function(self)
                    self.unit:ResetChargeVisual()
                    PhasonCannon.RackSalvoFiringState.OnHaltFire(self)
                end,
            },
        },
        AA1 = ClassWeapon(AAGun) { FxMuzzleFlashScale = .7 },
        AA2 = ClassWeapon(AAGun) { FxMuzzleFlashScale = .7 },
        AA3 = ClassWeapon(AAGun) { FxMuzzleFlashScale = .7 },
        AA4 = ClassWeapon(AAGun) { FxMuzzleFlashScale = .7 },
    },
}
TypeClass = GGA0402
