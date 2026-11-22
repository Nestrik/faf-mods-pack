local TMissileCruiseProjectile = import('/lua/terranprojectiles.lua').TMissileCruiseProjectile
local Effects = import('/lua/effecttemplates.lua')

UEL0213Rocket = ClassProjectile(TMissileCruiseProjectile) {
    -- Native TacticalMissileComponent handles boost, glide, and terminal guidance.
    -- The weapon forces an upward velocity; no turning during the first second.
    LaunchTicks = 10,
    LaunchTicksRange = 0,
    LaunchTurnRate = 0,
    LaunchTurnRateRange = 0,
    FinalBoostAngle = 30,
    HeightDistanceFactor = 11,

    FxImpactTrajectoryAligned = false,
    FxImpactAirUnit = Effects.TShipGaussCannonHitUnit02,
    FxAirUnitHitScale = 3,
    FxImpactLand = Effects.TShipGaussCannonHit02,
    FxImpactUnit = Effects.TShipGaussCannonHitUnit02,
    FxImpactProp = Effects.TShipGaussCannonHit02,
    FxLandHitScale = 3,
    FxUnitHitScale = 3,
    FxPropHitScale = 3,
    FxShieldHitScale = 3,
    FxWaterHitScale = 3,
    OnCreate = function(self, inWater)
        TMissileCruiseProjectile.OnCreate(self, inWater)
        local launcher = self.Launcher
        if launcher and not launcher:BeenDestroyed() then
            self.RetargetBrain = launcher:GetAIBrain()
        end
        self.RetargetDeadline = GetGameTick() + 300
    end,

    OnLostTarget = function(self)
        if self.RetargetThreadRunning then return end
        self.RetargetThreadRunning = true
        if self.MoveThread then
            KillThread(self.MoveThread)
            self.MoveThread = nil
        end
        local remainingTicks = self.RetargetDeadline - GetGameTick()
        if remainingTicks <= 0 then
            self:SetLifetime(0.1)
            return
        end
        self:SetLifetime(math.min(4, remainingTicks / 10))
        self.Trash:Add(ForkThread(self.FindAirTarget, self))
    end,

    FindAirTarget = function(self)
        local brain = self.RetargetBrain
        for attempt = 1, 6 do
            WaitTicks(5)
            if self:BeenDestroyed() then return end
            if not brain then break end

            local position = self:GetPosition()
            local candidates = brain:GetUnitsAroundPoint(
                categories.AIR * categories.MOBILE - categories.UNTARGETABLE,
                position, 60, 'Enemy'
            )
            local closest, closestDistance = nil, 60 * 60
            for _, candidate in candidates or {} do
                if not candidate.Dead and not candidate:BeenDestroyed() then
                    local blip = candidate:GetBlip(self.Army)
                    if blip and (blip:IsSeenNow(self.Army) or blip:IsOnRadar(self.Army)
                        or blip:IsOnOmni(self.Army)) then
                        local targetPosition = candidate:GetPosition()
                        local dx = targetPosition[1] - position[1]
                        local dz = targetPosition[3] - position[3]
                        local distance = dx * dx + dz * dz
                        if distance < closestDistance then
                            closest, closestDistance = candidate, distance
                        end
                    end
                end
            end

            if closest then
                local remainingTicks = self.RetargetDeadline - GetGameTick()
                if remainingTicks <= 0 then break end
                self:SetNewTarget(closest)
                self:TrackTarget(true)
                self:SetTurnRate(120)
                self:SetLifetime(math.min(6, remainingTicks / 10))
                self.RetargetThreadRunning = false
                return
            end
        end
        self.RetargetThreadRunning = false
        self:SetLifetime(0.5)
    end,

    -- Aerial impacts use a wider blast while surface damage keeps its original radius.
    OnImpact = function(self, targetType, targetEntity)
        if targetType == 'UnitAir' and self.DamageData then
            self.DamageData.DamageRadius = 4
        end
        TMissileCruiseProjectile.OnImpact(self, targetType, targetEntity)
    end,
}
TypeClass = UEL0213Rocket
