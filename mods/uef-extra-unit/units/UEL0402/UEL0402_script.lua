local Base = import('/lua/terranunits.lua').TLandUnit
local Laser = import('/lua/terranweapons.lua').TOrbitalDeathLaserBeamWeapon
local Weapon = import('/lua/sim/weapon.lua').Weapon

local MountBone = 'Turret_Right01'
local MountX, MountZ = -11.27, -7.58
local DockHeight, FlightHeight = 8, 160
local MountSpeed = 50
local SatelliteScale = 0.09

local function AttachVisual(unit, mesh, bone, offset, scale)
    local visual = Entity({ Owner = unit })
    visual:SetMesh(mesh, false)
    visual:SetCollisionShape('None')
    visual:AttachBoneTo(-1, unit, bone)
    visual:SetParentOffset(offset)
    visual:SetDrawScale(scale)
    visual:SetVizToFocusPlayer('Always')
    visual:SetVizToAllies('Always')
    visual:SetVizToEnemies('Intel')
    visual:SetVizToNeutrals('Intel')
    unit.Trash:Add(visual)
    return visual
end

UEL0402 = ClassUnit(Base) {
    Weapons = {
        SatelliteLaser = ClassWeapon(Laser) {
            RackSalvoFiringState = State(Laser.RackSalvoFiringState) {
                Main = function(self)
                    local unit = self.unit
                    if not unit.SatelliteMount then
                        ChangeState(self, self.IdleState)
                        return
                    end
                    unit.SatelliteAirborne = true
                    unit.SatelliteVisual:SetDrawScale(SatelliteScale)
                    unit.SatelliteMount:SetGoal(MountX, FlightHeight, MountZ)
                    WaitFor(unit.SatelliteMount)
                    if self:BeenDestroyed() or unit.Dead or unit:BeenDestroyed() then return end
                    -- Cancellation or loss of target during ascent still lands
                    -- the model; the native beam is never released prematurely.
                    if self.HaltFireOrdered or not self:WeaponHasTarget() then
                        self.HaltFireOrdered = false
                        self.CancelledLaunch = true
                        ChangeState(self, self.RackSalvoReloadState)
                        return
                    end
                    Laser.RackSalvoFiringState.Main(self)
                end,
                OnLostTarget = function(self)
                    -- Keep this state alive until it can land safely.
                    if self.unit then self.unit:OnLostTarget(self) end
                    Weapon.OnLostTarget(self)
                end,
                OnHaltFire = function(self)
                    self.HaltFireOrdered = true
                    Laser.OnHaltFire(self)
                end,
            },
            RackSalvoReloadState = State(Laser.RackSalvoReloadState) {
                Main = function(self)
                    local unit = self.unit
                    -- The engine starts the finite beam in the firing state and
                    -- changes to reload immediately; keep the mount aloft until
                    -- the beam lifetime has elapsed.
                    if not self.CancelledLaunch then
                        WaitSeconds(self.Blueprint.BeamLifetime)
                    end
                    self.CancelledLaunch = false
                    if self:BeenDestroyed() or unit.Dead or unit:BeenDestroyed() then return end
                    unit.SatelliteMount:SetGoal(MountX, DockHeight, MountZ)
                    WaitFor(unit.SatelliteMount)
                    if self:BeenDestroyed() or unit.Dead or unit:BeenDestroyed() then return end
                    unit.SatelliteAirborne = false
                    unit.SatelliteVisual:SetDrawScale(0.000001)
                    -- The native reload timer begins only after docking.
                    Laser.RackSalvoReloadState.Main(self)
                end,
            },
        },
    },

    OnStopBeingBuilt = function(self, builder, layer)
        Base.OnStopBeingBuilt(self, builder, layer)
        for _, bone in {
            'Turret_Right01', 'Turret_Right02', 'Turret_Left01', 'Turret_Left02',
            'Turret_Right_AA', 'Turret_Left_AA', 'Riot_Gun_Right', 'Riot_Gun_Left',
        } do
            self:HideBone(bone, true)
        end

        local mount = CreateSlider(self, MountBone)
        mount:SetWorldUnits(false)
        mount:SetSpeed(-1)
        mount:SetGoal(MountX, DockHeight, MountZ)
        mount:SetSpeed(MountSpeed)
        self.Trash:Add(mount)
        self.SatelliteMount = mount
        self.SatelliteAirborne = false

        -- The model is attached to the visible root, not the hidden gun bone.
        -- A sync thread positions it at that bone so the laser and visual move
        -- together. It is an owned visual entity, not a separate game unit.
        self.SatelliteVisual = AttachVisual(self, '/units/xea0002/xea0002_mesh',
            0, Vector(0, 0, 0), 0.000001)
        AttachVisual(self, '/mods/uef-extra-unit/meshes/launch-hatch/launch_hatch_mesh',
            0, Vector(0, 0.9, 0), 1)
        self:ForkThread(self.SyncSatelliteVisual)
    end,

    SyncSatelliteVisual = function(self)
        while not self.Dead and not self:BeenDestroyed() do
            if self.SatelliteAirborne and self.SatelliteVisual and not self.SatelliteVisual:BeenDestroyed() then
                local rx, ry, rz = self:GetPositionXYZ(0)
                local x, y, z = self:GetPositionXYZ(MountBone)
                local heading = self:GetHeading()
                local c, s = math.cos(heading), math.sin(heading)
                local dx, dz = x - rx, z - rz
                self.SatelliteVisual:SetParentOffset(Vector(c * dx - s * dz, y - ry, s * dx + c * dz))
            end
            WaitTicks(1)
        end
    end,
}
TypeClass = UEL0402
