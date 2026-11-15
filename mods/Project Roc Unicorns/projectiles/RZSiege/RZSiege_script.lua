local Base = import('/lua/sim/defaultprojectiles.lua').EmitterProjectile
local FX = '/mods/Project Roc Unicorns/effects/emitters/razlom_'
RZSiege = ClassProjectile(Base) {
    FxTrails = { FX .. 'flash_emit.bp', FX .. 'sparks_emit.bp' },
    FxImpactUnit = { FX .. 'impact_emit.bp', FX .. 'impact_ring_emit.bp', FX .. 'impact_sparks_emit.bp' },
    FxImpactLand = { FX .. 'impact_emit.bp', FX .. 'impact_ring_emit.bp', FX .. 'impact_sparks_emit.bp' },
    FxImpactShield = { FX .. 'impact_emit.bp', FX .. 'impact_ring_emit.bp' },
    FxImpactWater = { FX .. 'impact_emit.bp', FX .. 'impact_ring_emit.bp' },
    OnImpact = function(self, targetType, targetEntity)
        if targetType == 'Shield' and self.DamageData then self.DamageData.DamageAmount = 12000 end
        Base.OnImpact(self, targetType, targetEntity)
    end,
}
TypeClass = RZSiege
