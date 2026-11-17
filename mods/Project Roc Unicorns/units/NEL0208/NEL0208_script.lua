local Base = import('/lua/terranunits.lua').TLandUnit
local Artillery = import('/lua/terranweapons.lua').TIFArtilleryWeapon

NEL0208 = ClassUnit(Base) {
    OnMotionHorzEventChange = function(self, new, old)
        Base.OnMotionHorzEventChange(self, new, old)
        if new == 'Stopped' then
            if self.TrackAnimator then self.TrackAnimator:SetRate(0) end
        elseif old == 'Stopped' then
            if not self.TrackAnimator then
                self.TrackAnimator = self.Trash:Add(CreateAnimator(self, true))
                self.TrackAnimator:PlayAnim(self.Blueprint.Display.AnimationWalk, true)
                self.TrackAnimator:SetDirectionalAnim(true)
            end
            self.TrackAnimator:SetRate(self.Blueprint.Display.AnimationWalkRate or 1)
        end
    end,
    Weapons = {
        RocketRack = ClassWeapon(Artillery) {
            -- The stock firing state invokes this once per salvo step.
            CreateProjectileAtMuzzle = function(self, muzzle)
                local first = Artillery.CreateProjectileAtMuzzle(self, muzzle)
                for i = 1, 3 do
                    Artillery.CreateProjectileAtMuzzle(self, muzzle)
                end
                return first
            end,
        },
    },


}
TypeClass = NEL0208

