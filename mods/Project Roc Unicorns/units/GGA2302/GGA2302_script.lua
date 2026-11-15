local GroundSpread = import('/mods/Project Roc Unicorns/lua/sha_veyr_ground_spread.lua')
local GetTarmac = import('/lua/tarmacs.lua').GetTarmacType
local SStructureUnit = import('/lua/seraphimunits.lua').SStructureUnit
local Cannon = import('/lua/seraphimweapons.lua').SDFOhCannon
local FirePath = import('/mods/Project Roc Unicorns/lua/sha_veyr_fire_path.lua')

GGA2302 = ClassUnit(SStructureUnit) {
    -- Keep the build-grid heading. Only the articulated gun aims at targets.
    RotateTowardsEnemy = function(self)
    end,

    CreateTarmacThread = function(self, createAlbedoTarmac, createNormalTarmac, createGlowTarmac, orientation, tarmac, lifeTime)
        -- hold up one tick to allow upgrades to pass the tarmac bag
        WaitTicks(1)

        -- upgrades pass the tarmac bag, in which case we take ownership and do nothing
        if self:HasTarmac() then
            self.TarmacBag.OwnedByEntity = self.EntityId
            return
        end

        -- no tarmacs underwater
        if self.Layer ~= 'Land' then
            return
        end

        -- bring into local scope for performance
        local CreateDecal = CreateDecal
        local GetTarmac = GetTarmac
        local TableEmpty = table.empty
        local TableRandom = table.random

        -- determine tarmac to place
        if not tarmac then
            local tarmacBlueprints = self.Blueprint.Display.Tarmacs
            if tarmacBlueprints and not TableEmpty(tarmacBlueprints) then
                tarmac = TableRandom(tarmacBlueprints)
            else
                return
            end
        end

        -- determine lod cutoff
        local meshBlueprint = self.Blueprint.Display.Mesh
        local cutoffOthers = meshBlueprint.LODs[1].LODCutoff
        local cutoffAlbedo = meshBlueprint.LODs[2].LODCutoff
        if not cutoffAlbedo then
            cutoffAlbedo = cutoffOthers
            cutoffOthers = 0.3 * cutoffOthers
        else
            cutoffOthers = 0.8 * cutoffOthers
        end

        -- reduce the LOD for performance
        cutoffAlbedo = 0.75 * cutoffAlbedo
        cutoffOthers = 0.75 * cutoffOthers

        -- determine orientation
        if not orientation then
            if tarmac.Orientations and not TableEmpty(tarmac.Orientations) then
                orientation = TableRandom(tarmac.Orientations)
                -- convert to radians
                orientation = (0.01745 * orientation)
            else
                orientation = 0
            end
        end

        -- determine size
        local w = tarmac.Width
        local l = tarmac.Length

        -- determine faction
        local factionIndex = 4 -- Seraphim

        -- determine terrain name for tarmacs based on terrain type
        -- TurretYaw is centered over the pedestal, including the mesh grid correction.
        local anchor = self:GetPosition('TurretYaw')
        local position = {anchor[1], GetTerrainHeight(anchor[1], anchor[3]), anchor[3]}
        local terrain = GetTerrainType(position[1], position[3])
        local terrainName = ''
        if terrain then
            terrainName = terrain.Name
        end

        -- create a new bag
        self.TarmacBag = {
            Decals = TrashBag(),
            OwnedByEntity = self.EntityId,
            Orientation = orientation,
            CurrentBP = tarmac,
            Lifetime = cutoffOthers,
        }
        local bag = self.TarmacBag.Decals

        -- create albedo tarmac, note that it may have a 2nd texture for specular properties
        if createAlbedoTarmac and tarmac.Albedo then
            local albedo2 = tarmac.Albedo2
            if albedo2 then
                albedo2 = albedo2 .. GetTarmac(factionIndex, terrain)
            end

            local handle = CreateDecal(
                position,
                orientation,
                tarmac.Albedo .. GetTarmac(factionIndex, terrainName),
                albedo2 or '',
                'Albedo',
                w,
                l,
                cutoffAlbedo,
                lifeTime or 0,
                self.Army,
                0
            )

            bag:Add(handle)
            if tarmac.RemoveWhenDead then
                self.Trash:Add(handle)
            end
        end

        -- create normals tarmac, note not the usual normals shader
        if createNormalTarmac and tarmac.Normal then
            local handle = CreateDecal(
                position,
                orientation,
                tarmac.Normal .. GetTarmac(factionIndex, terrainName),
                '',
                'Alpha Normals',
                w,
                l,
                cutoffOthers,
                lifeTime or 0,
                self.Army,
                0
            )

            bag:Add(handle)
            if tarmac.RemoveWhenDead then
                self.Trash:Add(handle)
            end
        end

        -- create glow tarmacs, not used by the base game
        if createGlowTarmac and tarmac.Glow then
            local handle = CreateDecal(
                position,
                orientation,
                tarmac.Glow .. GetTarmac(factionIndex, terrainName),
                '',
                'Glow',
                w,
                l,
                cutoffOthers,
                lifeTime or 0,
                self.Army,
                0
            )

            bag:Add(handle)
            if tarmac.RemoveWhenDead then
                self.Trash:Add(handle)
            end
        end
    end,

    OnStopBeingBuilt = function(self, builder, layer)
        SStructureUnit.OnStopBeingBuilt(self, builder, layer)
        self.FinOrbit = CreateRotator(self, 'FinOrbit', 'y')
        self.FinOrbit:SetTargetSpeed(36)
        self.FinOrbit:SetAccel(18)
        self.Trash:Add(self.FinOrbit)
    end,

    Weapons = {
        MainGun = ClassWeapon(Cannon) {
            FxMuzzleFlashScale = 0.70,
            NextMuzzle = 'MuzzleLeft',
            CanWeaponFire = function(self)
                return Cannon.CanWeaponFire(self) and self:VolleyIsClear()
            end,
            -- One native shot creates three projectiles in the same simulation tick.
            PlaySound = function(self, sound)
                if not self.SilentVolleyCopy then Cannon.PlaySound(self, sound) end
            end,
            VolleyMuzzles = { 'MuzzleLeft', 'MuzzleRight', 'MuzzleTop' },
            VolleyIsClear = function(self)
                for _, bone in ipairs(self.VolleyMuzzles) do
                    if not FirePath.IsClear(self, bone) then return false end
                end
                return true
            end,
            PlayFxMuzzleSequence = function(self, muzzle)
                if not self:VolleyIsClear() then return end
                for _, bone in ipairs(self.VolleyMuzzles) do
                    Cannon.PlayFxMuzzleSequence(self, bone)
                end
            end,
            CreateProjectileAtMuzzle = function(self, muzzle)
                if not self:VolleyIsClear() then
                    self.RejectedTarget = self:GetCurrentTarget()
                    self.HaltFireOrdered = true
                    return nil
                end
                local target = self:GetCurrentTargetPos()
                local first
                for _, bone in ipairs(self.VolleyMuzzles) do
                    local projectile = Cannon.CreateProjectileAtMuzzle(self, bone)
                    GroundSpread.Apply(projectile, target,
                        self.Blueprint.GroundSpreadRadius, self.Blueprint.MuzzleVelocity)
                    first = first or projectile
                    self.SilentVolleyCopy = true
                end
                self.SilentVolleyCopy = false
                if first then self:ForkThread(self.PulseRecoil) end
                return first
            end,
            PulseRecoil = function(self)
                if self:BeenDestroyed() or self.unit.Dead then return end
                if not self.BurstRecoil then
                    self.BurstRecoil = CreateSlider(self.unit, 'GunRecoil')
                    self.Trash:Add(self.BurstRecoil)
                end
                self.BurstRecoil:SetSpeed(12)
                self.BurstRecoil:SetGoal(0, 0, -0.20)
                WaitTicks(1)
                if self:BeenDestroyed() or self.unit.Dead then return end
                self.BurstRecoil:SetGoal(0, 0, 0)
                self.BurstRecoil:SetSpeed(4)
            end,
            BlockedState = State {
                StateName = 'BlockedState',
                WeaponWantEnabled = false,
                WeaponAimWantEnabled = false,
                Main = function(self)
                    self.unit:SetBusy(false)
                    self.unit:SetWorkProgress(1)
                    local rejected = self.RejectedTarget
                    self.RejectedTarget = nil
                    self:ResetTarget()
                    local target = FirePath.FindClearTarget(self, self.NextMuzzle, rejected)
                    if target then
                        self.ClearTarget = target
                        ChangeState(self, self.ClearTargetState)
                        return
                    end
                    WaitTicks(5)
                    if not self:BeenDestroyed() and not self.unit.Dead then
                        self:ResetTarget()
                        ChangeState(self, self.IdleState)
                    end
                end,
            },
            ClearTargetState = State {
                StateName = 'ClearTargetState',
                WeaponWantEnabled = true,
                WeaponAimWantEnabled = true,
                Main = function(self)
                    local target = self.ClearTarget
                    self.ClearTarget = nil
                    if target and not target.Dead and not target:BeenDestroyed() then
                        self:SetTargetEntity(target)
                    end
                    ChangeState(self, self.RackSalvoFireReadyState)
                end,
            },
            -- Native CanWeaponFire can suppress OnFire entirely. Check while ready
            -- as well, so an obstructed first target cannot monopolize the gun.
            RackSalvoFireReadyState = State(Cannon.RackSalvoFireReadyState) {
                Main = function(self)
                    self.unit:SetBusy(false)
                    self.WeaponCanFire = true
                    while not self:BeenDestroyed() and not self.unit.Dead do
                        WaitTicks(3)
                        if self:WeaponHasTarget() and not self:VolleyIsClear() then
                            self.RejectedTarget = self:GetCurrentTarget()
                            ChangeState(self, self.BlockedState)
                            return
                        end
                    end
                end,
            },
            RackSalvoFiringState = State(Cannon.RackSalvoFiringState) {
                Main = function(self)
                    if not self:WeaponHasTarget() then
                        WaitTicks(1)
                        if not self:WeaponHasTarget() then ChangeState(self, self.IdleState); return end
                    end
                    if not self:VolleyIsClear() then
                        self.RejectedTarget = self:GetCurrentTarget()
                        ChangeState(self, self.BlockedState)
                        return
                    end
                    Cannon.RackSalvoFiringState.Main(self)
                end,
            },
        },
    },
}
TypeClass = GGA2302
