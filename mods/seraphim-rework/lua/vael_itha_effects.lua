-- Othuy (XSL0402) visual construction: a hidden body and layered electricity.
-- Palette selection and beam tint use verified IEffect methods, not a fictitious
-- particle army-color flag. The ramp's rows follow FAF's 19 lobby army colors.
local FX = '/mods/seraphim-rework/effects/emitters/'
local Colors = import('/lua/GameColors.lua').GameColors.ArmyColors
local Effects = {
    {'ball_othuy_arcs',38}, {'ball_othuy_surface',26}, {'ball_othuy_core',16},
    {'ball_othuy_haze',8}, {'ball_othuy_motes',20}, {'ball_othuy_flash',12},
}

function ArmyPaletteIndex(army)
    local brain = ArmyBrains[army]
    local setup = brain and ScenarioInfo.ArmySetup[brain.Name]
    local index = setup and setup.ArmyColor or 16
    if type(index) ~= 'number' or index < 1 or index > 19 then index = 16 end
    return index
end

function TintEmitter(emitter, army)
    emitter:SetEmitterCurveParam('RAMPSELECTION_CURVE', (ArmyPaletteIndex(army) - 0.5) / 19, 0)
    return emitter
end

function CreateOrb(entity, progress)
    local effects = {}
    for _, spec in ipairs(Effects) do
        local emitter = CreateAttachedEmitter(entity, -1, entity.Army, FX .. spec[1] .. '_emit.bp')
        TintEmitter(emitter, entity.Army)
        entity.Trash:Add(emitter)
        effects[#effects + 1] = {Emitter=emitter, Rate=spec[2]}
    end
    UpdateOrb(effects, progress or 1)
    return effects
end

function UpdateOrb(effects, progress)
    for _, effect in ipairs(effects) do
        effect.Emitter:ScaleEmitter(math.max(0.001, progress))
        effect.Emitter:SetEmitterCurveParam('EMITRATE_CURVE', effect.Rate * (0.25 + 0.75 * progress), 0)
    end
end

function DestroyOrb(effects)
    for _, effect in ipairs(effects) do effect.Emitter:Destroy() end
end

function CreateBurst(entity, name)
    local emitter = CreateEmitterAtEntity(entity, entity.Army, FX .. name .. '_emit.bp')
    TintEmitter(emitter, entity.Army)
    -- Finite one-shot emitter, as in Projectile.CreateImpactEffects: it must
    -- survive immediate projectile destruction on a shield or water impact.
    return emitter
end

function TintBeam(beam, army)
    local color = Colors[ArmyPaletteIndex(army)]
    local r = tonumber(string.sub(color, 3, 4), 16) / 255
    local g = tonumber(string.sub(color, 5, 6), 16) / 255
    local b = tonumber(string.sub(color, 7, 8), 16) / 255
    for _, prefix in ipairs({'STARTCOLOR_', 'ENDCOLOR_'}) do
        beam:SetBeamParam(prefix .. 'R', r)
        beam:SetBeamParam(prefix .. 'G', g)
        beam:SetBeamParam(prefix .. 'B', b)
    end
    return beam
end
