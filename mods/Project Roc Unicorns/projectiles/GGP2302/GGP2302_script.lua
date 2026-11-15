local Base = import('/lua/sim/projectiles/EmitterProjectile.lua').EmitterProjectile
local Impact = {
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_flash_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_ring_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_mist_emit.bp',
    '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_impact_sparks_emit.bp',
}
GGP2302 = ClassProjectile(Base) {
    -- World-space wake starts behind the sphere; corona stays at its centre.
    FxTrailOffset = -0.4,
    FxTrails = {
        '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_stardust_mist_emit.bp',
        '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_stardust_stars_emit.bp',
        '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_lightning_wake_emit.bp',
    },
    OnCreate = function(self, inWater)
        Base.OnCreate(self, inWater)
        CreateAttachedEmitter(self, -1, self.Army,
            '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_lightning_core_emit.bp')
    end,
    FxImpactLand = Impact,
    FxImpactUnit = Impact,
    FxImpactProp = Impact,
    FxImpactWater = Impact,
    FxLandHitScale = 1.0, FxUnitHitScale = 1.0, FxPropHitScale = 1.0, FxWaterHitScale = 1.0,
    DestroyOnImpact = true,
}
TypeClass = GGP2302
