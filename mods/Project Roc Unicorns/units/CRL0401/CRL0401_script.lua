local CConstructionUnit = import('/lua/cybranunits.lua').CConstructionUnit
local CDFMissileRedirectWeapon01 = import('/lua/sim/weapons/cybran/cdfmissileredirectweapon01.lua').CDFMissileRedirectWeapon01

local function CanAutoWork(unit)
    if unit.Dead or unit:IsPaused() then return false end
    -- The motion callback sets this state; nil is possible before the first move.
    if unit.HorzMotionState and unit.HorzMotionState != 'Stopped' then return false end
    if unit:IsUnitState('Moving') or unit:IsUnitState('Building')
        or unit:IsUnitState('Repairing') or unit:IsUnitState('Reclaiming')
        or unit:IsUnitState('Capturing') or unit:IsUnitState('Guarding')
        or unit:IsUnitState('Patrolling') or unit:IsUnitState('Attacking') then
        return false
    end
    local queue = unit:GetCommandQueue()
    return not queue or table.getn(queue) == 0
end

CRL0401 = ClassUnit(CConstructionUnit) {
    Weapons = { RedirectMissile = ClassWeapon(CDFMissileRedirectWeapon01) {} },
    OnMotionHorzEventChange = function(self, new, old)
        CConstructionUnit.OnMotionHorzEventChange(self, new, old)
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
    OnStopBeingBuilt = function(self, builder, layer)
        CConstructionUnit.OnStopBeingBuilt(self, builder, layer)
        self.Trash:Add(ForkThread(self.AutoWork, self))
    end,

    AutoWork = function(self)
        local preferRepair = true
        local idleSince = false
        while not self.Dead do
            if not CanAutoWork(self) then
                idleSince = false
            elseif not idleSince then
                idleSince = GetGameTick()
            elseif GetGameTick() - idleSince >= 10 then
                -- Require another full idle second before the next scan.
                idleSince = false
                local p = self:GetPosition()
                local radius = self:GetBlueprint().Economy.MaxBuildDistance
                local allies = self:GetAIBrain():GetUnitsAroundPoint(categories.ALLUNITS, p, radius, 'Ally') or {}
                local unfinished, damaged
                for _, unit in allies do
                    if unit != self and not unit.Dead then
                        if unit:GetFractionComplete() < 1 then
                            unfinished = unit
                            break
                        elseif not damaged and unit:GetHealth() < unit:GetMaxHealth() then
                            damaged = unit
                        end
                    end
                end
                if not CanAutoWork(self) then
                    -- A command or pause always wins over the automatic search.
                elseif unfinished then
                    IssueRepair({self}, unfinished)
                elseif damaged and preferRepair then
                    IssueRepair({self}, damaged)
                    preferRepair = false
                else
                    local objects = GetReclaimablesInRect(Rect(p[1]-radius, p[3]-radius, p[1]+radius, p[3]+radius)) or {}
                    local target
                    for _, object in objects do
                        if object and not IsUnit(object) and not object:BeenDestroyed() then
                            local op = object:GetPosition()
                            if VDist2(p[1], p[3], op[1], op[3]) < radius then
                                target = object
                                break
                            end
                        end
                    end
                    if target then
                        IssueReclaim({self}, target)
                        preferRepair = true
                    elseif damaged then
                        IssueRepair({self}, damaged)
                        preferRepair = false
                    end
                end
            end
            WaitTicks(1)
        end
    end,
}
TypeClass = CRL0401
