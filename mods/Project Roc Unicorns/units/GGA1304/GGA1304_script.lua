local SMassFabricationUnit = import('/lua/seraphimunits.lua').SMassFabricationUnit

GGA1304 = ClassUnit(SMassFabricationUnit) {
    OnStopBeingBuilt = function(self, builder, layer)
        SMassFabricationUnit.OnStopBeingBuilt(self, builder, layer)
        self.WorkAnimator = CreateAnimator(self)
        self.Trash:Add(self.WorkAnimator)
        self.WorkAnimator:PlayAnim(self:GetBlueprint().Display.AnimationActivate, true)
        self.WorkAnimator:SetRate(self.ConsumptionActive and 1 or 0)
    end,

    OnProductionPaused = function(self)
        SMassFabricationUnit.OnProductionPaused(self)
        if self.WorkAnimator then self.WorkAnimator:SetRate(0) end
    end,

    OnProductionUnpaused = function(self)
        SMassFabricationUnit.OnProductionUnpaused(self)
        if self.WorkAnimator then self.WorkAnimator:SetRate(1) end
    end,

    OnConsumptionActive = function(self)
        SMassFabricationUnit.OnConsumptionActive(self)
        if self.WorkAnimator then self.WorkAnimator:SetRate(1) end
    end,

    OnConsumptionInActive = function(self)
        SMassFabricationUnit.OnConsumptionInActive(self)
        if self.WorkAnimator then self.WorkAnimator:SetRate(0) end
    end,
}

TypeClass = GGA1304
