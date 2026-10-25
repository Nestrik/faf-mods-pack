-- Optional M28AI v327 support for Uya-Iava. Never edit M28AI's installed files.
-- Upgrade a normal T3 power choice only after the economy can support it.
local SeraphimReworkGetBlueprint = GetBlueprintThatCanBuildOfCategory

function GetBlueprintThatCanBuildOfCategory(aiBrain, category, builder, slowest, fastest,
    cheapest, mustBuildCategory, ignoreTech, maxSkirtSize, mostExpensive)

    local reactor = categories.gga1401
    local ordinaryCategory = category
    if reactor and category then
        -- refCategoryPower recognizes the reactor for accounting. Exclude it
        -- from the ordinary random/priority choice until the checks below pass.
        ordinaryCategory = category - reactor
    end
    local selected = SeraphimReworkGetBlueprint(aiBrain, ordinaryCategory, builder,
        slowest, fastest, cheapest, mustBuildCategory, ignoreTech, maxSkirtSize, mostExpensive)

    if reactor and selected == 'xsb1301' and not cheapest and not slowest and not fastest
        and not mustBuildCategory and aiBrain and builder
        and aiBrain:GetEconomyIncome('MASS') >= 8
        and aiBrain:GetEconomyIncome('ENERGY') >= 1000
        and aiBrain:GetEconomyStored('MASS') >= 5000
        and aiBrain:GetEconomyStoredRatio('ENERGY') >= 0.5
        and aiBrain:GetCurrentUnits(reactor) == 0
        and GetGameTimeSeconds() >= (aiBrain.SeraphimReworkNextReactorChoice or 0)
    then
        -- M28 uses per-tick income: 8/1000 means 80 mass/s and 10,000 energy/s.
        -- Calling its original selector retains CanBuild, unit restrictions and
        -- maximum skirt checks. Both power generators use the same 8x8 skirt.
        local candidate = SeraphimReworkGetBlueprint(aiBrain, reactor, builder,
            false, false, false, nil, ignoreTech, maxSkirtSize, false)
        if candidate then
            -- Avoid handing the same large project to several idle engineers
            -- before the first foundation exists. Failed placement can retry.
            aiBrain.SeraphimReworkNextReactorChoice = GetGameTimeSeconds() + 60
            return candidate
        end
    end

    return selected
end
