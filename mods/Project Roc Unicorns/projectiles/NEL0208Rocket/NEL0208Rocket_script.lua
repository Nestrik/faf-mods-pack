local TArtilleryProjectile = import('/lua/terranprojectiles.lua').TArtilleryProjectile
local Effects = import('/lua/effecttemplates.lua')
local impactFlash = { '/effects/emitters/cannon_artillery_hit_flash_01_emit.bp' }

NEL0208Rocket = ClassProjectile(TArtilleryProjectile) {
    FxImpactLand = table.concatenate(Effects.TPlasmaCannonHeavyHit01, impactFlash),
    FxImpactUnit = table.concatenate(Effects.TPlasmaCannonHeavyHitUnit01, impactFlash),
    FxImpactProp = table.concatenate(Effects.TPlasmaCannonHeavyHitUnit01, impactFlash),
    FxLandHitScale = 1.35,
    FxUnitHitScale = 1.35,
    FxPropHitScale = 1.35,
}
TypeClass = NEL0208Rocket
