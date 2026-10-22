local PhasonProjectile = import('/lua/seraphimprojectiles.lua').SDFExperimentalPhasonProjectile
local EffectTemplate = import('/lua/effecttemplates.lua')
local impactBurst = {
    '/mods/seraphim-rework/effects/emitters/gga0401_impact_flash_emit.bp',
    '/mods/seraphim-rework/effects/emitters/gga0401_impact_ring_emit.bp',
    '/mods/seraphim-rework/effects/emitters/gga0401_impact_arcs_emit.bp',
}

GGP0401 = ClassProjectile(PhasonProjectile) {
    FxTrailScale = 1.8,
    -- Native impact handling applies damage once, then creates these finite
    -- particle emitters. The extra light/ring/arcs are purely visual.
    FxImpactUnit = table.concatenate(EffectTemplate.SDFExperimentalPhasonProjHitUnit, impactBurst),
    FxImpactLand = table.concatenate(EffectTemplate.SDFExperimentalPhasonProjHit01, impactBurst),
    FxImpactProp = table.concatenate(EffectTemplate.SDFExperimentalPhasonProjHit01, impactBurst),
    FxImpactWater = table.concatenate(EffectTemplate.SDFExperimentalPhasonProjHit01, impactBurst),
    FxImpactShield = impactBurst,
}
TypeClass = GGP0401
