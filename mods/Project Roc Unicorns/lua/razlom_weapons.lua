local ProjectileWeapon = import('/lua/sim/defaultweapons.lua').DefaultProjectileWeapon
local BeamWeapon = import('/lua/sim/defaultweapons.lua').DefaultBeamWeapon
local CollisionBeam = import('/lua/sim/collisionbeam.lua').CollisionBeam
local WeaponCallbacks = import('/lua/sim/weapon.lua').Weapon
local FirePath = import('/mods/Project Roc Unicorns/lua/razlom_fire_path.lua')
local FX = '/mods/Project Roc Unicorns/effects/emitters/razlom_'

local AuxBeam = Class(CollisionBeam) {
    FxBeam = { FX .. 'aux_beam.bp' },
    FxBeamStartPoint = { FX .. 'muzzle_emit.bp', FX .. 'sparks_emit.bp' },
    FxBeamEndPoint = { FX .. 'muzzle_emit.bp' },
    FxBeamEndPointScale = 0.6,
    TerrainImpactType = 'LargeBeam01',
    TerrainImpactScale = 0.25,
}
local ChargeBeam = Class(CollisionBeam) {
    FxBeam = { FX .. 'charge1_beam.bp' },
    FxBeamStartPoint = { FX .. 'charge_emit.bp', FX .. 'sparks_emit.bp' },
    -- The targeting/charging beam is strictly visual, including at shield collisions.
    DoDamage = function(self, instigator, damageData, targetEntity) end,
    UpdateTerrainCollisionEffects = function(self, impactType) end,
}

AuxWeapon = ClassWeapon(BeamWeapon) {
    BeamType = AuxBeam,
    FxMuzzleFlash = {},
    FxChargeMuzzleFlash = {},
    OnLostTarget = function(self)
        self:PlayFxBeamEnd()
        BeamWeapon.OnLostTarget(self)
    end,
}

SiegeWeapon = ClassWeapon(ProjectileWeapon) {
    FxMuzzleFlash = { FX .. 'shot_emit.bp', FX .. 'sparks_emit.bp' },
    FxChargeMuzzleFlash = {},
    OnCreate = function(self)
        ProjectileWeapon.OnCreate(self)
        self.ChargeBeam = ChargeBeam { Weapon = self, BeamBone = 0, OtherBone = 'MainMuzzle', CollisionCheckInterval = 1 }
        self.ChargeBeam:SetParentWeapon(self)
        self.ChargeBeam:Disable()
        self.Trash:Add(self.ChargeBeam)
    end,
    StopCharge = function(self)
        self.Charging = false
        self.WeaponCanFire = true
        if self.ChargeBeam and not self.ChargeBeam:BeenDestroyed() then self.ChargeBeam:Disable() end
        local unit = self.unit
        if unit and not unit.Dead and not unit:BeenDestroyed() then
            unit:SetWorkProgress(1)
            unit:SetBusy(false)
            if unit.Rotor then unit.Rotor:SetTargetSpeed(15) end
            if unit.CounterRotor then unit.CounterRotor:SetTargetSpeed(-15) end
        end
    end,
    OnLostTarget = function(self)
        self:StopCharge()
        ProjectileWeapon.OnLostTarget(self)
    end,
    UpdateOrderedAttackPursuit = function(self)
        local blocked = FirePath.OrderedAttackIsBlocked(self)
        if blocked and not self.OrderedAttackPursuit then
            self.OrderedAttackPursuit = true
            self:StopCharge()
            self:ChangeMaxRadius(1)
            ChangeState(self, self.OrderedAttackPursuitState)
        elseif not blocked and self.OrderedAttackPursuit then
            self.OrderedAttackPursuit = false
            self:ChangeMaxRadius(self.Blueprint.MaxRadius)
            ChangeState(self, self.IdleState)
        end
    end,
    OrderedAttackPursuitState = State {
        WeaponWantEnabled = true, WeaponAimWantEnabled = false,
        Main = function(self) self.WeaponCanFire = false; self.unit:SetBusy(false) end,
        OnLostTarget = function(self) WeaponCallbacks.OnLostTarget(self) end,
        OnGotTarget = function(self) WeaponCallbacks.OnGotTarget(self) end,
        OnFire = function(self) end,
    },
    CanWeaponFire = function(self)
        return not self.OrderedAttackPursuit and not self.unit.Moving
            and ProjectileWeapon.CanWeaponFire(self) and FirePath.IsClear(self, 'MainMuzzle')
    end,
    TerrainBlockedState = State {
        WeaponWantEnabled = false, WeaponAimWantEnabled = false,
        OnLostTarget = function(self) WeaponCallbacks.OnLostTarget(self) end,
        OnGotTarget = function(self) WeaponCallbacks.OnGotTarget(self) end,
        OnFire = function(self) end,
        Main = function(self)
            self:StopCharge()
            local rejected = self:GetCurrentTarget()
            self:ResetTarget()
            while not self.unit.Dead do
                local target = FirePath.FindClearTarget(self, 'MainMuzzle', rejected)
                if target then
                    self.NextClearTarget = target
                    ChangeState(self, self.RetargetState)
                    return
                end
                WaitTicks(5)
                rejected = nil
                if self:WeaponHasTarget() and FirePath.IsClear(self, 'MainMuzzle') then
                    ChangeState(self, self.RackSalvoChargeState)
                    return
                end
            end
        end,
    },
    RetargetState = State {
        WeaponWantEnabled = true, WeaponAimWantEnabled = true,
        Main = function(self)
            local target = self.NextClearTarget
            self.NextClearTarget = nil
            if target and not target.Dead then self:SetTargetEntity(target) end
            WaitTicks(1)
            ChangeState(self, self.RackSalvoChargeState)
        end,
    },
    RackSalvoChargeState = State(ProjectileWeapon.RackSalvoChargeState) {
        Main = function(self)
            self.unit:SetBusy(false)
            if not self:WeaponHasTarget() then WaitTicks(1) end
            if self.unit.Moving or not self:WeaponHasTarget() then
                WaitTicks(3)
                ChangeState(self, self.IdleState)
                return
            end
            if not FirePath.IsClear(self, 'MainMuzzle') then
                ChangeState(self, self.TerrainBlockedState)
                return
            end
            self.Charging = true
            self.WeaponCanFire = false
            self:PlayFxRackSalvoChargeSequence()
            for tick = 0, 29 do
                if self.unit.Dead then self:StopCharge(); return end
                if self.unit.Moving or not self:WeaponHasTarget() then
                    self:StopCharge(); ChangeState(self, self.IdleState); return
                end
                if not FirePath.IsClear(self, 'MainMuzzle') then
                    self:StopCharge(); ChangeState(self, self.TerrainBlockedState); return
                end
                if tick == 0 or tick == 10 or tick == 20 then
                    self.ChargeBeam:Disable()
                    self.ChargeBeam.FxBeam = { FX .. 'charge' .. (math.floor(tick / 10) + 1) .. '_beam.bp' }
                    self.ChargeBeam:Enable()
                end
                local speed = 15 + 345 * tick / 29
                self.unit.Rotor:SetTargetSpeed(speed)
                self.unit.CounterRotor:SetTargetSpeed(-speed * 0.8)
                self.unit:SetWorkProgress(tick / 30)
                WaitTicks(1)
            end
            self.WeaponCanFire = true
            ChangeState(self, self.RackSalvoFireReadyState)
        end,
    },
    RackSalvoFireReadyState = State(ProjectileWeapon.RackSalvoFireReadyState) {
        Main = function(self)
            self.WeaponCanFire = true
            self.unit:SetBusy(false)
            while not self.unit.Dead do
                if self.unit.Moving or not self:WeaponHasTarget() then
                    self:StopCharge(); ChangeState(self, self.IdleState); return
                end
                if not FirePath.IsClear(self, 'MainMuzzle') then
                    self:StopCharge(); ChangeState(self, self.TerrainBlockedState); return
                end
                WaitTicks(2)
            end
        end,
    },
    CreateProjectileAtMuzzle = function(self, muzzle)
        if self.unit.Moving or not FirePath.IsClear(self, muzzle) then
            self:StopCharge()
            return nil
        end
        self.Charging = false
        local projectile = ProjectileWeapon.CreateProjectileAtMuzzle(self, muzzle)
        -- Native projectile collisions stop the flash at shields / walls / terrain.
        self:ForkThread(function(weapon)
            WaitTicks(2)
            weapon:StopCharge()
        end)
        return projectile
    end,
}
