local PreviousModBlueprints = ModBlueprints

local function SetShieldAssistCosts(shield, economy)
    -- FAF uses 75% of the owner's build costs for shields without assist rates.
    if shield.AssistCostEnergyPerBuildRate == nil then
        local buildTime = math.max(economy.BuildTime or 0.1, 0.1)
        shield.AssistCostEnergyPerBuildRate = 0.75 * (economy.BuildCostEnergy or 0) / buildTime
    end
    shield.AssistCostMassPerBuildRate = 0
end

function ModBlueprints(allBlueprints)
    PreviousModBlueprints(allBlueprints)

    for _, bp in pairs(allBlueprints.Unit) do
        if bp.CategoriesHash and bp.CategoriesHash.SHIELD and bp.Economy then
            if bp.Defense and bp.Defense.Shield then
                SetShieldAssistCosts(bp.Defense.Shield, bp.Economy)
            end
            for _, enhancement in pairs(bp.Enhancements or {}) do
                if type(enhancement) == 'table' and enhancement.ShieldMaxHealth then
                    SetShieldAssistCosts(enhancement, bp.Economy)
                end
            end
        end
    end
end
