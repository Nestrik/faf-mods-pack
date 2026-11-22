local Ring = import('/mods/Project Roc Unicorns/lua/razlom_ring.lua')
local ProjectileWeapon = import('/lua/sim/defaultweapons.lua').DefaultProjectileWeapon
local BeamWeapon = import('/lua/sim/defaultweapons.lua').DefaultBeamWeapon
local CollisionBeam = import('/lua/sim/collisionbeam.lua').CollisionBeam
local WeaponCallbacks = import('/lua/sim/weapon.lua').Weapon
local FirePath = import('/mods/Project Roc Unicorns/lua/razlom_fire_path.lua')
local GroundSpread = import('/mods/Project Roc Unicorns/lua/sha_veyr_ground_spread.lua')
local FX = '/mods/Project Roc Unicorns/effects/emitters/razlom_'
local AuxBeam = Class(CollisionBeam) {
    FxBeam = { FX .. 'aa_halo_beam.bp', FX .. 'aux_beam.bp' },
    FxBeamStartPoint = { FX .. 'aa_eye_glow_emit.bp', FX .. 'aa_eye_sparks_emit.bp' },
    FxBeamEndPoint = { FX .. 'aa_cut_glow_emit.bp', FX .. 'aa_cut_sparks_emit.bp' },
    FxBeamEndPointScale = 1.0,
    TerrainImpactType = 'LargeBeam01',
    TerrainImpactScale = 0.25,
}
AuxWeapon = ClassWeapon(BeamWeapon) {
    SetWeaponEnabled = function(self, enabled)
        BeamWeapon.SetWeaponEnabled(self, enabled and self.WaterClear ~= false)
    end,
    CanWeaponFire = function(self)
        return self.WaterClear ~= false and BeamWeapon.CanWeaponFire(self)
    end,
    CreateProjectileAtMuzzle = function(self, muzzle)
        local p = self.unit:GetPosition(muzzle)
        if p[2] <= GetSurfaceHeight(p[1],p[3])+.08 then
            self:PlayFxBeamEnd()
            return
        end
        return BeamWeapon.CreateProjectileAtMuzzle(self,muzzle)
    end,
    BeamType = AuxBeam,
    FxMuzzleFlash = {},
    FxChargeMuzzleFlash = {},
    OnLostTarget = function(self)
        self:PlayFxBeamEnd()
        BeamWeapon.OnLostTarget(self)
    end,
}

SiegeWeapon = ClassWeapon(ProjectileWeapon) {
    SetWeaponEnabled = function(self, enabled)
        ProjectileWeapon.SetWeaponEnabled(self, enabled and self.WaterClear ~= false)
    end,
    -- This floating weapon must never mark its mobile owner busy or immobile.
    -- Keep the native state transitions, but scope the deployment lock to firing.
    WeaponUnpackingState = State(ProjectileWeapon.WeaponUnpackingState) {
        Main = function(self)
            self.WeaponCanFire = false
            self:PlayFxWeaponUnpackSequence()
            if not self.unit.Dead then
                ChangeState(self, self.RackSalvoFireReadyState)
            end
        end,
    },
    WeaponPackingState = State(ProjectileWeapon.WeaponPackingState) {
        Main = function(self)
            WaitSeconds(self.Blueprint.WeaponRepackTimeout or 2)
            if self.unit.Dead then return end
            self.WeaponCanFire = false
            self:AimManipulatorSetEnabled(false)
            self:PlayFxWeaponPackSequence()
            if not self.unit.Dead then ChangeState(self, self.IdleState) end
        end,
    },
    PlayFxWeaponUnpackSequence = function(self)
        self.WeaponPackState = 'Unpacking'
        Ring.Deploy(self.unit)
        self.WeaponPackState = 'Unpacked'
    end,
    PlayFxWeaponPackSequence = function(self)
        self.WeaponPackState = 'Packing'
        Ring.Stow(self.unit)
        self.WeaponPackState = 'Packed'
    end,
    FxMuzzleFlash = {}, -- the shared comet already has a luminous launch corona
    FxChargeMuzzleFlash = {},
    StopCharge = function(self)
        self.Charging = false
        local unit = self.unit
        if unit and not unit.Dead and not unit:BeenDestroyed() then
            if unit.Rotor then unit.Rotor:SetTargetSpeed(15) end
            if unit.CounterRotor then unit.CounterRotor:SetTargetSpeed(-15) end
        end
    end,
    OnLostTarget = function(self)
        self:StopCharge()
        ProjectileWeapon.OnLostTarget(self)
    end,
    UpdateOrderedAttackPursuit = function(self)
        -- Never reset automatic targets or enter pursuit during player movement.
        -- Restore the normal radius only if a preceding attack used pursuit.
        if FirePath.HasNonAttackOrder(self.unit) then
            self.EnrouteAttack = nil
            if self.OrderedAttackPursuit then
                self.OrderedAttackPursuit = false
                self:ChangeMaxRadius(self.Blueprint.MaxRadius)
                ChangeState(self, self.IdleState)
            end
            return
        end
        local distant, orderedTarget = FirePath.GetDistantAttack(self)
        if distant then
            -- Keep the player attack order and the weapon's full combat range.
            -- SetTargetEntity changes only this weapon, never the command queue.
            if self.OrderedAttackPursuit then
                self.OrderedAttackPursuit = false
                self:ChangeMaxRadius(self.Blueprint.MaxRadius)
                ChangeState(self, self.IdleState)
            end
            self.EnrouteAttack = true
            local target = FirePath.FindClearTarget(self, 'MainMuzzle', orderedTarget)
            if target then
                local current = self:GetCurrentTarget()
                if current and current.GetSource and not current:BeenDestroyed() then current = current:GetSource() end
                if current ~= target then self:SetTargetEntity(target) end
            end
            return
        end
        if self.EnrouteAttack then
            self.EnrouteAttack = nil
            local aim, target = FirePath.GetOrderedAttack(self.unit)
            if target then self:SetTargetEntity(target)
            elseif aim then self:SetTargetGround(aim) end
        end
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
        -- Free automatic targeting from an occluded enemy without rewriting orders.
        if not self.OrderedAttackPursuit and not FirePath.GetOrderedAttack(self.unit)
            and self:WeaponHasTarget() and not FirePath.IsClear(self, 'MainMuzzle') then
            local target = FirePath.FindClearTarget(self, 'MainMuzzle', self:GetCurrentTarget())
            self:ResetTarget()
            if target then self:SetTargetEntity(target) end
        end
    end,
    OrderedAttackPursuitState = State {
        WeaponWantEnabled = true, WeaponAimWantEnabled = false,
        Main = function(self) self.WeaponCanFire = false; self:StopCharge() end,
        OnLostTarget = function(self) WeaponCallbacks.OnLostTarget(self) end,
        OnGotTarget = function(self) WeaponCallbacks.OnGotTarget(self) end,
        OnFire = function(self) end,
    },
    CanWeaponFire = function(self)
        return self.WaterClear ~= false and self.unit.Ring and self.unit.Ring.ready and not self.OrderedAttackPursuit and ProjectileWeapon.CanWeaponFire(self)
            and FirePath.IsClear(self, 'MainMuzzle')
    end,
    CreateProjectileAtMuzzle = function(self, muzzle)
        if self.WaterClear == false or not self.unit.Ring or not self.unit.Ring.ready or not FirePath.IsClear(self, muzzle) then return nil end
        local projectile = ProjectileWeapon.CreateProjectileAtMuzzle(self, muzzle)
        GroundSpread.Apply(projectile, self:GetCurrentTargetPos(),
            self.Blueprint.GroundSpreadRadius, self.Blueprint.MuzzleVelocity)
        if projectile then
            if self.unit.Rotor then self.unit.Rotor:SetTargetSpeed(240) end
            if self.unit.CounterRotor then self.unit.CounterRotor:SetTargetSpeed(-192) end
        end
        return projectile
    end,
}
