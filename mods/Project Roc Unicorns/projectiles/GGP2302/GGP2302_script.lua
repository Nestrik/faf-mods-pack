local Base = import('/lua/sim/projectiles/SinglePolyTrailProjectile.lua').SinglePolyTrailProjectile
local EffectTemplate = import('/lua/effecttemplates.lua')
local Impact = EffectTemplate.SDFExperimentalPhasonProjHit01
GGP2302 = ClassProjectile(Base) {
    -- Continuous overlapping corona particles, without the short white ring bursts.
    FxImpactTrajectoryAligned = false,
    FxTrailOffset = 0,
    PolyTrail = '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_comet_ribbon_emit.bp',
    PolyTrailOffset = 0,
    FxTrails = {
        '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_dark_motes_emit.bp',
        '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_stardust_mist_emit.bp',
        '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_stardust_stars_emit.bp',
    },
    OnCreate = function(self, inWater)
        Base.OnCreate(self, inWater)
        for lane, lateral in ipairs({ -0.25, 0.25 }) do
            CreateTrail(self, -1, self.Army,
                '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_white_fringe_' .. lane .. '_emit.bp'):OffsetEmitter(lateral, 0, 0)
        end
        -- Companion ribbon follows the same history as the existing comet trail.
        -- Three independent irregular masks and repeat lengths avoid aligned bars.
        for lane, lateral in ipairs({ -0.14, 0, 0.14 }) do
            CreateTrail(self, -1, self.Army,
                '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_irregular_lane_' .. lane .. '_emit.bp'):OffsetEmitter(lateral, 0, 0)
        end
        CreateAttachedEmitter(self, -1, self.Army,
            '/mods/Project Roc Unicorns/effects/emitters/sha_veyr_orb_shadow_emit.bp')
        CreateEmitterOnEntity(self, self.Army,
            '/effects/emitters/seraphim_experimental_phasonproj_fxtrails_06_emit.bp'):ScaleEmitter(0.65)
        self.Trash:Add(ForkThread(self.StartStaggeredLightning, self))
    end,
    -- A finite startup thread, owned by the projectile. Layers never reset together.
    StartStaggeredLightning = function(self)
        local fx = '/mods/Project Roc Unicorns/effects/emitters/'
        if self:BeenDestroyed() then return end
        CreateAttachedEmitter(self, -1, self.Army, fx .. 'sha_veyr_taper_arc_1_emit.bp')
        WaitTicks(1)
        if self:BeenDestroyed() then return end
        CreateEmitterOnEntity(self, self.Army,
            '/effects/emitters/seraphim_experimental_phasonproj_fxtrails_05_emit.bp'):ScaleEmitter(0.50)
        for i, delay in ipairs({ 1, 2, 1, 2 }) do
            WaitTicks(delay)
            if self:BeenDestroyed() then return end
            CreateAttachedEmitter(self, -1, self.Army,
                fx .. 'sha_veyr_taper_arc_' .. (i + 1) .. '_emit.bp')
        end
    end,
    FxImpactLand = Impact,
    FxImpactUnit = Impact,
    FxImpactProp = Impact,
    FxImpactWater = Impact,
    FxLandHitScale = 0.35, FxUnitHitScale = 0.35, FxPropHitScale = 0.35, FxWaterHitScale = 0.35,
    DestroyOnImpact = true,
}
TypeClass = GGP2302
