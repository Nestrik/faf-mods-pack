-- Straight-shot terrain/wall clearance and visible alternate-target selection.
local function SourceTarget(target)
    if target and target.GetSource and not target:BeenDestroyed() then return target:GetSource() end
    return target
end

local function ClearToPoint(weapon, muzzle, target, intendedTarget)
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
    -- Walls are units, not terrain. Test the complete 3-D segment against
    -- their collision-height and horizontal volume. The intended wall target
    -- is excluded so the player can destroy the wall itself.
    local walls = GetUnitsInRect(Rect(math.min(origin[1],target[1])-2,
        math.min(origin[3],target[3])-2, math.max(origin[1],target[1])+2,
        math.max(origin[3],target[3])+2))
    local length2 = dx*dx + dz*dz
    for _, wall in ipairs(walls or {}) do
        if wall ~= weapon.unit and wall ~= intendedTarget and not wall.Dead
            and not wall:BeenDestroyed() and EntityCategoryContains(categories.WALL, wall) then
            local pos = wall:GetPosition()
            local bp = wall:GetBlueprint()
            local wx = pos[1] + (bp.CollisionOffsetX or 0)
            local wz = pos[3] + (bp.CollisionOffsetZ or 0)
            local radius = math.max(bp.SizeX or 1, bp.SizeZ or 1) * .5 + .10
            if length2 > .000001 then
                local ox, oz = origin[1]-wx, origin[3]-wz
                local dot = ox*dx+oz*dz
                local discriminant = dot*dot-length2*(ox*ox+oz*oz-radius*radius)
                if discriminant >= 0 then
                    local half = math.sqrt(discriminant)
                    local enter = math.max(.001,(-dot-half)/length2)
                    local leave = math.min(.999,(-dot+half)/length2)
                    local bottom = pos[2] + (bp.CollisionOffsetY or 0) - .10
                    local top = bottom + (bp.SizeY or 1) + .20
                    if math.abs(dy) < .000001 then
                        if enter <= leave and origin[2] >= bottom and origin[2] <= top then return false end
                    else
                        local a, b = (bottom-origin[2])/dy, (top-origin[2])/dy
                        enter = math.max(enter,math.min(a,b))
                        leave = math.min(leave,math.max(a,b))
                        if enter <= leave then return false end
                    end
                end
            end
        end
    end
    return true
end

function IsClear(weapon, muzzle)
    if not weapon:WeaponHasTarget() then return true end
    local target = weapon:GetCurrentTargetPos()
    return not target or ClearToPoint(weapon, muzzle, target, SourceTarget(weapon:GetCurrentTarget()))
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
        if ClearToPoint(weapon, muzzle, candidate.Aim, candidate.Unit) then return candidate.Unit end
    end
end


-- Read only the active order. Do not replace, clear or reorder player commands.
local CommandTypes = import('/lua/sim/commands/shared.lua').UnitQueueDataToCommand
function GetOrderedAttack(unit)
    local queue = unit:GetCommandQueue()
    local order = queue and queue[1]
    local info = order and CommandTypes[order.commandType]
    if not info or info.Type ~= 'Attack' then return nil end
    local target = order.target
    if target then
        if target.Dead or target:BeenDestroyed() then return nil end
        local pos = target:GetPosition()
        return {pos[1], pos[2] + (target:GetBlueprint().SizeY or 1)*.5, pos[3]}, target
    end
    if order.targetId then return nil end -- a destroyed entity is not a ground attack
    if order.x and order.y and order.z then return {order.x, order.y+.1, order.z} end
end

function OrderedAttackIsBlocked(weapon)
    local aim, target = GetOrderedAttack(weapon.unit)
    return aim and not ClearToPoint(weapon, 'MainMuzzle', aim, target) or false
end
