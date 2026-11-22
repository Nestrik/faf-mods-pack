-- Engineer tabs include every EXPERIMENTAL blueprint in T4, even if it also
-- has TECH2. Keep Raider in T2 while preserving its simulation category.
local OriginalCategoryFilter = EntityCategoryFilterDown
local OriginalOnSelection = OnSelection
local SortingSelection = false

function EntityCategoryFilterDown(category, units)
    local result = OriginalCategoryFilter(category, units)
    if SortingSelection and category == categories.EXPERIMENTAL and result then
        for i = table.getn(result), 1, -1 do
            if string.lower(result[i]) == 'crl0402' then
                table.remove(result, i)
            end
        end
    end
    return result
end

function OnSelection(buildableCategories, selection, isOldSelection)
    local wasSorting = SortingSelection
    SortingSelection = true
    local ok, result = pcall(OriginalOnSelection, buildableCategories, selection, isOldSelection)
    SortingSelection = wasSorting
    if not ok then
        error(result)
    end
    return result
end
