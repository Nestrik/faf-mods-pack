local TestGenerator = import('/mods/seraphim-acu-test-generator/lua/TestGenerator.lua')
local oldUEL0001 = UEL0001

UEL0001 = Class(oldUEL0001) {
    ProcessEnhancementGGATestGenerator = TestGenerator.Apply,
    ProcessEnhancementGGATestGeneratorRemove = TestGenerator.Remove,
}

TypeClass = UEL0001
