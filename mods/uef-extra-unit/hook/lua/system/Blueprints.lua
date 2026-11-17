-- FAF 3840 derives unit density from health in BatchProcessUnits. Apply this
-- one-unit override after either standard blueprint processing path.
local function SetOverlordDensity(blueprints)
    local unit = blueprints.Unit and blueprints.Unit.uel0209
    if unit then unit.AverageDensity = 45000 end
end

local PreviousPostModBlueprints = PostModBlueprints
function PostModBlueprints(blueprints)
    PreviousPostModBlueprints(blueprints)
    SetOverlordDensity(blueprints)
end

local PreviousBatchProcessUnits = BatchProcessUnits
function BatchProcessUnits(blueprints)
    PreviousBatchProcessUnits(blueprints)
    SetOverlordDensity(blueprints)
end
