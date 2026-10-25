local TestGenerator = import('/mods/seraphim-acu-test-generator/lua/TestGenerator.lua')
local oldURL0001 = URL0001

URL0001 = Class(oldURL0001) {
    ProcessEnhancementGGATestGenerator = TestGenerator.Apply,
    ProcessEnhancementGGATestGeneratorRemove = TestGenerator.Remove,
}

TypeClass = URL0001
