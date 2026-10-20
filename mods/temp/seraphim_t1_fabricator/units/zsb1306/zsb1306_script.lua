local SMassFabricationUnit = import('/lua/seraphimunits.lua').SMassFabricationUnit

ZSB1306 = ClassUnit(SMassFabricationUnit) {
    OnStopBeingBuilt = function(self, builder, layer)
        SMassFabricationUnit.OnStopBeingBuilt(self, builder, layer)
        if self.HyalaHiddenForUpgrade then
            self:ShowBone(0, true)
            self.HyalaHiddenForUpgrade = nil
        end
        self:PlayActiveAnimation()
    end,

    PlayActiveAnimation = function(self)
        if self.UpgradingVisual then return end
        if not self.WorkAnimator then
            self.WorkAnimator = CreateAnimator(self)
            self.Trash:Add(self.WorkAnimator)
            self.WorkAnimator:PlayAnim(self:GetBlueprint().Display.AnimationActivate, true)
        end
        self.WorkAnimator:SetRate(self.ConsumptionActive and 1 or 0)
    end,

    GetUpgradeAnimation = function(self, unitBeingBuilt)
        local display = self:GetBlueprint().Display
        if not display.AnimationUpgrade then return nil end
        self.UpgradingVisual = true
        if self.WorkAnimator then
            self.WorkAnimator:Destroy()
            self.WorkAnimator = nil
        end
        -- This SCM has the destination rig. Its SCA starts in the source layout.
        self:SetMesh(display.UpgradeMeshBlueprint)
        self.ActiveUpgradeTarget = unitBeingBuilt
        unitBeingBuilt.HyalaHiddenForUpgrade = true
        unitBeingBuilt:HideBone(0, true)
        -- StructureUnit.UpgradingState controls this animator with SetAnimationFraction.
        return display.AnimationUpgrade
    end,

    RestoreHyalaMesh = function(self)
        if self.AnimatorUpgradeManip then
            self.AnimatorUpgradeManip:Destroy()
            self.AnimatorUpgradeManip = nil
        end
        if self.UpgradingVisual then
            self:SetMesh(self:GetBlueprint().Display.MeshBlueprint)
            self.UpgradingVisual = false
        end
        local target = self.ActiveUpgradeTarget
        if target and not target.Dead then
            target:ShowBone(0, true)
            target.HyalaHiddenForUpgrade = nil
        end
        self.ActiveUpgradeTarget = nil
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

    UpgradingState = State(SMassFabricationUnit.UpgradingState) {
        OnFailedToBuild = function(self)
            self:RestoreHyalaMesh()
            SMassFabricationUnit.UpgradingState.OnFailedToBuild(self)
        end,
    },
}

TypeClass = ZSB1306
