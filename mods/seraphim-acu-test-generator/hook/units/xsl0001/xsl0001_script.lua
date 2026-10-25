local TestGenerator = import('/mods/seraphim-acu-test-generator/lua/TestGenerator.lua')
local oldXSL0001 = XSL0001

XSL0001 = Class(oldXSL0001) {
    ProcessEnhancementGGATestGenerator = TestGenerator.Apply,
    ProcessEnhancementGGATestGeneratorRemove = TestGenerator.Remove,
}

TypeClass = XSL0001
