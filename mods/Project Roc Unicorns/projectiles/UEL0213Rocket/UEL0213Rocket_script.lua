local TMissileCruiseProjectile = import('/lua/terranprojectiles.lua').TMissileCruiseProjectile
local Effects = import('/lua/effecttemplates.lua')

UEL0213Rocket = ClassProjectile(TMissileCruiseProjectile) {
    -- Native TacticalMissileComponent handles boost, glide, and terminal guidance.
    -- The weapon forces an upward velocity; no turning during the first second.
    LaunchTicks = 10,
    LaunchTicksRange = 0,
    LaunchTurnRate = 0,
    LaunchTurnRateRange = 0,
    FinalBoostAngle = 30,
    HeightDistanceFactor = 11,

    FxImpactTrajectoryAligned = false,
    FxImpactLand = Effects.TShipGaussCannonHit02,
    FxImpactUnit = Effects.TShipGaussCannonHitUnit02,
    FxImpactProp = Effects.TShipGaussCannonHit02,
    FxLandHitScale = 3,
    FxUnitHitScale = 3,
    FxPropHitScale = 3,
    FxShieldHitScale = 3,
    FxWaterHitScale = 3,
}
TypeClass = UEL0213Rocket
