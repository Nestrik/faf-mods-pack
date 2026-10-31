local HoverTank = import('/lua/seraphimunits.lua').SHoverLandUnit
local SeraphimWeapons = import('/lua/seraphimweapons.lua')
local PhasonCannon = SeraphimWeapons.SDFExperimentalPhasonProj
local FirePath = import('/mods/Project Roc Unicorns/lua/dush_nai_fire_path.lua')
local ChargeAnimation = import('/mods/Project Roc Unicorns/lua/itha_yen_charge.lua')

GGA0401 = ClassUnit(HoverTank) {
    OnStopBeingBuilt = function(self, builder, layer)
        HoverTank.OnStopBeingBuilt(self, builder, layer)
        ChargeAnimation.Initialize(self)
    end,

    OnKilled = function(self, instigator, damageType, overkillRatio)
        ChargeAnimation.Stop(self)
        HoverTank.OnKilled(self, instigator, damageType, overkillRatio)
    end,

    OnDestroy = function(self)
        ChargeAnimation.Stop(self)
        HoverTank.OnDestroy(self)
    end,

    Weapons = {
        MainGun = ClassWeapon(PhasonCannon) {
            -- Engine callback: unlike suppressing a projectile after spawning,
            -- this keeps a blocked gun from starting another firing cycle.
            CanWeaponFire = function(self)
                return PhasonCannon.CanWeaponFire(self) and FirePath.IsClear(self, 'MainMuzzle')
            end,
            -- A target or the shooter can move during the native 3 s charge.
            -- Recheck at release; no new projectile/damage if the path closes.
            CreateProjectileAtMuzzle = function(self, muzzle)
                if not FirePath.IsClear(self, muzzle) then
                    self:CancelBlockedCycle()
                    return nil
                end
                return PhasonCannon.CreateProjectileAtMuzzle(self, muzzle)
            end,
            CancelBlockedCycle = function(self)
                self.TerrainRejectedTarget = self:GetCurrentTarget()
                self.BlockedOnRelease = true
                self.FireClockEpoch = (self.FireClockEpoch or 0) + 1
                self.unit:SetWorkProgress(1)
            end,
            OnWeaponFired = function(self)
                PhasonCannon.OnWeaponFired(self)
                if self.BlockedOnRelease then
                    self.BlockedOnRelease = false
                    ChangeState(self, self.TerrainBlockedState)
                end
            end,
            TerrainBlockedState = State {
                StateName = 'TerrainBlockedState',
                WeaponWantEnabled = false,
                WeaponAimWantEnabled = false,
                Main = function(self)
                    self.FireClockEpoch = (self.FireClockEpoch or 0) + 1
                    self.unit:SetBusy(false)
                    self.unit:SetWorkProgress(1)
                    local rejected = self.TerrainRejectedTarget
                    self.TerrainRejectedTarget = nil
                    self:ResetTarget()
                    local target = FirePath.FindClearTarget(self, 'MainMuzzle', rejected)
                    if target then
                        self.ClearShotTarget = target
                        ChangeState(self, self.RetargetClearState)
                        return
                    end
                    -- Native target acquisition is retried without polling a
                    -- fake firing cycle or issuing/changing player orders.
                    WaitTicks(10)
                    if not self:BeenDestroyed() and not self.unit.Dead then
                        self:ResetTarget()
                        ChangeState(self, self.IdleState)
                    end
                end,
            },
            RetargetClearState = State {
                StateName = 'RetargetClearState',
                WeaponWantEnabled = true,
                WeaponAimWantEnabled = true,
                Main = function(self)
                    local target = self.ClearShotTarget
                    self.ClearShotTarget = nil
                    if target and not target.Dead and not target:BeenDestroyed() then
                        self:SetTargetEntity(target)
                    end
                    ChangeState(self, self.RackSalvoFireReadyState)
                end,
            },
            RackSalvoFiringState = State(PhasonCannon.RackSalvoFiringState) {
                Main = function(self)
                    -- This is before native Main forks RenderClockThread,
                    -- plays charge audio or sets up the three-second salvo.
                    -- WeaponHasTarget is an end-of-tick cache in moho. Let
                    -- a just-acquired target settle before the terrain guard.
                    if not self:WeaponHasTarget() then
                        WaitTicks(1)
                        if not self:WeaponHasTarget() then
                            ChangeState(self, self.IdleState)
                            return
                        end
                    end
                    if not FirePath.IsClear(self, 'MainMuzzle') then
                        self.TerrainRejectedTarget = self:GetCurrentTarget()
                        ChangeState(self, self.TerrainBlockedState)
                        return
                    end
                    self.BlockedOnRelease = false
                    self.FireClockEpoch = (self.FireClockEpoch or 0) + 1
                    PhasonCannon.RackSalvoFiringState.Main(self)
                end,
                RenderClockThread = function(self, seconds)
                    -- Equivalent native clock, with cancellation for a target
                    -- that becomes obstructed during the charge.
                    local epoch = self.FireClockEpoch
                    local total = math.max(1, math.floor(seconds * 10 + .5))
                    for remaining = total, 0, -1 do
                        if self:BeenDestroyed() or self.unit.Dead or self.FireClockEpoch ~= epoch then return end
                        if not self.unit:IsUnitState('SiloBuildingAmmo') then
                            self.unit:SetWorkProgress(1 - remaining / total)
                        end
                        WaitTicks(1)
                    end
                end,
            },
            FxMuzzleFlashScale = 1.3,
            -- The attached original phason sphere and distributed electrical
            -- field replace the stock single-muzzle charge flash.
            FxChargeMuzzleFlash = {},
            PlayFxMuzzleChargeSequence = function(self, muzzle)
                ChargeAnimation.BeginWeaponCharge(self.unit, self.Blueprint.MuzzleChargeDelay)
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                if not FirePath.IsClear(self, muzzle) then
                    self:CancelBlockedCycle()
                    return
                end
                ChargeAnimation.OnShot(self.unit, self:GetWeaponRoF())
                PhasonCannon.PlayFxMuzzleSequence(self, muzzle)
            end,
            -- Clear-path firing uses the unchanged native salvo. A blocked
            -- path waits outside it, preserving the accepted visual controller.
        },
    },
}
TypeClass = GGA0401
