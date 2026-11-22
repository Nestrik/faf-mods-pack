-- Ring deployment only. Locomotion and projectile behaviour remain independent.
local function smooth(t) return t*t*(3-2*t) end
local function alive(unit) return not unit.Dead and not unit:BeenDestroyed() end

function DestroyEffects(unit)
    local r = unit.Ring
    if not r then return end
    for _, fx in ipairs(r.effects or {}) do fx:Destroy() end
    r.effects = {}
end

local function effects(unit)
    DestroyEffects(unit)
    local fx = CreateAttachedEmitter(unit, 'MainMuzzle', unit.Army,
        '/mods/Project Roc Unicorns/effects/emitters/razlom_ring_portal_emit.bp')
    unit.Trash:Add(fx)
    unit.Ring.effects = {fx}
end

local function holdAim(unit)
    local r = unit.Ring
    if r.homeYaw then return end
    r.homeYaw = CreateRotator(unit, 'MainYaw', 'y', 0, 180, 0, 0)
    r.homePitch = CreateRotator(unit, 'MainPitch', 'x', 0, 90, 0, 0)
    r.homeYaw:SetPrecedence(100)
    r.homePitch:SetPrecedence(100)
    unit.Trash:Add(r.homeYaw)
    unit.Trash:Add(r.homePitch)
end

local function releaseAim(unit)
    local r = unit.Ring
    if r.homeYaw then r.homeYaw:Destroy(); r.homeYaw = nil end
    if r.homePitch then r.homePitch:Destroy(); r.homePitch = nil end
end

function Initialize(unit)
    if unit.Ring then return end
    local r = {height=0, angle=0, ready=false, active=false, effects={}}
    unit.Ring = r
    r.lift = CreateSlider(unit, 'RingLift')
    r.lift:SetWorldUnits(true)
    r.lift:SetSpeed(4)
    r.lift:SetGoal(0,0,0)
    r.tilt = CreateRotator(unit, 'RingTilt', 'x', 0, 180, 0, 0)
    r.tilt:SetPrecedence(40)
    unit.Trash:Add(r.lift)
    unit.Trash:Add(r.tilt)
    holdAim(unit)
    unit:ForkThread(function(u)
        local t = 0
        while alive(u) do
            if not r.active then
                r.height = .045 * math.sin(t * math.pi)
                r.lift:SetGoal(0,r.height,0)
            end
            t = t + .1
            WaitTicks(1)
        end
    end)
end

local function move(unit, height, angle, ticks)
    local r = unit.Ring
    local h0, a0 = r.height, r.angle
    for i=1,ticks do
        if not alive(unit) then return false end
        local t = smooth(i/ticks)
        r.height = h0 + (height-h0)*t
        r.angle = a0 + (angle-a0)*t
        r.lift:SetGoal(0,r.height,0)
        r.tilt:SetGoal(r.angle)
        WaitTicks(1)
    end
    return alive(unit)
end

function Deploy(unit)
    Initialize(unit)
    local r = unit.Ring
    if r.ready then return end -- reacquired target during the repack grace period
    r.active = true
    r.ready = false
    -- Lift before tipping so the rim never swings through the armour.
    if not move(unit,2.05,r.angle,10) then return end
    if not move(unit,2.05,90,10) then return end
    releaseAim(unit)
    effects(unit)
    r.ready = true
end

function Stow(unit)
    local r = unit.Ring
    if not r then return end
    r.active = true
    r.ready = false
    DestroyEffects(unit)
    holdAim(unit)
    if not move(unit,2.05,0,10) then return end
    if not move(unit,0,0,10) then return end
    r.active = false
end
