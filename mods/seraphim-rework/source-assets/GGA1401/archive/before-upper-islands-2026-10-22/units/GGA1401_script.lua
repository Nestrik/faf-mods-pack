local SEnergyCreationUnit = import('/lua/seraphimunits.lua').SEnergyCreationUnit
local Ythotha = import('/units/xsl0401/xsl0401_script.lua').XSL0401

GGA1401 = ClassUnit(SEnergyCreationUnit) {
    -- The stock XSB1301 rising light, expanding ground rings and distortion.
    -- SEnergyCreationUnit creates these on the root after construction.
    AmbientEffects = 'ST3PowerAmbient',

    -- Use Ythotha's actual residual-energy unit and its native spawn effects.
    SpawnEffects = Ythotha.SpawnEffects,
    SpawnElectroStorm = Ythotha.SpawnElectroStorm,

    DeathWeaponEnabled = false,
    PlayDestructionEffects = false,
    ShowUnitDestructionDebris = false,

    OnStopBeingBuilt = function(self, builder, layer)
        SEnergyCreationUnit.OnStopBeingBuilt(self, builder, layer)

        -- Unit.OnStopBeingBuilt creates Defense.Shield; the ordinary shield
        -- toggle works independently of this generator's continuous production.
        self.Trash:Add(CreateAnimator(self):PlayAnim(self.Blueprint.Display.AnimationIdle, true))
    end,

    DeathThread = function(self, overkillRatio, instigator)
        -- Match Ythotha: unfinished construction does not release an Othuy.
        -- Reclaim does not enter this thread, so ordinary recycling is safe.
        if self:GetFractionComplete() == 1 then
            self:SpawnElectroStorm()
        end

        -- Retain native effect cleanup and reclaimable wreckage. Class flags
        -- above suppress the default explosion and flying destruction debris.
        SEnergyCreationUnit.DeathThread(self, overkillRatio, instigator)
    end,
}

TypeClass = GGA1401
