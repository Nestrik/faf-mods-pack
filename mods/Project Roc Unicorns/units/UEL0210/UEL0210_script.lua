local TShieldLandUnit = import('/lua/terranunits.lua').TShieldLandUnit
local Beam = import('/lua/terranweapons.lua').TOrbitalDeathLaserBeamWeapon

-- A direct line from the emitter must clear terrain and intervening wall units.
-- The collision beam itself handles other physical impacts in the engine.
local function HasClearLine(weapon)
    if not weapon:WeaponHasTarget() then return true end
    local target = weapon:GetCurrentTargetPos()
    if not target then return true end
    local origin = weapon.unit:GetPosition('Turret_Muzzle')
    local dx, dy, dz = target[1]-origin[1], target[2]-origin[2], target[3]-origin[3]
    local steps = math.max(1, math.ceil(math.sqrt(dx*dx+dz*dz)*2))
    for i = 1, steps-1 do
        local t = i / steps
        if GetTerrainHeight(origin[1]+dx*t, origin[3]+dz*t) > origin[2]+dy*t+.03 then return false end
    end
    local intended = weapon:GetCurrentTarget()
    if intended and intended.GetSource and not intended:BeenDestroyed() then intended = intended:GetSource() end
    local walls = GetUnitsInRect(Rect(math.min(origin[1],target[1])-2, math.min(origin[3],target[3])-2, math.max(origin[1],target[1])+2, math.max(origin[3],target[3])+2))
    local length2 = dx*dx+dz*dz
    for _, wall in ipairs(walls or {}) do
        if length2 > .000001 and wall ~= intended and wall ~= weapon.unit and not wall.Dead and not wall:BeenDestroyed() and EntityCategoryContains(categories.WALL, wall) then
            local pos, bp = wall:GetPosition(), wall:GetBlueprint()
            local ox, oz = origin[1]-pos[1]-(bp.CollisionOffsetX or 0), origin[3]-pos[3]-(bp.CollisionOffsetZ or 0)
            local radius = math.max(bp.SizeX or 1,bp.SizeZ or 1)*.5+.1
            local dot = ox*dx+oz*dz
            local disc = dot*dot-length2*(ox*ox+oz*oz-radius*radius)
            if disc >= 0 then
                local half = math.sqrt(disc)
                local enter, leave = math.max(.001,(-dot-half)/length2), math.min(.999,(-dot+half)/length2)
                local bottom = pos[2]+(bp.CollisionOffsetY or 0)-.1
                local top = bottom+(bp.SizeY or 1)+.2
                if math.abs(dy)<.000001 then
                    if enter<=leave and origin[2]>=bottom and origin[2]<=top then return false end
                else
                    local a,b = (bottom-origin[2])/dy,(top-origin[2])/dy
                    enter,leave=math.max(enter,math.min(a,b)),math.min(leave,math.max(a,b))
                    if enter<=leave then return false end
                end
            end
        end
    end
    return true
end

UEL0210 = ClassUnit(TShieldLandUnit) {
    OnMotionHorzEventChange = function(self, new, old)
        TShieldLandUnit.OnMotionHorzEventChange(self, new, old)
        if self.Dead then return end
        if new == 'Stopped' then
            if self.TrackAnimator then self.TrackAnimator:SetRate(0) end
        elseif old == 'Stopped' then
            if not self.TrackAnimator then
                self.TrackAnimator = self.Trash:Add(CreateAnimator(self, true))
                self.TrackAnimator:PlayAnim(self.Blueprint.Display.AnimationWalk, true)
                self.TrackAnimator:SetDirectionalAnim(true)
            end
            self.TrackAnimator:SetRate(self.Blueprint.Display.AnimationWalkRate or 1)
        end
    end,

    Weapons = {
        MainGun = ClassWeapon(Beam) {
            CanWeaponFire = function(self)
                return Beam.CanWeaponFire(self) and HasClearLine(self)
            end,
            CreateProjectileAtMuzzle = function(self, muzzle)
                if HasClearLine(self) then return Beam.CreateProjectileAtMuzzle(self, muzzle) end
            end,
        },
    },
}
TypeClass = UEL0210
