local XSL0307 = import('/units/xsl0307/xsl0307_script.lua').XSL0307

GGA0102 = Class(XSL0307) {
    OnStopBeingBuilt = function(self, builder, layer)
        XSL0307.OnStopBeingBuilt(self, builder, layer)

        -- Follow ArtyShields: replace the independent shield entity's default
        -- spherical collision with a box aligned to the forward panel.
        local shield = self.MyShield
        local createShieldMesh = shield.CreateShieldMesh
        local setPanelCollision = function(shieldEntity)
            local size = shieldEntity.Size
            shieldEntity:SetCollisionShape(
                'Box',
                0,
                size * 0.405,
                size * 2.19,
                size * 5.2,
                size * 0.405,
                size * 0.81
            )
        end

        shield.CreateShieldMesh = function(shieldEntity)
            createShieldMesh(shieldEntity)
            setPanelCollision(shieldEntity)
        end

        -- The stock shield may already be active by the time this unit hook
        -- runs; correct its initial sphere as well as future activations.
        setPanelCollision(shield)
    end,
}

TypeClass = GGA0102
