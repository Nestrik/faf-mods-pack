-- Add handlers for the test enhancement to the stock Seraphim ACU script.
do
    local oldXSL0001 = XSL0001

    XSL0001 = Class(oldXSL0001) {
        ProcessEnhancementGGATestGenerator = function(self, bp)
            local economy = self.Blueprint.Economy

            self:SetProductionPerSecondEnergy(
                (economy.ProductionPerSecondEnergy or 0) + (bp.ProductionPerSecondEnergy or 0)
            )
            self:SetProductionPerSecondMass(
                (economy.ProductionPerSecondMass or 0) + (bp.ProductionPerSecondMass or 0)
            )

            if bp.NewVisionRadius then
                self:SetIntelRadius('Vision', bp.NewVisionRadius)
            end

            local buildRateIncrease = (bp.NewBuildRate or economy.BuildRate) - economy.BuildRate
            if buildRateIncrease > 0 then
                if not Buffs['GGATestGeneratorBuildRate'] then
                    BuffBlueprint {
                        Name = 'GGATestGeneratorBuildRate',
                        DisplayName = 'GGATestGeneratorBuildRate',
                        BuffType = 'GGATESTGENERATORBUILDRATE',
                        Stacks = 'REPLACE',
                        Duration = -1,
                        Affects = {
                            BuildRate = {
                                Add = buildRateIncrease,
                                Mult = 1,
                            },
                        },
                    }
                end

                import('/lua/sim/buff.lua').ApplyBuff(self, 'GGATestGeneratorBuildRate')
            end
        end,

        ProcessEnhancementGGATestGeneratorRemove = function(self)
            local economy = self.Blueprint.Economy

            self:SetProductionPerSecondEnergy(economy.ProductionPerSecondEnergy or 0)
            self:SetProductionPerSecondMass(economy.ProductionPerSecondMass or 0)

            local visionRadius = self.Blueprint.Intel and self.Blueprint.Intel.VisionRadius
            if visionRadius then
                self:SetIntelRadius('Vision', visionRadius)
            end

            local buff = import('/lua/sim/buff.lua')
            if buff.HasBuff(self, 'GGATestGeneratorBuildRate') then
                buff.RemoveBuff(self, 'GGATestGeneratorBuildRate')
            end
        end,
    }

    TypeClass = XSL0001
end
