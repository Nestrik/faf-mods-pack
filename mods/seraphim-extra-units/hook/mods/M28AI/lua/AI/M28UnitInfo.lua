-- Optional M28AI tactical-artillery classification for Vael-Itha only.
do
    local tacticalArtillery = categories.gga2404
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
