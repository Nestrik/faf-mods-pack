local Ring = import('/mods/Project Roc Unicorns/lua/razlom_ring.lua')
local Walker = import('/lua/seraphimunits.lua').SWalkingLandUnit
local Motion = import('/lua/sim/units/mobileunit.lua').MobileUnit
local Gait = import('/mods/Project Roc Unicorns/lua/razlom_locomotion.lua')
local Entity = import('/lua/sim/entity.lua').Entity
local Weapons = import('/mods/Project Roc Unicorns/lua/razlom_weapons.lua')
local Parts = import('/mods/Project Roc Unicorns/units/GGA0405/parts.lua').Parts

-- XSL0401's exact ambient emitter resources, raised with the native build shader.
local BuildMistEmitters = {
    '/effects/emitters/seraphim_being_built_ambient_02_emit.bp',
    '/effects/emitters/seraphim_being_built_ambient_03_emit.bp',
    '/effects/emitters/seraphim_being_built_ambient_04_emit.bp',
    '/effects/emitters/seraphim_being_built_ambient_05_emit.bp',
    '/effects/emitters/seraphim_being_built_ambient_01_emit.bp',
}
local function BuildEffect(unit, builder, effectsBag, scaleFactor)
    local emitters = {}
    local anchor = Entity { Owner = unit, Army = unit.Army }
    local initial = unit:GetPosition()
    local initialScale = .25 + .75 * unit:GetFractionComplete()
    anchor:SetPosition({initial[1], initial[2] + 3.2753124 * initialScale, initial[3]}, true)
    effectsBag:Add(anchor)
    local lods = unit.Blueprint.Display.Mesh.LODs
    local sizeZ = unit.Blueprint.Physics.MeshExtentsZ or unit.Blueprint.Footprint.SizeZ
    for i, effect in ipairs(BuildMistEmitters) do
        local emitter = CreateAttachedEmitter(anchor, -1, unit.Army, effect)
        emitter:SetEmitterParam('LODCUTOFF', i == 5 and .9 * lods[table.getn(lods)].LODCutoff or lods[1].LODCutoff)
        emitter:SetEmitterCurveParam('Y_POSITION_CURVE', 0, 0)
        emitter:SetEmitterCurveParam('YDIR_CURVE', 0, 0)
        emitter:ScaleEmitter((i == 5 and 3.2 or 4) * initialScale)
        effectsBag:Add(emitter)
        table.insert(emitters, emitter)
    end
    while not unit.Dead and not unit.FinishedVisualsCreated do
        local fraction = unit:GetFractionComplete()
        if fraction >= 1 then break end
        -- Body centre measured from both exported chassis chunks (model-space Y).
        local growth = .25 + .75 * fraction
        local height = 3.2753124 * growth
        local position = unit:GetPosition()
        -- Move an unscaled owner entity; never accumulate emitter offsets.
        anchor:SetPosition({position[1], position[2] + height, position[3]}, false)
        for i, emitter in ipairs(emitters) do
            emitter:ScaleEmitter((i == 5 and 3.2 or 4) * growth)
        end
        WaitTicks(1)
    end
    if not unit.Dead then
        CreateLightParticleIntel(unit, -1, unit.Army, .75 * sizeZ * 3.5, 8, 'glow_02', 'ramp_blue_22')
    end
end

GGA0405 = ClassUnit(Walker) {
    -- The root mesh is the entire intact hull, not a detachable debris fragment.
    ShowUnitDestructionDebris = false,
    CreateWreckageProp = function(self, overkillRatio)
        local wreck = Walker.CreateWreckageProp(self, overkillRatio)
        if wreck then
            -- Use the dedicated collapsed wreck, not an auto-generated live-mesh copy.
            wreck:SetMesh('/mods/Project Roc Unicorns/units/GGA0405/wreck_' .. Random(1,3) .. '_mesh')
        end
        self:HideBone(0, true)
        return wreck
    end,

    OnCreate = function(self)
        Walker.OnCreate(self)
        self.ModelParts = {}
        self.LegVisuals = {}
        -- Native build shader only scales the unit mesh, not attached Entities.
        -- Keep it hidden until the complete assembly can be revealed atomically.
        self:HideBone(0, true)
    end,
    CreateFinishedVisualParts = function(self)
        -- All visible parts are rigidly skinned to this unit's native skeleton.
        -- This preserves army colour and the existing bone animation controllers.
        self.FinishedVisualsCreated = true
    end,
    DestroyConstructionVisuals = function(self)
        for _, part in ipairs(self.ConstructionParts or {}) do
            if not part:BeenDestroyed() then part:Destroy() end
        end
        self.ConstructionParts = {}
    end,
    StartBeingBuiltEffects = function(self, builder, layer)
        Walker.StartBeingBuiltEffects(self, builder, layer)
        -- One native unit mesh receives the real construction fraction in the shader.
        self:SetMesh('/mods/Project Roc Unicorns/units/GGA0405/construction_mesh', true)
        self:ShowBone(0, true)
        self:ForkThread(BuildEffect, builder, self.OnBeingBuiltEffectsBag, 2)
    end,
    OnStartBeingBuilt = function(self, builder, layer)
        Walker.OnStartBeingBuilt(self, builder, layer)
    end,
    StopBeingBuiltEffects = function(self, builder, layer)
        Walker.StopBeingBuiltEffects(self, builder, layer)
        if not self.Dead then
            self:SetMesh('/mods/Project Roc Unicorns/units/GGA0405/chassis_live_mesh', true)
            self:ShowBone(0, true)
        end
    end,
    OnStopBeingBuilt = function(self, builder, layer)
        Walker.OnStopBeingBuilt(self, builder, layer)
        self:DestroyConstructionVisuals()
        self:SetMesh('/mods/Project Roc Unicorns/units/GGA0405/chassis_live_mesh', true)
        self:ShowBone(0, true)
        self:CreateFinishedVisualParts()
        self:ForkThread(function(unit)
            local states = {}
            while not unit.Dead and not unit:BeenDestroyed() do
                local p = unit:GetPosition()
                local water = GetSurfaceHeight(p[1],p[3])
                -- Deployed centre 6.21, bounding radius <1.73: all of the tilted ring clears water.
                local allowed = {MainGun=p[2]+4.30>water}
                for _,label in ipairs({'AuxLeft','AuxRight'}) do
                    local muzzle=unit:GetPosition(label..'Muzzle')
                    allowed[label]=muzzle[2]>GetSurfaceHeight(muzzle[1],muzzle[3])+.08
                end
                for label,enabled in pairs(allowed) do
                    local weapon=unit:GetWeaponByLabel(label)
                    weapon.WaterClear=enabled
                    if states[label]~=enabled then
                        states[label]=enabled
                        weapon:SetWeaponEnabled(enabled)
                        if not enabled and label~='MainGun' then weapon:PlayFxBeamEnd() end
                    end
                end
                WaitTicks(2)
            end
        end)

        Ring.Initialize(self)
        Gait.Initialize(self)
        self:ForkThread(function(unit)
            local gun = unit:GetWeaponByLabel('MainGun')
            while not unit.Dead do
                gun:UpdateOrderedAttackPursuit()
                WaitTicks(5)
            end
        end)
    end,
    OnMotionHorzEventChange = function(self, new, old)
        -- World-space foot solver replaces the stock constant-rate walk animator.
        Motion.OnMotionHorzEventChange(self, new, old)
        self.Moving = new ~= 'Stopped'
        if self.Moving then
            local gun = self:GetWeaponByLabel('MainGun')
            if gun and gun.Charging then
                gun:StopCharge()
                ChangeState(gun, gun.IdleState)
            end
        end
    end,
    RemoveVisualParts = function(self)
        Ring.DestroyEffects(self)
        self:DestroyConstructionVisuals()
        for _, part in ipairs(self.ModelParts or {}) do
            if not part:BeenDestroyed() then part:Destroy() end
        end
        self.ModelParts = {}
        local gun = self:GetWeaponByLabel('MainGun')
        if gun then gun:StopCharge() end
    end,
    OnKilled = function(self, instigator, damageType, overkillRatio)
        self:RemoveVisualParts()
        Walker.OnKilled(self, instigator, damageType, overkillRatio)
    end,
    OnDestroy = function(self)
        self:RemoveVisualParts()
        Walker.OnDestroy(self)
    end,
    Weapons = {
        MainGun = Weapons.SiegeWeapon,
        AuxLeft = Weapons.AuxWeapon,
        AuxRight = Weapons.AuxWeapon,
    },
}
TypeClass = GGA0405
