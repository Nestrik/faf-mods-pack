local FAFModBlueprints = ModBlueprints

function ModBlueprints(all_blueprints)
    FAFModBlueprints(all_blueprints)

    local seraphimCommander = all_blueprints.Unit and all_blueprints.Unit.xsl0001
    if not seraphimCommander then
        return
    end

    seraphimCommander.Enhancements = seraphimCommander.Enhancements or {}
    seraphimCommander.Enhancements.GGATestGenerator = {
        BuildCostEnergy = 1,
        BuildCostMass = 1,
        BuildTime = 1,
        Icon = 'ras',
        Name = 'Test Resource Generator',
        NewBuildRate = 2500,
        NewVisionRadius = 2000,
        ProductionPerSecondEnergy = 100000,
        ProductionPerSecondMass = 2000,
        ShowBones = { 'Back_Upgrade' },
        Slot = 'Back',
        UpgradeEffectBones = { 'Back_Upgrade' },
        UpgradeUnitAmbientBones = { 'Body' },
    }

    seraphimCommander.Enhancements.GGATestGeneratorRemove = {
        BuildCostEnergy = 1,
        BuildCostMass = 1,
        BuildTime = 1,
        HideBones = { 'Back_Upgrade' },
        Icon = 'ras',
        Name = 'Remove Test Resource Generator',
        Prerequisite = 'GGATestGenerator',
        RemoveEnhancements = {
            'GGATestGenerator',
            'GGATestGeneratorRemove',
        },
        Slot = 'Back',
    }
end
