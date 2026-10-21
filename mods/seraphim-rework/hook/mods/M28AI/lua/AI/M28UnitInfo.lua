-- GGA2401 and GGA2404 are short-range tactical artillery despite being TECH3 structures.
-- Keep its real tech/size categories and correct only M28's AI role filters.
-- This optional hook runs when M28AI imports its own UnitInfo module.
do
    local tacticalArtillery = categories.gga2401
    if categories.gga2404 then
        tacticalArtillery = tacticalArtillery and (tacticalArtillery + categories.gga2404) or categories.gga2404
    end
    if tacticalArtillery and refCategoryFixedT2Arti and refCategoryFixedT3Arti then
        refCategoryFixedT2Arti = refCategoryFixedT2Arti + tacticalArtillery
        refCategoryFixedT3Arti = refCategoryFixedT3Arti - tacticalArtillery

        -- These category expressions were constructed before this hook runs.
        -- Update them explicitly so firebases and threat handling agree.
        if refCategoryFirebaseSuitable then
            refCategoryFirebaseSuitable = refCategoryFirebaseSuitable + tacticalArtillery
        end
        if refCategoryDangerousToLand then
            refCategoryDangerousToLand = refCategoryDangerousToLand + tacticalArtillery
        end
        if refCategoryExperimentalLevel then
            refCategoryExperimentalLevel = refCategoryExperimentalLevel - tacticalArtillery
        end
        if refCategoryBigThreatCategories then
            refCategoryBigThreatCategories = refCategoryBigThreatCategories - tacticalArtillery
        end
    end
end

-- Recognize the real experimental energy producer for economy accounting.
-- Its construction choice is gated separately in the M28Factory hook; keep
-- refCategoryT3Power restricted to actual T3 units.
do
    if categories.gga1401 and refCategoryPower then
        refCategoryPower = refCategoryPower + categories.gga1401
    end
end
