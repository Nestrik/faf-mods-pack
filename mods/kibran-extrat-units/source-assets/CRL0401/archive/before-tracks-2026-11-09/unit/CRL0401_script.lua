local CConstructionUnit = import('/lua/cybranunits.lua').CConstructionUnit

CRL0401 = ClassUnit(CConstructionUnit) {
    OnStopBeingBuilt = function(self, builder, layer)
        CConstructionUnit.OnStopBeingBuilt(self, builder, layer)
        self.Trash:Add(ForkThread(self.AutoWork, self))
    end,

    AutoWork = function(self)
        -- A separate, invisible engineer allows reclaim without replacing the
        -- vehicle's move/patrol queue. It uses native reclaim and its economy.
        local p = self:GetPosition()
        local worker = CreateUnitHPR('CRL0001', self:GetArmy(), p[1], p[2], p[3], 0, 0, 0)
        if not worker then
            WARN('CRL0401: could not create automatic reclaim worker')
            return
        end
        self.Trash:Add(worker)
        local radius = self:GetBlueprint().Economy.MaxBuildDistance
        local target = false
        local scanTicks = 0
        local preferRepair = false
        local lastX, lastY, lastZ = p[1], p[2], p[3]
        while not self.Dead and not worker.Dead do
            p = self:GetPosition()
            if p[1] != lastX or p[2] != lastY or p[3] != lastZ then
                Warp(worker, p)
                lastX, lastY, lastZ = p[1], p[2], p[3]
            end
            -- Do not double the station's build power during manual work.
            local busy = self:IsPaused() or self:IsUnitState('Repairing')
                or self:IsUnitState('Building') or self:IsUnitState('Reclaiming')
                or self:IsUnitState('Capturing')
            if target then
                if target:BeenDestroyed() then
                    target = false
                    preferRepair = true
                else
                    local tp = target:GetPosition()
                    if busy or VDist2(p[1], p[3], tp[1], tp[3]) >= radius then
                        IssueClearCommands({worker})
                        target = false
                    end
                end
            end

            if scanTicks <= 0 and not busy then
                scanTicks = 20
                worker:SetBuildRate(self:GetBuildRate())
                local workerQueue = worker:GetCommandQueue()
                if target and not worker:IsUnitState('Reclaiming') and (not workerQueue or table.getn(workerQueue) == 0) then
                    target = false
                end
                local queue = self:GetCommandQueue()
                local canRepair = not target and (not queue or table.getn(queue) == 0)
                local repaired = false
                if canRepair and preferRepair then
                    local allies = self:GetAIBrain():GetUnitsAroundPoint(categories.ALLUNITS, p, radius, 'Ally') or {}
                    for _, unit in allies do
                        if unit != self and unit != worker and not unit.Dead and unit:GetFractionComplete() == 1 and unit:GetHealth() < unit:GetMaxHealth() then
                            IssueRepair({self}, unit)
                            repaired = true
                            break
                        end
                    end
                    preferRepair = false
                end
                if not repaired and not target and not worker:IsUnitState('Reclaiming') then
                    local rect = Rect(p[1]-radius, p[3]-radius, p[1]+radius, p[3]+radius)
                    local objects = GetReclaimablesInRect(rect)
                    if objects then
                        for _, object in objects do
                            if object and not IsUnit(object) and not object:BeenDestroyed() then
                                local op = object:GetPosition()
                                if VDist2(p[1], p[3], op[1], op[3]) < radius then
                                    target = object
                                    IssueReclaim({worker}, object)
                                    break
                                end
                            end
                        end
                    end
                end
                -- Auto-repair retains the normal vehicle command queue and
                -- yields to automatic reclaim and to player-issued orders.
                if not repaired and canRepair and not target then
                    local allies = self:GetAIBrain():GetUnitsAroundPoint(categories.ALLUNITS, p, radius, 'Ally') or {}
                    for _, unit in allies do
                        if unit != self and unit != worker and not unit.Dead and unit:GetFractionComplete() == 1 and unit:GetHealth() < unit:GetMaxHealth() then
                            IssueRepair({self}, unit)
                            break
                        end
                    end
                end
            end
            scanTicks = scanTicks - 1
            WaitTicks(1)
        end
    end,
}
TypeClass = CRL0401
