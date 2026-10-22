local SEnergyCreationUnit = import('/lua/seraphimunits.lua').SEnergyCreationUnit

GGA1401 = ClassUnit(SEnergyCreationUnit) {
    -- The stock XSB1301 rising light, expanding ground rings and distortion.
    -- SEnergyCreationUnit creates these on the root after construction.
    AmbientEffects = 'ST3PowerAmbient',

    OnStopBeingBuilt = function(self, builder, layer)
        SEnergyCreationUnit.OnStopBeingBuilt(self, builder, layer)

        -- Unit.OnStopBeingBuilt creates Defense.Shield; the ordinary shield
        -- toggle works independently of this generator's continuous production.
        self.Trash:Add(CreateAnimator(self):PlayAnim(self.Blueprint.Display.AnimationIdle, true))
    end,
}

TypeClass = GGA1401
