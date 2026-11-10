local Base = import('/lua/aeonunits.lua').AShieldHoverLandUnit
local EffectUtil = import('/lua/EffectUtilities.lua')

NEA0401 = ClassUnit(Base) {
    StartBeingBuiltEffects = function(self, builder, layer)
        Base.StartBeingBuiltEffects(self, builder, layer)
        -- Aeon factories already create the pool for their products. Engineer
        -- construction of this mobile experimental needs the stock pool here.
        if builder and not EntityCategoryContains(categories.FACTORY, builder) then
            self:ForkThread(EffectUtil.CreateAeonBuildBaseThread, builder, self.OnBeingBuiltEffectsBag)
        end
    end,

    OnStopBeingBuilt = function(self, builder, layer)
        Base.OnStopBeingBuilt(self, builder, layer)
        -- The live electrical arcs follow the crystal's bone as the tank turns.
        self.Trash:Add(CreateAttachedEmitter(self, 'Crystal', self.Army,
            '/effects/emitters/zapper_electricity_01_emit.bp'):ScaleEmitter(3))
        self.Trash:Add(CreateAttachedEmitter(self, 'Crystal', self.Army,
            '/mods/Project Roc Unicorns/effects/emitters/nea0401_crystal_mist_emit.bp'))
        self.RingsAnimator = CreateAnimator(self)
        self.Trash:Add(self.RingsAnimator)
        self.RingsAnimator:PlayAnim(self:GetBlueprint().Display.AnimationRings, true)
        self.Swarm = {}
        self:ForkThread(self.SwarmProductionThread)
    end,

    SwarmProductionThread = function(self)
        while not self.Dead and not self:BeenDestroyed() do
            for slot = 1, 20 do
                if self.Dead or self:BeenDestroyed() then return end
                local drone = self.Swarm[slot]
                if not drone or drone.Dead or drone:BeenDestroyed() then
                    local pos = self:GetPosition('Launch')
                    drone = CreateUnitHPR('NEA0001', self.Army, pos[1], pos[2] - 0.35, pos[3], 0, 0, 0)
                    if drone then
                        self.Swarm[slot] = drone
                        drone:SetCreator(self)
                        self:ForkThread(self.LaunchDrone, drone, slot)
                    end
                    -- One completed drone every three seconds, with no extra resource cost.
                    WaitSeconds(3)
                end
            end
            WaitSeconds(1)
        end
    end,

    LaunchDrone = function(self, drone, slot)
        -- Rise from the hatch before handing control to the existing swarm AI.
        if drone.Dead or drone:BeenDestroyed() then return end
        local pos = drone:GetPosition()
        drone:SetElevation(5)
        IssueMove({ drone }, { pos[1] + 0.3, GetSurfaceHeight(pos[1] + 0.3, pos[3]), pos[3] })
        WaitSeconds(1.2)
        if not drone.Dead and not drone:BeenDestroyed() then
            if self.Dead or self:BeenDestroyed() then
                drone:Destroy()
            else
                drone:StartSwarm(self, slot)
            end
        end
    end,

    OnDestroy = function(self)
        if self.Swarm then
            for _, drone in self.Swarm do
                if drone and not drone.Dead and not drone:BeenDestroyed() then
                    drone:Destroy()
                end
            end
        end
        Base.OnDestroy(self)
    end,
}
TypeClass = NEA0401
