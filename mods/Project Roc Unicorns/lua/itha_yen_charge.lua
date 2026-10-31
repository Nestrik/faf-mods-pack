-- Visual-only controller. Native DefaultProjectileWeapon still owns all firing,
-- target checks, reload timing, projectile creation and damage.
local Beam = '/mods/Project Roc Unicorns/effects/emitters/itha_yen_charge_beam_emit.bp'
local ChargeMesh = '/mods/Project Roc Unicorns/effects/entities/DushNaiCharge/DushNaiCharge_mesh'
local Entity = import('/lua/sim/Entity.lua').Entity
local ChargeFX = import('/lua/effecttemplates.lua').SDFExperimentalPhasonProjFXTrails01
local CoreBeam = '/mods/Project Roc Unicorns/effects/emitters/itha_yen_charge_core_beam_emit.bp'
local ClosedOffset = 2.15 -- native SCM units; .215 game units per side
local FullOrbScale = .048 -- .288 game-unit radius: fits the .596-wide open gap

local function Alive(unit, epoch)
    return not unit.Dead and not unit:BeenDestroyed() and unit.ChargeEpoch == epoch
end

local function Smooth(t)
    return t * t * (3 - 2 * t)
end

function ClearOrbEffects(unit)
    for _, effect in ipairs(unit.GunOrbEffects or {}) do effect:Destroy() end
    unit.GunOrbEffects = {}
end

function UpdateOrbEffects(unit, progress, visible)
    if not visible then ClearOrbEffects(unit); return end
    if not unit.GunOrbEffects or table.getn(unit.GunOrbEffects) == 0 then
        unit.GunOrbEffects = {}
        for _, path in ipairs(ChargeFX) do
            local effect = CreateAttachedEmitter(unit.ChargeVisual, -1, unit.Army, path)
            table.insert(unit.GunOrbEffects, effect)
        end
    end
    for _, effect in ipairs(unit.GunOrbEffects) do
        effect:ScaleEmitter(.55 * math.max(.04, progress))
    end
end

function SetPose(unit, openness, progress, visible)
    local offset = ClosedOffset * (1 - openness)
    local speed = unit.GunOpenness and math.max(.001, math.abs(openness - unit.GunOpenness) * ClosedOffset * 10) or -1
    unit.GunOpenness = openness
    unit.GunChargeProgress = progress
    if unit.GondolaSliders then
        unit.GondolaSliders[1]:SetSpeed(speed)
        unit.GondolaSliders[2]:SetSpeed(speed)
        unit.GondolaSliders[1]:SetGoal(offset, 0, 0)
        unit.GondolaSliders[2]:SetGoal(-offset, 0, 0)
    end
    local visual = unit.ChargeVisual
    if visual and not visual:BeenDestroyed() then
        -- A visible seed grows for the entire charge; ready pose retains it.
        local orb = math.max(.04, progress)
        visual:SetDrawScale(visible and FullOrbScale * orb or .000001)
        UpdateOrbEffects(unit, orb, visible)
    end
end

function ClearBeams(unit)
    for _, beam in ipairs(unit.GunChargeBeams or {}) do beam:Destroy() end
    unit.GunChargeBeams = {}
end

function ElectricalFieldThread(unit)
    local tick = 0
    while not unit.Dead and not unit:BeenDestroyed() do
        ClearBeams(unit)
        local progress = unit.GunChargeProgress or 0
        -- Continuous field while charging AND ready. Endpoints still change
        -- every tick, rather than leaving static strands around the sphere.
        local active = unit.GunVisualStage == 'charging' or unit.GunVisualStage == 'ready'
        if active then
            local count = unit.GunVisualStage == 'ready' and 3 or 4
            for i = 1, count do
                local left = math.mod(tick + i * 2, 5) + 1
                local right = math.mod(tick * 3 + i, 5) + 1
                for _, path in ipairs({Beam, CoreBeam}) do
                    local beam = AttachBeamEntityToEntity(unit, 'ChargeL' .. left,
                        unit, 'ChargeR' .. right, unit.Army, path)
                    if beam then
                        local width = path == CoreBeam and (.025 + .040 * progress) or (.12 + .16 * progress)
                        beam:SetBeamParam('THICKNESS', width)
                        table.insert(unit.GunChargeBeams, beam)
                    end
                end
            end
        end
        tick = tick + 1
        WaitTicks(1)
    end
    ClearBeams(unit)
end

function Recharge(unit, seconds, afterShot)
    unit.ChargeEpoch = (unit.ChargeEpoch or 0) + 1
    local epoch = unit.ChargeEpoch
    local start = afterShot and 0 or (unit.GunChargeProgress or 0)
    unit:ForkThread(function(self)
        local ticks = math.max(1, math.floor(seconds * 10 + .5))
        local closing = afterShot and 8 or 0
        if afterShot then
            self.GunVisualStage = 'recovering'
            SetPose(self, 1, 0, false)
            WaitTicks(2)
            for i = 1, 6 do
                if not Alive(self, epoch) then return end
                SetPose(self, 1 - Smooth(i / 6), 0, false)
                WaitTicks(1)
            end
        end
        local growTicks = math.max(1, ticks - closing)
        self.GunVisualStage = 'charging'
        for i = 1, growTicks do
            if not Alive(self, epoch) then return end
            local t = start + (1 - start) * i / growTicks
            SetPose(self, Smooth(t), t, true)
            WaitTicks(1)
        end
        if Alive(self, epoch) then
            self.GunVisualStage = 'ready'
            SetPose(self, 1, 1, true)
        end
    end)
end

function BeginWeaponCharge(unit, duration)
    -- Do not shrink/reset a ball already recharging or waiting for a target.
    if unit.GunVisualStage ~= 'ready' then Recharge(unit, duration, false) end
end

function OnShot(unit, rateOfFire)
    -- No WaitTicks in the native muzzle callback: the projectile leaves now.
    unit.GunVisualStage = 'recovering'
    SetPose(unit, 1, 0, false)
    Recharge(unit, 1 / math.max(.001, rateOfFire), true)
end

function Initialize(unit)
    unit.GondolaSliders = {}
    for _, bone in ipairs({'GondolaLeft', 'GondolaRight'}) do
        local slider = CreateSlider(unit, bone)
        slider:SetWorldUnits(false)
        slider:SetSpeed(-1)
        unit.Trash:Add(slider)
        table.insert(unit.GondolaSliders, slider)
    end
    -- Owned visual Entity, following the same mesh/visibility pattern as
    -- native shield visuals. It has no projectile lifetime, impact or motion.
    local visual = Entity({Owner = unit})
    visual:SetMesh(ChargeMesh, false)
    visual:SetCollisionShape('None')
    visual:AttachBoneTo(-1, unit, 'MainMuzzle')
    visual:SetParentOffset(Vector(0, 0, 0))
    visual:SetVizToFocusPlayer('Always')
    visual:SetVizToAllies('Always')
    visual:SetVizToEnemies('Intel')
    visual:SetVizToNeutrals('Intel')
    visual:SetDrawScale(.000001)
    unit.ChargeVisual = visual
    unit.Trash:Add(visual)
    unit.GunOrbEffects = {}
    unit.GunChargeBeams = {}
    SetPose(unit, 0, 0, false)
    unit:ForkThread(ElectricalFieldThread)
    Recharge(unit, 3, false)
end

function Stop(unit)
    unit.ChargeEpoch = (unit.ChargeEpoch or 0) + 1
    unit.GunVisualStage = 'off'
    ClearBeams(unit)
    ClearOrbEffects(unit)
    local visual = unit.ChargeVisual
    if visual and not visual:BeenDestroyed() then visual:SetDrawScale(.000001) end
end
