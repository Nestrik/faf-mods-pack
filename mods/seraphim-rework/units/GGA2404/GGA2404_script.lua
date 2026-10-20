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
        self.ChargeSlider = CreateSlider(self, 'Charge')
        self.Trash:Add(self.ChargeSlider)
        -- A visual projectile inherits the launcher's army and visibility. It is
        -- collision-free, has no damage, and is attached until the unit is destroyed.
        local visual = self:CreateProjectileAtBone(
            '/mods/seraphim-rework/projectiles/GGP2404Charge/GGP2404Charge_proj.bp', 'Charge')
        if visual and not visual:BeenDestroyed() then
            self.ChargeVisual = visual
            visual:AttachBoneTo(-1, self, 'Charge')
            visual:SetDrawScale(0.000001)
            self.Trash:Add(visual)
        end
        self:ResetChargeVisual()
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

    ResetChargeVisual = function(self)
        self.ChargeEpoch = (self.ChargeEpoch or 0) + 1
        if self.ChargeVisual and not self.ChargeVisual:BeenDestroyed() then
            self.ChargeVisual:SetDrawScale(0.000001)
        end
        if self.ChargeSlider then self.ChargeSlider:SetGoal(0, 0, 0):SetSpeed(-1) end
        self:HideBone('FieldBoost', true)
        self:HideBone('FieldPeak', true)
        -- Field is intentionally never hidden: weak lightning persists after firing.
    end,

    BeginChargeVisual = function(self, seconds)
        self:ResetChargeVisual()
        local epoch = self.ChargeEpoch
        self:ForkThread(function(unit)
            local steps = math.max(1, math.floor(seconds * 10 + 0.5) - 1)
            for i = 0, steps do
                if unit.Dead or unit:BeenDestroyed() or unit.ChargeEpoch ~= epoch then return end
                local chargeTime = i / steps
                local p = math.min(1, chargeTime / 0.80)
                p = p * p * (3 - 2 * p)
                if unit.ChargeVisual and not unit.ChargeVisual:BeenDestroyed() then
                    unit.ChargeVisual:SetDrawScale(0.05 * (0.04 + 0.96 * p))
                end
                if p >= 0.30 then unit:ShowBone('FieldBoost', true) end
                if p >= 0.70 then unit:ShowBone('FieldPeak', true) end
                local travel = math.max(0, math.min(1, (chargeTime - 0.80) / 0.20))
                travel = travel * travel * (3 - 2 * travel)
                unit.ChargeSlider:SetGoal(0, 0, 28.8 * travel):SetSpeed(-1)
                if i < steps then WaitTicks(1) end
            end
        end)
    end,

    OnKilled = function(self, instigator, type, overkillRatio)
        self:ResetChargeVisual()
        SStructureUnit.OnKilled(self, instigator, type, overkillRatio)
    end,

    Weapons = {
        MainGun = ClassWeapon(PhasonWeapon) {
            FxMuzzleFlashScale = 0.6,
            FxChargeMuzzleFlashScale = 0.6,
            PlayFxMuzzleChargeSequence = function(self, muzzle)
                self.unit:BeginChargeVisual(self.Blueprint.MuzzleChargeDelay)
                PhasonWeapon.PlayFxMuzzleChargeSequence(self, muzzle)
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                self.unit:ResetChargeVisual()
                self.unit.RingRecoilRotator:SetGoal(-2):SetSpeed(90)
                self.unit:ForkThread(function(unit)
                    WaitTicks(1)
                    if not unit.Dead and not unit:BeenDestroyed() then unit.RingRecoilRotator:SetGoal(0):SetSpeed(18) end
                end)
                PhasonWeapon.PlayFxMuzzleSequence(self, muzzle)
            end,
            OnLostTarget = function(self)
                self.unit:ResetChargeVisual()
                PhasonWeapon.OnLostTarget(self)
            end,
            RackSalvoFiringState = State(PhasonWeapon.RackSalvoFiringState) {
                OnHaltFire = function(self)
                    self.unit:ResetChargeVisual()
                    PhasonWeapon.RackSalvoFiringState.OnHaltFire(self)
                end,
            },
        },
    },
}
TypeClass = GGA2404
