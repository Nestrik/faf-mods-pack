local TestGenerator = import('/mods/seraphim-acu-test-generator/lua/TestGenerator.lua')
local oldUAL0001 = UAL0001

UAL0001 = Class(oldUAL0001) {
    ProcessEnhancementGGATestGenerator = TestGenerator.Apply,
    ProcessEnhancementGGATestGeneratorRemove = TestGenerator.Remove,
}

TypeClass = UAL0001
