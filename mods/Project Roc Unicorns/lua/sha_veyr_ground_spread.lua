-- Spread is a disk on the surface, never a random pitch/yaw cone.
function Apply(projectile, target, radius, speed)
    if not projectile or projectile:BeenDestroyed() or not target then return end
    local angle = 2 * math.pi * Random()
    local distance = radius * math.sqrt(Random())
    local x = target[1] + distance * math.cos(angle)
    local z = target[3] + distance * math.sin(angle)
    -- Keep the impact point inside the map, including shots near its edge.
    local size = ScenarioInfo and ScenarioInfo.size
    if size then
        x = math.max(.05, math.min(size[1] - .05, x))
        z = math.max(.05, math.min(size[2] - .05, z))
    end
    -- Aim just below the surface to guarantee crossing it instead of skimming.
    local y = GetSurfaceHeight(x, z) - .05
    local origin = projectile:GetPosition()
    local dx, dy, dz = x-origin[1], y-origin[2], z-origin[3]
    local length = math.sqrt(dx*dx + dy*dy + dz*dz)
    if length < .001 then return end
    projectile:SetNewTargetGroundXYZ(x, y, z)
    projectile:SetVelocity(dx / length, dy / length, dz / length)
    projectile:SetVelocity(speed)
end
