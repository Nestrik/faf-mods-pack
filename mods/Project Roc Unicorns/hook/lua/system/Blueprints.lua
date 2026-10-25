local FAFModBlueprints = ModBlueprints

function ModBlueprints(all_blueprints)
    FAFModBlueprints(all_blueprints)

    if all_blueprints.Unit then
        all_blueprints.Unit.xsb1104 = nil
    end
end
