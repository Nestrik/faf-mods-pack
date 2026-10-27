local SStructureUnit = import('/lua/seraphimunits.lua').SStructureUnit
local SDFUltraChromaticBeamGenerator = import('/lua/seraphimweapons.lua').SDFUltraChromaticBeamGenerator

GGA2301 = Class(SStructureUnit) {
    OnStopBeingBuilt = function(self, builder, layer)
        SStructureUnit.OnStopBeingBuilt(self, builder, layer)

        self.PrismAnimator = CreateAnimator(self)
        self.Trash:Add(self.PrismAnimator)
        self.PrismAnimator:PlayAnim(self:GetBlueprint().Display.AnimationActivate, false)
        self:ForkThread(function(unit, animator)
            WaitFor(animator)
            if not unit:IsDead() then
                animator:PlayAnim(unit:GetBlueprint().Display.AnimationIdle, true)
            end
        end, self, self.PrismAnimator)
    end,

    Weapons = {
        MainGun = Class(SDFUltraChromaticBeamGenerator) {},
    },
}

TypeClass = GGA2301
