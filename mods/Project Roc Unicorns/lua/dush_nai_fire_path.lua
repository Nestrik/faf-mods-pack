-- Straight-shot terrain check and conservative blocked-target recovery.
local function ClearToPoint(weapon, muzzle, target)
    local origin = weapon.unit:GetPosition(muzzle)
    local dx = target[1] - origin[1]
    local dy = target[2] - origin[2]
    local dz = target[3] - origin[3]
    local distance = math.sqrt(dx * dx + dz * dz)
    -- Half-unit sampling catches narrow ridges as well as broad mountains.
    -- Skip endpoints: the target may sit directly on the terrain surface.
    local steps = math.max(1, math.ceil(distance * 2))
    for i = 1, steps - 1 do
        local t = i / steps
        local x = origin[1] + dx * t
        local y = origin[2] + dy * t
        local z = origin[3] + dz * t
        if GetTerrainHeight(x, z) > y + .03 then return false end
    end
    return true
end

function IsClear(weapon, muzzle)
    if not weapon:WeaponHasTarget() then return true end
    local target = weapon:GetCurrentTargetPos()
    return not target or ClearToPoint(weapon, muzzle, target)
end

local function KnownNow(unit, army)
    local blip = unit:GetBlip(army)
    return blip and (blip:IsSeenNow(army) or blip:IsOnRadar(army)
        or blip:IsOnSonar(army) or blip:IsOnOmni(army))
end

function FindClearTarget(weapon, muzzle, rejected)
    local unit = weapon.unit
    local army = unit.Army
    local bp = weapon.Blueprint
    local origin = unit:GetPosition(muzzle)
    if rejected and rejected.GetSource and not rejected:BeenDestroyed() then rejected = rejected:GetSource() end
    local priorities = weapon.ClearTargetPriorities
    if not priorities then
        priorities = {}
        for _, text in ipairs(bp.TargetPriorities or {'ALLUNITS'}) do
            table.insert(priorities, ParseEntityCategory(text))
        end
        weapon.ClearTargetPriorities = priorities
    end
    local candidates = {}
    local maximum = bp.MaxRadius
    local minimum = bp.MinRadius or 0
    local units = unit:GetAIBrain():GetUnitsAroundPoint(
        categories.ALLUNITS - categories.AIR - categories.UNTARGETABLE, origin, maximum, 'Enemy')
    for _, target in ipairs(units or {}) do
        if target ~= rejected and not target.Dead and not target:BeenDestroyed()
            and KnownNow(target, army) then
            local layer = target:GetCurrentLayer()
            if layer == 'Land' or layer == 'Water' then
                local pos = target:GetPosition()
                local dx, dz = pos[1] - origin[1], pos[3] - origin[3]
                local distance = dx * dx + dz * dz
                if distance <= maximum * maximum and distance >= minimum * minimum then
                    local rank = table.getn(priorities) + 1
                    for i, category in ipairs(priorities) do
                        if EntityCategoryContains(category, target) then rank = i; break end
                    end
                    local aim = {pos[1], pos[2] + (target:GetBlueprint().SizeY or 1) * .5, pos[3]}
                    table.insert(candidates, {Unit=target, Aim=aim, Rank=rank, Distance=distance, Id=target:GetEntityId()})
                end
            end
        end
    end
    table.sort(candidates, function(a, b)
        if a.Rank ~= b.Rank then return a.Rank < b.Rank end
        if a.Distance ~= b.Distance then return a.Distance < b.Distance end
        return a.Id < b.Id
    end)
    for _, candidate in ipairs(candidates) do
        if ClearToPoint(weapon, muzzle, candidate.Aim) then return candidate.Unit end
    end
end
