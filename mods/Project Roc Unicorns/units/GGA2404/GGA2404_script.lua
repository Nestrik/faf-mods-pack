local Structure = import('/lua/seraphimunits.lua').SStructureUnit
local Cannon = import('/lua/seraphimweapons.lua').SDFExperimentalPhasonProj

GGA2404 = ClassUnit(Structure) {
    OnStopBeingBuilt = function(self, builder, layer)
        Structure.OnStopBeingBuilt(self, builder, layer)
        -- Animation setup cannot gate the native weapon. The tank's visible
        -- charge projectile uses SetDrawScale, without particle helper methods.
        self:ForkThread(self.InitializeGunAnimation)
        self:GetWeaponByLabel('MainGun'):StartEconomyDrain()
    end,

    InitializeGunAnimation = function(self)
        self.GondolaSliders = {}
        for _, bone in ipairs({'GondolaL', 'GondolaR'}) do
            local slider = CreateSlider(self, bone)
            slider:SetSpeed(-1)
            self.Trash:Add(slider)
            table.insert(self.GondolaSliders, slider)
        end
        for _, bone in ipairs({'Field', 'FieldBoost', 'FieldPeak'}) do
            self:HideBone(bone, true)
        end
        self.HoverSlider = CreateSlider(self, 'Hover')
        self.HoverSlider:SetSpeed(-1)
        self.Trash:Add(self.HoverSlider)
        self:ForkThread(self.FloatGunThread)
        local visual = self:CreateProjectileAtBone(
            '/mods/Project Roc Unicorns/projectiles/GGP2404Charge/GGP2404Charge_proj.bp', 'Charge')
        if visual and not visual:BeenDestroyed() then
            self.ChargeVisual = visual
            visual:AttachBoneTo(-1, self, 'Charge')
            visual:SetDrawScale(.000001)
            self.Trash:Add(visual)
        end
        self:SetGunChargePose(0, false)
        local spin = CreateRotator(self, 'Charge', 'z')
        spin:SetTargetSpeed(65)
        spin:SetAccel(120)
        self.Trash:Add(spin)
    end,

    FloatGunThread = function(self)
        local cfg = self.Blueprint.ChargeAnimation
        local amplitude = cfg.HoverHeight / self.Blueprint.Display.UniformScale
        local phase = 0
        local step = 2 * math.pi / cfg.HoverPeriodTicks
        self.HoverSlider:SetSpeed(amplitude * step * 10)
        while not self.Dead and not self:BeenDestroyed() do
            self.HoverSlider:SetGoal(0, amplitude * math.sin(phase), 0)
            phase = math.mod(phase + step, 2 * math.pi)
            WaitTicks(1)
        end
    end,

    SetGunChargePose = function(self, openness, visible)
        local previous = self.GondolaOpen
        self.GondolaOpen = openness
        -- Native slide goals use model units, matching the exported rig scale.
        local offset = self.Blueprint.ChargeAnimation.ClosedInwardOffset
            / self.Blueprint.Display.UniformScale * (1 - openness)
        if self.GondolaSliders then
            local distance = self.Blueprint.ChargeAnimation.ClosedInwardOffset
                / self.Blueprint.Display.UniformScale
            local speed = previous and math.max(.001, math.abs(openness - previous) * distance * 10) or -1
            self.GondolaSliders[1]:SetSpeed(speed)
            self.GondolaSliders[2]:SetSpeed(speed)
            self.GondolaSliders[1]:SetGoal(offset, 0, 0)
            self.GondolaSliders[2]:SetGoal(-offset, 0, 0)
        end
        local visual = self.ChargeVisual
        if visual and not visual:BeenDestroyed() then
            visual:SetDrawScale(visible and self.Blueprint.ChargeAnimation.VisualScale * (.05 + .95 * openness) or .000001)
        end
    end,

    AnimateRecharge = function(self, seconds, afterShot)
        self.AnimationEpoch = (self.AnimationEpoch or 0) + 1
        local epoch = self.AnimationEpoch
        self:ForkThread(function(unit)
            local function alive()
                return not unit.Dead and not unit:BeenDestroyed() and unit.AnimationEpoch == epoch
            end
            local cfg = unit.Blueprint.ChargeAnimation
            local ticks = math.max(1, math.floor(seconds * 10 + .5))
            local closeTicks = afterShot and cfg.CloseTicks or 0
            local delayTicks = afterShot and cfg.PostShotDelayTicks or 0
            local growTicks = math.max(1, ticks - closeTicks - delayTicks)
            if afterShot then
                unit:SetGunChargePose(1, false)
                WaitTicks(delayTicks)
                for i = 1, closeTicks do
                    if not alive() then return end
                    local t = i / closeTicks
                    unit:SetGunChargePose(1 - t * t * (3 - 2 * t), false)
                    WaitTicks(1)
                end
            else
                unit:SetGunChargePose(0, false)
            end
            for i = 1, growTicks do
                if not alive() then return end
                local t = i / growTicks
                unit:SetGunChargePose(t * t * (3 - 2 * t), true)
                WaitTicks(1)
            end
            -- The native event, not this visual timer, decides when firing is
            -- allowed. During an energy shortage the full orb waits here.
            if alive() then unit:SetGunChargePose(1, true) end
        end)
    end,

    ShotAnimation = function(self)
        self:SetGunChargePose(1, false)
        if not self.ShotRecoil then
            self.ShotRecoil = CreateRotator(self, 'Recoil', 'x')
            self.Trash:Add(self.ShotRecoil)
        end
        self.ShotRecoil:SetGoal(-2)
        self.ShotRecoil:SetSpeed(90)
        WaitTicks(1)
        if not self.Dead and not self:BeenDestroyed() then
            self.ShotRecoil:SetGoal(0)
            self.ShotRecoil:SetSpeed(18)
        end
    end,

    OnKilled = function(self, instigator, damageType, overkillRatio)
        self.AnimationEpoch = (self.AnimationEpoch or 0) + 1
        self:SetGunChargePose(0, false)
        -- Native weapon destruction owns and cancels its economy event.
        Structure.OnKilled(self, instigator, damageType, overkillRatio)
    end,

    Weapons = {
        MainGun = ClassWeapon(Cannon) {
            FxMuzzleFlash = {},
            FxChargeMuzzleFlash = {},
            StartEconomyDrain = function(self)
                local previous = self.EconDrain
                Cannon.StartEconomyDrain(self)
                local event = self.EconDrain
                if event and event ~= previous then
                    local afterShot = self.AnimationAfterShot or false
                    self.AnimationAfterShot = false
                    self.unit:AnimateRecharge(
                        math.max(.1, self:GetWeaponEnergyRequired() / self:GetWeaponEnergyDrain()), afterShot)
                end
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                Cannon.PlayFxMuzzleSequence(self, muzzle)
                self.AnimationAfterShot = true
                self.unit:ForkThread(self.unit.ShotAnimation)
            end,
            -- No custom firing state, ChargeReady gate, economy allocation,
            -- projectile-creation override or target-loss transition.
        },
    },
}
TypeClass = GGA2404
