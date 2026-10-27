-- Shared enhancement handlers for the four stock faction ACUs.
local Buff = import('/lua/sim/buff.lua')

local function GetBuildRateBuffName(unit)
    -- Buff blueprints are global; keep each commander's base build rate separate.
    return 'GGATestGeneratorBuildRate_' .. unit:GetUnitId()
end

function Apply(self, bp)
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
        local buffName = GetBuildRateBuffName(self)
        if not Buffs[buffName] then
            BuffBlueprint {
                Name = buffName,
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

        Buff.ApplyBuff(self, buffName)
    end
end

function Remove(self)
    local economy = self.Blueprint.Economy

    self:SetProductionPerSecondEnergy(economy.ProductionPerSecondEnergy or 0)
    self:SetProductionPerSecondMass(economy.ProductionPerSecondMass or 0)

    local visionRadius = self.Blueprint.Intel and self.Blueprint.Intel.VisionRadius
    if visionRadius then
        self:SetIntelRadius('Vision', visionRadius)
    end

    local buffName = GetBuildRateBuffName(self)
    if Buff.HasBuff(self, buffName) then
        Buff.RemoveBuff(self, buffName)
    end
end
