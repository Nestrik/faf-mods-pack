local Base = import('/lua/terranunits.lua').TLandUnit
local Laser = import('/lua/terranweapons.lua').TOrbitalDeathLaserBeamWeapon

local Stations = {
    { bone = 'Turret_Right01', label = 'SatelliteLaser1', x = 8, z = 8 },
    { bone = 'Turret_Right02', label = 'SatelliteLaser2', x = 8, z = -8 },
    { bone = 'Turret_Left01',  label = 'SatelliteLaser3', x = -8, z = 8 },
    { bone = 'Turret_Left02',  label = 'SatelliteLaser4', x = -8, z = -8 },
}

UEL0402 = ClassUnit(Base) {
    Weapons = {
        SatelliteLaser1 = ClassWeapon(Laser) {},
        SatelliteLaser2 = ClassWeapon(Laser) {},
        SatelliteLaser3 = ClassWeapon(Laser) {},
        SatelliteLaser4 = ClassWeapon(Laser) {},
    },

    OnStopBeingBuilt = function(self, builder, layer)
        Base.OnStopBeingBuilt(self, builder, layer)
        for _, bone in { 'Turret_Right_AA', 'Turret_Left_AA', 'Riot_Gun_Right', 'Riot_Gun_Left' } do
            self:HideBone(bone, true)
        end
        self.SatelliteStations = {}
        local p = self:GetPosition()
        local heading = self:GetHeading()
        local c, s = math.cos(heading), math.sin(heading)
        local scale = self.Blueprint.Display.UniformScale
        for _, spec in Stations do
            local x, y, z = self:GetPositionXYZ(spec.bone)
            local dx, dz = x - p[1], z - p[3]
            local station = {
                spec = spec,
                baseX = c * dx - s * dz,
                baseZ = s * dx + c * dz,
                baseY = y - p[2],
                weapon = self:GetWeaponByLabel(spec.label),
            }
            -- The original turret geometry is hidden, but its rig remains the
            -- platform's native weapon and motion rig.
            self:HideBone(spec.bone, true)
            local slider = CreateSlider(self, spec.bone)
            slider:SetWorldUnits(false)
            slider:SetSpeed(30 / scale)
            self.Trash:Add(slider)
            station.slider = slider

            -- This entity is only a mesh attached to the platform bone. It has
            -- no unit blueprint, orders, health, weapon or independent physics.
            local visual = Entity({ Owner = self })
            visual:SetMesh('/units/xea0002/xea0002_mesh', false)
            visual:SetCollisionShape('None')
            visual:AttachBoneTo(-1, self, spec.bone)
            visual:SetParentOffset(Vector(0, 0, 0))
            visual:SetDrawScale(0.05)
            visual:SetVizToFocusPlayer('Always')
            visual:SetVizToAllies('Always')
            visual:SetVizToEnemies('Intel')
            visual:SetVizToNeutrals('Intel')
            self.Trash:Add(visual)
            table.insert(self.SatelliteStations, station)
        end
        self:ForkThread(self.MoveSatelliteBones)
    end,

    MoveSatelliteBones = function(self)
        local scale = self.Blueprint.Display.UniformScale
        while not self.Dead and not self:BeenDestroyed() do
            local p = self:GetPosition()
            local heading = self:GetHeading()
            local c, s = math.cos(heading), math.sin(heading)
            for _, station in self.SatelliteStations do
                local x, y, z = station.spec.x, 35, station.spec.z
                local target = station.weapon:WeaponHasTarget() and station.weapon:GetCurrentTargetPos()
                if target and station.weapon:WeaponHasTarget() then
                    local dx, dz = target[1] - p[1], target[3] - p[3]
                    local distance = math.sqrt(dx * dx + dz * dz)
                    if distance > 300 then
                        dx, dz = dx * 300 / distance, dz * 300 / distance
                    end
                    x, z = c * dx - s * dz, s * dx + c * dz
                    y = math.max(35, target[2] - p[2] + 35)
                end
                station.slider:SetGoal((x - station.baseX) / scale,
                    (y - station.baseY) / scale, (z - station.baseZ) / scale)
            end
            WaitTicks(5)
        end
    end,
}
TypeClass = UEL0402

