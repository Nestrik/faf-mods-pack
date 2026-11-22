-- RaZlom's static wreck has one bone, unlike its articulated live skeleton.
local PreviousCreateWreckageEffects = CreateWreckageEffects
local RaZlomWreckSmoke = import('/lua/effecttemplates.lua').DefaultWreckageEffectsLrg01

function CreateWreckageEffects(unit, prop)
    local bp = unit.Blueprint or unit:GetBlueprint()
    if bp.BlueprintId ~= 'gga0405' then
        return PreviousCreateWreckageEffects(unit, prop)
    end
    -- Never use a live leg/ring bone index on the single-bone wreck.
    if not prop or prop:BeenDestroyed() then return end
    for i = 1, 2 do
        local emitter = CreateEmitterAtBone(prop, 0, unit.Army, RaZlomWreckSmoke[i])
        emitter:ScaleEmitter(1)
        emitter:SetEmitterParam('LIFETIME', 60)
        prop.Trash:Add(emitter)
    end
end
