local SEnergyCreationUnit = import('/lua/seraphimunits.lua').SEnergyCreationUnit

GGA1401 = ClassUnit(SEnergyCreationUnit) {
    OnStopBeingBuilt = function(self, builder, layer)
        SEnergyCreationUnit.OnStopBeingBuilt(self, builder, layer)

        -- Unit.OnStopBeingBuilt creates Defense.Shield; the ordinary shield
        -- toggle works independently of this generator's continuous production.
        self.Trash:Add(CreateAnimator(self):PlayAnim(self.Blueprint.Display.AnimationIdle, true))
    end,
}

TypeClass = GGA1401
