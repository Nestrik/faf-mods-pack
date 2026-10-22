local SStructureUnit = import('/lua/seraphimunits.lua').SStructureUnit
local PhasonWeapon = import('/lua/seraphimweapons.lua').SDFExperimentalPhasonProj

GGA2404 = ClassUnit(SStructureUnit) {
    OnStopBeingBuilt = function(self, builder, layer)
        SStructureUnit.OnStopBeingBuilt(self, builder, layer)
        self.HoverSlider = CreateSlider(self, 'Hover')
        self.Trash:Add(self.HoverSlider)
        self.FieldRotators = {}
        for _, bone in ipairs({'Field', 'FieldBoost', 'FieldPeak'}) do
            local rotator = CreateRotator(self, bone, 'z')
            rotator:SetTargetSpeed(150):SetAccel(300)
            self.Trash:Add(rotator)
        end
        self.ChargeRotator = CreateRotator(self, 'Charge', 'z')
        self.ChargeRotator:SetTargetSpeed(120):SetAccel(240)
        self.Trash:Add(self.ChargeRotator)
        self.RingRecoilRotator = CreateRotator(self, 'Recoil', 'x')
        self.Trash:Add(self.RingRecoilRotator)
        self.GondolaSliders = {}
        for _, bone in ipairs({'GondolaL', 'GondolaR'}) do
            local slider = CreateSlider(self, bone)
            self.GondolaSliders[#self.GondolaSliders + 1] = slider
            self.Trash:Add(slider)
        end
        -- A visual projectile inherits the launcher's army and visibility. It is
        -- collision-free, has no damage, and is attached until the unit is destroyed.
        local visual = self:CreateProjectileAtBone(
            '/mods/seraphim-rework/projectiles/GGP2404Charge/GGP2404Charge_proj.bp', 'Charge')
        if visual and not visual:BeenDestroyed() then
            self.ChargeVisual = visual
            visual:AttachBoneTo(-1, self, 'Charge')
            visual:SetChargeProgress(0)
            self.Trash:Add(visual)
        end
        self:SetChargePose(0, false)
        self:BeginRecharge(false)
        self:ForkThread(self.HoverThread)
    end,

    HoverThread = function(self)
        while not self:BeenDestroyed() do
            self.HoverSlider:SetGoal(0, 0.6, 0):SetSpeed(0.6)
            WaitSeconds(2)
            if self:BeenDestroyed() then return end
            self.HoverSlider:SetGoal(0, -0.6, 0):SetSpeed(0.6)
            WaitSeconds(2)
        end
    end,

    SetChargePose = function(self, openness, growing)
        local previous = self.GondolaOpen
        self.GondolaOpen = openness
        local cfg = self.Blueprint.ChargeAnimation
        local nativeOffset = cfg.ClosedInwardOffset / self.Blueprint.Display.UniformScale
        local offset = nativeOffset * (1 - openness)
        local speed = previous and math.max(0.001, math.abs(openness - previous) * nativeOffset * 10) or -1
        self.GondolaSliders[1]:SetGoal(offset, 0, 0):SetSpeed(speed)
        self.GondolaSliders[2]:SetGoal(-offset, 0, 0):SetSpeed(speed)
        if self.ChargeVisual and not self.ChargeVisual:BeenDestroyed() then
            self.ChargeVisual:SetChargeProgress(growing and (0.04 + 0.96 * openness) or 0)
        end
        -- The original full-width mesh field must not cut through the closed
        -- gondolas. During growth the scaled particle orb supplies the discharge.
        for _, bone in ipairs({'Field', 'FieldBoost', 'FieldPeak'}) do
            if growing and openness >= 0.98 then self:ShowBone(bone, true)
            else self:HideBone(bone, true) end
        end
    end,

    BeginRecharge = function(self, afterShot, periodTicks)
        self.ChargeReady = false
        self.ChargeEpoch = (self.ChargeEpoch or 0) + 1
        local epoch = self.ChargeEpoch
        if self.RechargeDrain then
            RemoveEconomyEvent(self, self.RechargeDrain)
            self.RechargeDrain = nil
        end
        local cfg = self.Blueprint.ChargeAnimation
        periodTicks = periodTicks or math.floor(10 / self.Blueprint.Weapon[1].RateOfFire + 0.5)
        local growTicks = math.max(1, periodTicks - cfg.PostShotDelayTicks - cfg.CloseTicks)
        self:ForkThread(function(unit)
            local function alive()
                return not unit.Dead and not unit:BeenDestroyed() and unit.ChargeEpoch == epoch
            end
            if afterShot then
                unit:SetChargePose(1, false)
                WaitTicks(cfg.PostShotDelayTicks)
                for tick = 1, cfg.CloseTicks do
                    if not alive() then return end
                    local p = tick / cfg.CloseTicks
                    p = p * p * (3 - 2 * p)
                    unit:SetChargePose(1 - p, false)
                    WaitTicks(1)
                end
            else
                unit:SetChargePose(0, false)
            end
            if not alive() then return end
            local weapon = unit:GetWeaponByLabel('MainGun')
            -- The same economy progress drives the orb and gondolas. A stalled
            -- economy cannot leave a fully grown, unpaid shot ready to fire.
            local drain = CreateEconomyEvent(unit, weapon:GetWeaponEnergyRequired(), 0,
                growTicks / 10, function(owner, progress)
                    if not alive() then return end
                    local p = progress * progress * (3 - 2 * progress)
                    owner:SetChargePose(p, true)
                end)
            unit.RechargeDrain = drain
            WaitFor(drain)
            if not alive() then return end
            RemoveEconomyEvent(unit, drain)
            unit.RechargeDrain = nil
            unit:SetChargePose(1, true)
            unit.ChargeReady = true
        end)
    end,

    OnKilled = function(self, instigator, type, overkillRatio)
        self.ChargeEpoch = (self.ChargeEpoch or 0) + 1
        self.ChargeReady = false
        if self.RechargeDrain then
            RemoveEconomyEvent(self, self.RechargeDrain)
            self.RechargeDrain = nil
        end
        if self.ChargeVisual and not self.ChargeVisual:BeenDestroyed() then
            self.ChargeVisual:SetChargeProgress(0)
        end
        for _, bone in ipairs({'Field', 'FieldBoost', 'FieldPeak'}) do self:HideBone(bone, true) end
        SStructureUnit.OnKilled(self, instigator, type, overkillRatio)
    end,

    Weapons = {
        MainGun = ClassWeapon(PhasonWeapon) {
            -- BeginRecharge pays exactly once, including the initial shot and
            -- recharging without a target. Suppress the separate native event.
            StartEconomyDrain = function(self) end,
            -- The centered charging entity supplies the army-colored FX.
            FxMuzzleFlash = {},
            FxChargeMuzzleFlash = {},
            FxMuzzleFlashScale = 0.6,
            FxChargeMuzzleFlashScale = 0.6,
            CreateProjectileAtMuzzle = function(self, muzzle)
                if not self.unit.ChargeReady then return nil end
                local projectile = PhasonWeapon.CreateProjectileAtMuzzle(self, muzzle)
                if projectile and not projectile:BeenDestroyed() then
                    -- Consume only a successfully created projectile. Recharging
                    -- runs independently of target acquisition and fire orders.
                    self.unit:BeginRecharge(true, math.floor(10 / self:GetWeaponRoF() + 0.5))
                    self.unit.RingRecoilRotator:SetGoal(-2):SetSpeed(90)
                    self.unit:ForkThread(function(unit)
                        WaitTicks(1)
                        if not unit.Dead and not unit:BeenDestroyed() then unit.RingRecoilRotator:SetGoal(0):SetSpeed(18) end
                    end)
                end
                return projectile
            end,
            RackSalvoFiringState = State(PhasonWeapon.RackSalvoFiringState) {
                Main = function(self)
                    self.WaitingForCharge = true
                    while not self.unit.Dead and not self.unit:BeenDestroyed()
                        and not self.unit.ChargeReady and not self.HaltFireOrdered
                        and self:WeaponHasTarget() do WaitTicks(1) end
                    self.WaitingForCharge = false
                    if self.unit.Dead or self.unit:BeenDestroyed() then return end
                    if self.HaltFireOrdered or not self:WeaponHasTarget() then
                        self.HaltFireOrdered = false
                        ChangeState(self, self.IdleState)
                        return
                    end
                    PhasonWeapon.RackSalvoFiringState.Main(self)
                end,
                OnLostTarget = function(self)
                    if self.WaitingForCharge then
                        self.WaitingForCharge = false
                        PhasonWeapon.OnLostTarget(self)
                    else
                        PhasonWeapon.RackSalvoFiringState.OnLostTarget(self)
                    end
                end,
            },
        },
    },
}
TypeClass = GGA2404
