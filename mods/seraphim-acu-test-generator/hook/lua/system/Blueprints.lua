local FAFModBlueprints = ModBlueprints

-- Stock back upgrade bones and resource enhancement icons differ by faction.
local CommanderVisuals = {
    uel0001 = { Bone = 'Back_Upgrade_B01', AmbientBone = 'UEL0001', Icon = 'isb' },
    ual0001 = { Bone = 'Back_Upgrade', AmbientBone = 'UAL0001', Icon = 'ras' },
    url0001 = { Bone = 'Back_Upgrade', AmbientBone = 'URL0001', Icon = 'ras' },
    xsl0001 = { Bone = 'Back_Upgrade', AmbientBone = 'Body', Icon = 'ras' },
}

function ModBlueprints(all_blueprints)
    FAFModBlueprints(all_blueprints)

    if not all_blueprints.Unit then
        return
    end

    for id, visuals in pairs(CommanderVisuals) do
        local commander = all_blueprints.Unit[id]
        if commander then
            commander.Enhancements = commander.Enhancements or {}
            commander.Enhancements.GGATestGenerator = {
                BuildCostEnergy = 1,
                BuildCostMass = 1,
                BuildTime = 1,
                Icon = visuals.Icon,
                Name = 'Test Resource Generator',
                NewBuildRate = 2500,
                NewVisionRadius = 2000,
                ProductionPerSecondEnergy = 100000,
                ProductionPerSecondMass = 2000,
                ShowBones = { visuals.Bone },
                Slot = 'Back',
                UpgradeEffectBones = { visuals.Bone },
                UpgradeUnitAmbientBones = { visuals.AmbientBone },
            }

            commander.Enhancements.GGATestGeneratorRemove = {
                BuildCostEnergy = 1,
                BuildCostMass = 1,
                BuildTime = 1,
                HideBones = { visuals.Bone },
                Icon = visuals.Icon,
                Name = 'Remove Test Resource Generator',
                Prerequisite = 'GGATestGenerator',
                RemoveEnhancements = {
                    'GGATestGenerator',
                    'GGATestGeneratorRemove',
                },
                Slot = 'Back',
            }
        end
    end
end
