local FAFModBlueprints = ModBlueprints

function ModBlueprints(all_blueprints)
    FAFModBlueprints(all_blueprints)

    if all_blueprints.Unit then
        all_blueprints.Unit.xsb1104 = nil
        -- Keep Vothuun disabled even if an old blueprint remains in a source
        -- archive or an installation updated by merging folders.
        all_blueprints.Unit.gga2401 = nil
        -- Removed Cyclops: suppress stale files when users merge an update.
        all_blueprints.Unit.gga0404 = nil
    end
end

-- FAF recalculates density from health; apply the narrow override after processing.
local function SetSonicDensity(blueprints)
    local unit = blueprints.Unit and blueprints.Unit.uel0210
    if unit then unit.AverageDensity = 45000 end
end

local PreviousPostModBlueprints = PostModBlueprints
function PostModBlueprints(blueprints)
    PreviousPostModBlueprints(blueprints)
    SetSonicDensity(blueprints)
end

local PreviousBatchProcessUnits = BatchProcessUnits
function BatchProcessUnits(blueprints)
    PreviousBatchProcessUnits(blueprints)
    SetSonicDensity(blueprints)
end
