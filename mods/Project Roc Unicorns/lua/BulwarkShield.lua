local CShieldStructureUnit = import('/lua/cybranunits.lua').CShieldStructureUnit

BulwarkShield = ClassUnit(CShieldStructureUnit) {
    OnShieldEnabled = function(self)
        CShieldStructureUnit.OnShieldEnabled(self)
        if not self.ShieldRotor then
            self.ShieldRotor = CreateRotator(self, 'ShieldRotor', 'y')
            self.Trash:Add(self.ShieldRotor)
        end
        self.ShieldRotor:SetSpeed(10)
    end,

    OnShieldDisabled = function(self)
        CShieldStructureUnit.OnShieldDisabled(self)
        if self.ShieldRotor then
            self.ShieldRotor:SetSpeed(0)
        end
    end,
}
